from osp.core.session.sim_wrapper_session import SimWrapperSession
from osp.core.utils import change_oclass

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")


class DummySimWrapperSession(SimWrapperSession):
    def __init__(self, **kwargs):
        super().__init__(engine=DummySyntacticLayer(), **kwargs)
        self._person_map = dict()

    def __str__(self):
        return "Dummy SimWrapperSession"

    # OVERRIDE
    def _run(self, root_cuds_object):
        self._engine.simulate(root_cuds_object.num_steps)

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        # update the age of each person and delete persons that became citizens
        for uid in uids:
            root_cuds_object = self._registry.get(self.root)
            cities = root_cuds_object.get(oclass=CITY.CITY)
            if uid == self.root:
                yield self._load_wrapper(uid)
            elif cities and uid == cities[0].uid:
                assert len(cities) == 1, len(cities)
                yield self._load_city(uid)
            elif uid in self._person_map:
                yield self._load_person(uid)
            elif uid in self._registry:
                yield self._registry.get(uid)
            else:
                yield None

    def _load_person(self, uid):
        person = self._registry.get(uid)
        idx = self._person_map[uid]
        person.age = self._engine.get_person(idx)[1].age
        if person.is_a(CITY.CITIZEN):
            return person
        self._check_convert_to_inhabitant(uid)
        return person

    def _load_city(self, uid):
        city = self._registry.get(uid)
        inhabitant_uids = set([x.uid
                               for x in city.get(rel=CITY.HAS_INHABITANT)])
        person_uids = self._person_map.keys() - inhabitant_uids
        for person_uid in person_uids:
            self.refresh(person_uid)
        return city

    def _load_wrapper(self, uid):
        wrapper = self._registry.get(uid)
        for person in wrapper.get(oclass=CITY.PERSON):
            self.refresh(person.uid)
        return wrapper

    def _check_convert_to_inhabitant(self, uid):
        wrapper = self._registry.get(self.root)
        city = wrapper.get(oclass=CITY.CITY)[0]
        idx = self._person_map[uid]
        is_inhabitant, dummy_person = self._engine.get_person(idx)
        if is_inhabitant:
            person = self._registry.get(uid)
            change_oclass(person, CITY.CITIZEN,
                          {"name": dummy_person.name,
                           "age": dummy_person.age})
            wrapper.remove(person, rel=CITY.HAS_PART)
            city.add(person, rel=CITY.HAS_INHABITANT)

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        if self._ran and buffer:
            raise RuntimeError("Do not add cuds_objects "
                               "after running the simulation")
        sorted_added = sorted(
            buffer.values(),
            key=lambda x: x.name if hasattr(x, "name") else "0")
        for added in sorted_added:
            if (
                added.is_a(CITY.PERSON)
                and self.root in map(lambda x: x.uid,
                                     added.get(rel=CITY.IS_PART_OF))
            ):
                idx = self._engine.add_person(DummyPerson(added.name,
                                                          added.age))
                self._person_map[added.uid] = idx

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        if self._ran and buffer:
            raise RuntimeError("Do not update cuds_objects after running "
                               + "the simulation")

    # OVERRIDE
    def _apply_deleted(self, root_obj, buffer):
        if self._ran and buffer:
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
        return len(self.persons) - 1

    def get_person(self, idx):
        return idx < self.i, self.persons[idx]

    def simulate(self, num_steps):
        self.i += num_steps

        for p in self.persons:
            p.get_older(num_steps)
