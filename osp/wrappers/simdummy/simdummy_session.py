"""A dummy simulation session used for demonstrational and testing purposes.

With each simulation step, the age of all person that are direct
descendents of the Wrapper object will be increased by one.
Each simulation step one person will move to the city and become
an inhabitant.
"""

from osp.core.session.sim_wrapper_session import SimWrapperSession
from osp.core.utils.wrapper_development import change_oclass
from osp.wrappers.simdummy import DummyPerson, DummySyntacticLayer

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry

    Parser().parse("city")
    city = namespace_registry.city


class SimDummySession(SimWrapperSession):
    """A Dummy session for educational and testing purposes."""

    def __init__(self, **kwargs):
        """Initialize the dummy session."""
        super().__init__(engine=DummySyntacticLayer(), **kwargs)
        self._person_map = dict()

    def __str__(self):
        """Convert the dummy session to a string."""
        return "Dummy SimWrapperSession"

    # OVERRIDE
    def _run(self, root_cuds_object):
        """Run the simulation.

        Args:
            root_cuds_object (Cuds): The wrapper object.
        """
        self._engine.simulate(root_cuds_object.numSteps)

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        """Load objects from the dummy backend.

        Args:
            uids (List[Union[UUID, URIRef]): Load the objects with the
                given uids.
            expired (Set[Union[UUID, URIRef]], optional): A set of uids
                that have been marked as expired.. Defaults to None.

        Yields:
            Cuds: A loaded CUDS objects.
        """
        # update the age of each person and delete persons that became citizens
        for uid in uids:
            root_cuds_object = self._registry.get(self.root)
            cities = root_cuds_object.get(oclass=city.City)
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
        """Load the Person CUDS object with given uid from the backend.

        Args:
            uid (Union[UUID, URIRef]): The uid of the CUDS object
            to load.

        Returns:
            Cuds: The loaded Person CUDS object.
        """
        person = self._registry.get(uid)
        idx = self._person_map[uid]
        person.age = self._engine.get_person(idx)[1].age
        if person.is_a(city.Citizen):
            return person
        self._check_convert_to_inhabitant(uid)
        return person

    def _load_city(self, uid):
        """Load the City CUDS object with the given uid from the backend.

        Args:
            uid (Union[UUID, URIRef]): The uid of the City CUDS
            object to load.

        Returns:
            Cuds: The loaded City CUDS object.
        """
        c = self._registry.get(uid)
        inhabitant_uids = set([x.uid for x in c.get(rel=city.hasInhabitant)])
        person_uids = self._person_map.keys() - inhabitant_uids
        for person_uid in person_uids:
            self.refresh(person_uid)
        return c

    def _load_wrapper(self, uid):
        """Load the Wrapper CUDS object.

        Args:
            uid (Union[UUID, URIRef]): The uid of the Wrapper.

        Returns:
            Cuds: The loaded Wrapper object.
        """
        wrapper = self._registry.get(uid)
        for person in wrapper.get(oclass=city.Person):
            self.refresh(person.uid)
        return wrapper

    def _check_convert_to_inhabitant(self, uid):
        """Check whether a Person should be converted to an Inhabitant.

        If the backend converted the Person with the given UUID to
        an inhabitant, this method will change the ontology class
        of the object.

        Args:
            uid (Union[UUID, URIRef]): The uid of the person to
            check.
        """
        wrapper = self._registry.get(self.root)
        c = wrapper.get(oclass=city.City)[0]
        idx = self._person_map[uid]
        is_inhabitant, dummy_person = self._engine.get_person(idx)
        if is_inhabitant:
            person = self._registry.get(uid)
            change_oclass(
                person,
                city.Citizen,
                {"name": dummy_person.name, "age": dummy_person.age},
            )
            wrapper.remove(person, rel=city.hasPart)
            c.add(person, rel=city.hasInhabitant)

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        """Apply the added buffer to the backend.

        Args:
            root_obj (Cuds): The Wrapper CUDS object.
            buffer (dict[Union[UUID, URIRef], Cuds]): The added CUDS objects.

        Raises:
            RuntimeError: It is not allowed to add CUDS objects after
                the simulation has been started.
        """
        if self._ran and buffer:
            raise RuntimeError(
                "Do not add cuds_objects " "after running the simulation"
            )
        sorted_added = sorted(
            buffer.values(),
            key=lambda x: x.name if hasattr(x, "name") else "0",
        )
        for added in sorted_added:
            if added.is_a(city.Person) and self.root in map(
                lambda x: x.uid, added.get(rel=city.isPartOf)
            ):
                idx = self._engine.add_person(
                    DummyPerson(added.name, added.age)
                )
                self._person_map[added.uid] = idx

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        """Apply the updated buffer to the backend.

        Args:
            root_obj (Cuds): The Wrapper Cuds object.
            buffer (dict[Union[UUID, URIRef], Cuds]): The updated CUDS objects.

        Raises:
            RuntimeError: It is not allowed to update CUDS objects
                after the simulation has been started.
        """
        if self._ran and buffer:
            raise RuntimeError(
                "Do not update cuds_objects after running " + "the simulation"
            )

    # OVERRIDE
    def _apply_deleted(self, root_obj, buffer):
        """Apply the deleted buffer to the backend.

        Args:
            root_obj (Cuds): The Wrapper Cuds object.
            buffer (dict[Union[UUID, URIRef], CUDS]): The deleted CUDS objects.

        Raises:
            RuntimeError: It is not allowed to delete CUDS objects
                after the simulation has been started.
        """
        if self._ran and buffer:
            raise RuntimeError(
                "Do not delete cuds_objects after running " + "the simulation"
            )
