"""Test the performance of basic API calls."""

import itertools
import random

import rdflib

from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.session import Session

from .benchmark import Benchmark

DEFAULT_SIZE = 500


class EntityIri(Benchmark):
    """Benchmark getting the iri of ontology entities."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.citizen = city.Citizen(name="someone", age=25)

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.iri

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_entity_iri(benchmark):
    """Wrapper function for the IndividualIri benchmark."""
    return EntityIri.iterate_pytest_benchmark(benchmark, size=DEFAULT_SIZE)


class EntityIdentifier(Benchmark):
    """Benchmark getting the identifier of ontology entities."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.citizen = city.Citizen(name="someone", age=25)

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.identifier

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_entity_identifier(benchmark):
    """Wrapper function for the IndividualUID benchmark."""
    return EntityIdentifier.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualCreate(Benchmark):
    """Benchmark the `__call__` method (creation) of ontology individuals."""

    ontology: Session
    prev_default_ontology: Session
    city: OntologyNamespace

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city = city

    def _benchmark_iterate(self, iteration=None):
        self.city.Citizen(
            name="citizen " + str(iteration), age=random.randint(0, 80)
        )

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_create(benchmark):
    """Wrapper function for the IndividualCreate benchmark."""
    return IndividualCreate.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualIsA(Benchmark):
    """Benchmark the `is_a` method of ontology individuals."""

    ontology: Session
    prev_default_ontology: Session

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        classes = (
            city.ArchitecturalComponent,
            city.Floor,
        )
        classes_age = (
            city.LivingBeing,
            city.Citizen,
            city.Person,
        )
        classes_coordinates = (
            city.City,
            city.Street,
            city.Neighborhood,
            city.PopulatedPlace,
        )
        classes_name = (
            city.ArchitecturalStructure,
            city.Building,
        )
        stuff = tuple(class_() for class_ in classes)
        aged_stuff = tuple(
            class_(name="name", age=25) for class_ in classes_age
        )
        coordinated_stuff = tuple(
            class_(name="name", coordinates=[0, 0])
            for class_ in classes_coordinates
        )
        named_stuff = tuple(class_(name="name") for class_ in classes_name)

        self.iterator_stuff = itertools.cycle(
            stuff + aged_stuff + coordinated_stuff + named_stuff
        )
        self.classes = (
            classes + classes_age + classes_coordinates + named_stuff
        )

    def _benchmark_iterate(self, iteration: int = None):
        individual = next(self.iterator_stuff)
        class_ = random.choice(self.classes)
        individual.is_a(class_)

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_is_a(benchmark):
    """Wrapper function for the IndividualIsA benchmark."""
    return IndividualIsA.iterate_pytest_benchmark(benchmark, size=DEFAULT_SIZE)


class IndividualClasses(Benchmark):
    """Benchmark the `classes` method of ontology individuals."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.citizen = city.Citizen(name="someone", age=25)

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.classes

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_classes(benchmark):
    """Wrapper function for the IndividualClasses benchmark."""
    return IndividualClasses.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualConnect(Benchmark):
    """Benchmark the `add` method, selecting the relationship."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city_namespace = city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        self.citizens = tuple(
            city.Citizen(name=f"citizen {i}", age=25) for i in range(self.size)
        )

    def _benchmark_iterate(self, iteration=None):
        self.city.connect(
            self.citizens[iteration], rel=self.city_namespace.hasInhabitant
        )

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_connect(benchmark):
    """Wrapper function for the IndividualAddRel benchmark."""
    return IndividualConnect.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualGetByIdentifier(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        self.citizens = tuple(
            city.Citizen(name=f"citizen {i}", age=25) for i in range(self.size)
        )
        self.identifiers = tuple(
            citizen.identifier for citizen in self.citizens
        )
        for citizen in self.citizens:
            self.city.connect(citizen, rel=city.hasInhabitant)

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(self.identifiers[iteration])

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_get_byidentifier(benchmark):
    """Wrapper function for the IndividualGetByIdentifier benchmark."""
    return IndividualGetByIdentifier.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualGetByIdentifierURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type IRI)."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        self.iris = tuple(
            rdflib.URIRef(f"http://example.org/city#Citizen_{i}")
            for i in range(self.size)
        )
        self.citizens = tuple(
            city.Citizen(name=f"citizen {i}", age=25, iri=self.iris[i])
            for i in range(self.size)
        )
        for citizen in self.citizens:
            self.city.connect(citizen, rel=city.hasInhabitant)

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(self.iris[iteration])

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_get_byidentifieruriref(benchmark):
    """Wrapper function for the IndividualGetByIdentifierURIRef benchmark."""
    return IndividualGetByIdentifierURIRef.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualGetByRel(Benchmark):
    """Benchmark getting CUDS objects by relationship."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city_namespace = city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        citizen = city.Citizen(name="Citizen", age=25)
        streets = tuple(
            city.Street(name=f"street {i}", coordinates=[0, 0])
            for i in range(self.size - 1)
        )
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            self.city.connect(thing, rel=rel.get(i, city.hasPart))

    def _benchmark_iterate(self, iteration: int = None):
        tuple(self.city.get(rel=self.city_namespace.hasInhabitant))

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_get_byrel(benchmark):
    """Wrapper function for the IndividualGetByRel benchmark."""
    return IndividualGetByRel.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualGetByOclass(Benchmark):
    """Benchmark getting CUDS objects by oclass."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city_namespace = city

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        citizen = city.Citizen(name="Citizen", age=25)
        streets = tuple(
            city.Street(name=f"street {i}", coordinates=[0, 0])
            for i in range(self.size - 1)
        )
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            fr.connect(thing, rel=rel.get(i, city.hasPart))

        self.city = fr

    def _benchmark_iterate(self, iteration: int = None):
        tuple(self.city.get(oclass=self.city_namespace.Citizen))

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_get_byoclass(benchmark):
    """Wrapper function for the IndividualGetByOclass benchmark."""
    return IndividualGetByOclass.iterate_pytest_benchmark(
        benchmark, DEFAULT_SIZE
    )


