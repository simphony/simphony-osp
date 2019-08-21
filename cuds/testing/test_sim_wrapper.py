from cuds.classes.core.session.sim_wrapper_session import SimWrapperSession
from cuds.classes.generated.cuba import CUBA
import cuds.classes
import unittest2 as unittest


class TestSimWrapper(unittest.TestCase):

    def setUp(self):
        pass

    def test_dummy_sim_wrapper(self):
        with DummySimSession() as session:
            wrapper = cuds.classes.CitySimWrapper(num_steps=1, session=session)
            c = cuds.classes.City(name="Freiburg")
            p1 = cuds.classes.Person(name="Hans", age=34)
            p2 = cuds.classes.Person(name="Renate", age=54)
            wrapper.add(c, p1, p2)
            cw = wrapper.get(c.uid)[0]

            session.run()

            self.assertEqual(len(
                wrapper.get(cuba_key=cuds.classes.Person.cuba_key,
                            rel=cuds.classes.HasPart)), 1)
            self.assertEqual(len(
                cw.get(cuba_key=cuds.classes.Citizen.cuba_key,
                       rel=cuds.classes.IsInhabitedBy)), 1)
            self.assertEqual(wrapper.get(p2.uid)[0].name, "Renate")
            self.assertEqual(wrapper.get(p2.uid)[0].age, 55)
            self.assertEqual(cw.get(p1.uid)[0].name, "Hans")
            self.assertEqual(cw.get(p1.uid)[0].age, 35)

            session.run()
            wrapper.add(cuds.classes.Person(name="Peter"))
            self.assertRaises(RuntimeError, session.run)


class DummySimSession(SimWrapperSession):
    def __init__(self):
        super().__init__(engine=DummySyntacticLayer())
        self._person_map = list()

    def __str__(self):
        return "Dummy SimWrapperSession"

    # OVERRIDE
    def _run(self, root_cuds):
        self._engine.simulate(root_cuds.num_steps)

    # OVERRIDE
    def _update_cuds_after_run(self, root_cuds):
        # update the age of each person and delete persons that became citizens
        person_uids = set()
        for i, p in self._engine.get_persons():
            uid = self._person_map[i]
            person_uids.add(uid)
            root_cuds.get(uid)[0].age = p.age
        for p in root_cuds.get(cuba_key=CUBA.PERSON):
            if p.uid not in person_uids:
                root_cuds.remove(p)

        # update the age of the citizens and add new citizens
        city = root_cuds.get(cuba_key=CUBA.CITY)[0]
        for i, p in self._engine.get_inhabitants():
            uid = self._person_map[i]
            inhabitant = city.get(uid)[0]
            if inhabitant:
                inhabitant.age = p.age
            else:
                citizen = cuds.classes.Citizen(name=p.name, age=p.age)
                citizen.uid = self._person_map[i]
                city.add(citizen, rel=cuds.classes.IsInhabitedBy)

    # OVERRIDE
    def _apply_added(self):
        if self._ran and self._added:
            raise RuntimeError("Do not add cuds after running the simulation")
        sorted_added = sorted(
            self._added.values(),
            key=lambda x: x.name if hasattr(x, "name") else "0")
        for added in sorted_added:
            if isinstance(added, cuds.classes.Person) and \
                    self.root in added[cuds.classes.IsPartOf]:
                self._engine.add_person(DummyPerson(added.name, added.age))
                self._person_map.append(added.uid)

    # OVERRIDE
    def _apply_updated(self):
        if self._ran and self._added:
            raise RuntimeError("Do not update cuds after running "
                               + "the simulation")

    # OVERRIDE
    def _apply_deleted(self):
        if self._ran and self._deleted:
            raise RuntimeError("Do not delete cuds after running "
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
