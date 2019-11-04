from osp.core.session.sim_wrapper_session import SimWrapperSession
from osp.core import CITY
import unittest2 as unittest


class TestSimWrapperCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_dummy_sim_wrapper(self):
        """Create a dummy simulation syntactic layer + test
        if working with this layer works as expected.
        """
        with DummySimSession() as session:
            wrapper = CITY.CITY_SIM_WRAPPER(num_steps=1, session=session)
            c = CITY.CITY(name="Freiburg")
            p1 = CITY.PERSON(name="Hans", age=34)
            p2 = CITY.PERSON(name="Renate", age=54)
            cw, _, _ = wrapper.add(c, p1, p2)

            session.run()

            self.assertEqual(len(
                wrapper.get(entity=CITY.PERSON,
                            rel=CITY.HAS_PART)), 1)
            self.assertEqual(len(
                cw.get(entity=CITY.CITIZEN,
                       rel=CITY.HAS_INHABITANT)), 1)
            self.assertEqual(wrapper.get(p2.uid).name, "Renate")
            self.assertEqual(wrapper.get(p2.uid).age, 55)
            self.assertEqual(cw.get(p1.uid).name, "Hans")
            self.assertEqual(cw.get(p1.uid).age, 35)

            session.run()
            wrapper.add(CITY.PERSON(name="Peter"))
            self.assertRaises(RuntimeError, session.run)


class DummySimSession(SimWrapperSession):
    def __init__(self, **kwargs):
        super().__init__(engine=DummySyntacticLayer(), **kwargs)
        self._person_map = list()

    def __str__(self):
        return "Dummy SimWrapperSession"

    # OVERRIDE
    def _run(self, root_cuds_object):
        self._engine.simulate(root_cuds_object.num_steps)

    # OVERRIDE
    def _update_cuds_objects_after_run(self, root_cuds_object):
        # update the age of each person and delete persons that became citizens
        person_uids = set()
        for i, p in self._engine.get_persons():
            uid = self._person_map[i]
            person_uids.add(uid)
            root_cuds_object.get(uid).age = p.age
        for p in root_cuds_object.get(entity=CITY.PERSON):
            if p.uid not in person_uids:
                root_cuds_object.remove(p)

        # update the age of the citizens and add new citizens
        city = root_cuds_object.get(entity=CITY.CITY)[0]
        for i, p in self._engine.get_inhabitants():
            uid = self._person_map[i]
            inhabitant = city.get(uid)
            if inhabitant:
                inhabitant.age = p.age
            else:
                citizen = CITY.CITIZEN(
                    name=p.name, age=p.age, uid=self._person_map[i])
                city.add(citizen, rel=CITY.HAS_INHABITANT)

    # OVERRIDE
    def _apply_added(self):
        if self._ran and self._added:
            raise RuntimeError("Do not add cuds_objects "
                               "after running the simulation")
        sorted_added = sorted(
            self._added.values(),
            key=lambda x: x.name if hasattr(x, "name") else "0")
        for added in sorted_added:
            if added.is_a in CITY.PERSON.subclasses and \
                    CITY.IS_PART_OF in added._neighbours and \
                    self.root in added._neighbours[CITY.IS_PART_OF]:
                self._engine.add_person(DummyPerson(added.name, added.age))
                self._person_map.append(added.uid)

    # OVERRIDE
    def _apply_updated(self):
        if self._ran and self._added:
            raise RuntimeError("Do not update cuds_objects after running "
                               + "the simulation")

    # OVERRIDE
    def _apply_deleted(self):
        if self._ran and self._deleted:
            raise RuntimeError("Do not delete cuds_objects after running "
                               + "the simulation")


class DummyPerson():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_older(self, num_years):
        self.age += num_years


class DummySyntacticLayer():
    def __init__(self):
        self.persons = list()
        self.i = 0

    def add_person(self, person):
        self.persons.append(person)

    def get_persons(self):
        return zip(range(self.i, len(self.persons)),
                   self.persons[self.i:])

    def get_inhabitants(self):
        return enumerate(self.persons[:self.i])

    def simulate(self, num_steps):
        self.i += num_steps

        for p in self.persons:
            p.get_older(num_steps)


if __name__ == '__main__':
    unittest.main()