class IndividualIterByIdentifier(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        self.citizens = tuple(
            city.Citizen(name=f"citizen {i}", age=25) for i in range(self.size)
        )
        self.identifiers = tuple(
            citizen.identifier for citizen in self.citizens
        )
        for citizen in self.citizens:
            self.city.connect(citizen, rel=city.hasInhabitant)
        self.iterator = self.city.iter(*self.identifiers)

    def _benchmark_iterate(self, iteration: int = None):
        next(self.iterator)

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_iter_byidentifier(benchmark):
    """Wrapper function for the IndividualIterByIdentifier benchmark."""
    return IndividualIterByIdentifier.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualIterByIdentifierURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        self.iris = tuple(
            rdflib.URIRef(f"http://example.org/city#Citizen_{i}")
            for i in range(self.size)
        )
        self.citizens = tuple(
            city.Citizen(name=f"citizen {i}", age=25, iri=self.iris[i])
            for i in range(self.size)
        )
        for citizen in self.citizens:
            self.city.connect(citizen, rel=city.hasInhabitant)
        self.iterator = self.city.iter(*self.iris)

    def _benchmark_iterate(self, iteration: int = None):
        next(self.iterator)

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_iter_byidentifieruriref(benchmark):
    """Wrapper function for the IndividualIterByIdentifierURIRef benchmark."""
    return IndividualIterByIdentifierURIRef.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualIterByRel(Benchmark):
    """Benchmark getting CUDS objects by relationship."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city_namespace = city

        self.city = city.City(name="Freiburg", coordinates=[0, 0])
        citizen = city.Citizen(name="Citizen", age=25)
        streets = tuple(
            city.Street(name=f"street {i}", coordinates=[0, 0])
            for i in range(self.size - 1)
        )
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            self.city.connect(thing, rel=rel.get(i, city.hasPart))

    def _benchmark_iterate(self, iteration: int = None):
        next(self.city.iter(rel=self.city_namespace.hasInhabitant))

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_iter_byrel(benchmark):
    """Wrapper function for the IndividualIterByRel benchmark."""
    return IndividualIterByRel.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualIterByOclass(Benchmark):
    """Benchmark getting CUDS objects by oclass."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.city_namespace = city

        fr = city.City(name="Freiburg", coordinates=[0, 0])
        citizen = city.Citizen(name="Citizen", age=25)
        streets = tuple(
            city.Street(name=f"street {i}", coordinates=[0, 0])
            for i in range(self.size - 1)
        )
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            fr.connect(thing, rel=rel.get(i, city.hasPart))

        self.city = fr

    def _benchmark_iterate(self, iteration: int = None):
        next(self.city.iter(oclass=self.city_namespace.Citizen))

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_iter_byoclass(benchmark):
    """Wrapper function for the IndividualIterByOclass benchmark."""
    return IndividualIterByOclass.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


class IndividualGetAttr(Benchmark):
    """Benchmark getting attributes of ontology individuals."""

    def _benchmark_set_up(self):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SIMPHONY, OWL, RDFS and City.
        """
        self.ontology = Session(identifier="test-tbox", ontology=True)
        self.ontology.load_parser(OntologyParser.get_parser("city"))
        self.prev_default_ontology = Session.default_ontology
        Session.default_ontology = self.ontology

        from simphony_osp.namespaces import city

        self.citizen = city.Citizen(name="Lukas", age=93)
        self.city = city.City(name="Freiburg", coordinates=[108, 49])
        self.address = city.Address(
            name="Street123", postalCode=79111, number=1
        )
        self.things = itertools.cycle((self.citizen, self.city, self.address))
        self.attributes = itertools.cycle(
            (("age",), ("coordinates",), ("postalCode",))
        )

    def _benchmark_iterate(self, iteration: int = None):
        thing = next(self.things)
        attributes = next(self.attributes)
        for attr in attributes:
            getattr(thing, attr)

    def _benchmark_tear_down(self):
        """Restore the previous default TBox."""
        Session.default_ontology = self.prev_default_ontology


def benchmark_individual_getattr(benchmark):
    """Wrapper function for the IndividualAttributes benchmark."""
    return IndividualGetAttr.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE
    )


if __name__ == "__main__":
    pass
