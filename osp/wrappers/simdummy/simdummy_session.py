from osp.wrappers.simdummy import (
    DummySyntacticLayer, DummyPerson
)
from osp.core.session.sim_wrapper_session import SimWrapperSession
from osp.core.utils import change_oclass


class SimDummySession(SimWrapperSession):
    def __init__(self, **kwargs):
        super().__init__(engine=DummySyntacticLayer(), **kwargs)
        from osp.core.namespaces import city
        self.onto = city
        self._person_map = dict()

    def __str__(self):
        return "Dummy SimWrapperSession"

    # OVERRIDE
    def _run(self, root_cuds_object):
        self._engine.simulate(root_cuds_object.numSteps)

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        # update the age of each person and delete persons that became citizens
        for uid in uids:
            root_cuds_object = self._registry.get(self.root)
            cities = root_cuds_object.get(oclass=self.onto.City)
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
        if person.is_a(self.onto.CITIZEN):
            return person
        self._check_convert_to_inhabitant(uid)
        return person

    def _load_city(self, uid):
        c = self._registry.get(uid)
        inhabitant_uids = set(
            [x.uid for x in c.get(rel=self.onto.HAS_INHABITANT)]
        )
        person_uids = self._person_map.keys() - inhabitant_uids
        for person_uid in person_uids:
            self.refresh(person_uid)
        return c

    def _load_wrapper(self, uid):
        wrapper = self._registry.get(uid)
        for person in wrapper.get(oclass=self.onto.Person):
            self.refresh(person.uid)
        return wrapper

    def _check_convert_to_inhabitant(self, uid):
        wrapper = self._registry.get(self.root)
        c = wrapper.get(oclass=self.onto.City)[0]
        idx = self._person_map[uid]
        is_inhabitant, dummy_person = self._engine.get_person(idx)
        if is_inhabitant:
            person = self._registry.get(uid)
            change_oclass(person, self.onto.CITIZEN,
                          {"name": dummy_person.name,
                           "age": dummy_person.age})
            wrapper.remove(person, rel=self.onto.HAS_PART)
            c.add(person, rel=self.onto.HAS_INHABITANT)

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
                added.is_a(self.onto.Person)
                and self.root in map(lambda x: x.uid,
                                     added.get(rel=self.onto.isPartOf))
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
