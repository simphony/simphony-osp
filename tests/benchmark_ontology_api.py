"""Test the performance of basic API calls."""

import random
import itertools
import rdflib
from .benchmark import Benchmark
from osp.core.ontology.parser import OntologyParser
from osp.core.session.session import Session
from osp.core.utils.datatypes import UID

try:
    from osp.core.namespaces import city
except ImportError:  # When the city ontology is not installed.
    Session.ontology.load_parser(OntologyParser.get_parser('city'))
    city = Session.ontology.get_namespace('city')


DEFAULT_SIZE = 500


class IndividualCreate(Benchmark):
    """Benchmark the creation of CUDS objects."""

    def _benchmark_set_up(self):
        pass

    def _benchmark_iterate(self, iteration=None):
        city.Citizen(name='citizen ' + str(iteration),
                     age=random.randint(0, 80))

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_create(benchmark):
    """Wrapper function for the IndividualCreate benchmark."""
    return IndividualCreate.iterate_pytest_benchmark(benchmark,
                                                     size=DEFAULT_SIZE)


# `add` method.

class IndividualAddDefault(Benchmark):
    """Benchmark the `add` method using the default relationship."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.neighborhoods = tuple(city.Neighborhood(name=f'neighborhood {i}')
                                   for i in range(self.size))

    def _benchmark_iterate(self, iteration=None):
        self.city.add(self.neighborhoods[iteration])

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_add_default(benchmark):
    """Wrapper function for the IndividualAddDefault benchmark."""
    return IndividualAddDefault.iterate_pytest_benchmark(benchmark,
                                                         size=DEFAULT_SIZE)


class IndividualAddRel(Benchmark):
    """Benchmark the `add` method, selecting the relationship."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.citizens = tuple(city.Citizen(name=f'citizen {i}')
                              for i in range(self.size))

    def _benchmark_iterate(self, iteration=None):
        self.city.add(self.citizens[iteration], rel=city.hasInhabitant)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_add_rel(benchmark):
    """Wrapper function for the IndividualAddRel benchmark."""
    return IndividualAddRel.iterate_pytest_benchmark(benchmark,
                                                     size=DEFAULT_SIZE)


# `get` method

class IndividualGetByUIDUUID(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.citizens = tuple(city.Citizen(name=f'citizen {i}')
                              for i in range(self.size))
        self.uids = tuple(citizen.uid for citizen in self.citizens)
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(self.uids[iteration])

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_get_byuiduuid(benchmark):
    """Wrapper function for the IndividualGetByUIDUUID benchmark."""
    return IndividualGetByUIDUUID.iterate_pytest_benchmark(benchmark,
                                                           size=DEFAULT_SIZE)


class IndividualGetByUIDURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type IRI)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.iris = tuple(rdflib.URIRef(f'http://example.org/city#Citizen_{i}')
                          for i in range(self.size))
        self.uids = tuple(UID(iri) for iri in self.iris)
        self.citizens = tuple(city.Citizen(name=f'citizen {i}',
                                           iri=self.iris[i])
                              for i in range(self.size))
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(self.uids[iteration])

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_get_byuiduriref(benchmark):
    """Wrapper function for the IndividualGetByUIDURIRef benchmark."""
    return IndividualGetByUIDURIRef.iterate_pytest_benchmark(benchmark,
                                                             size=DEFAULT_SIZE)


class IndividualGetByRel(Benchmark):
    """Benchmark getting CUDS objects by relationship."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        citizen = city.Citizen(name='Citizen')
        streets = tuple(city.Street(name=f'street {i}')
                        for i in range(self.size - 1))
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            self.city.add(thing, rel=rel.get(i, city.hasPart))

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(rel=city.hasInhabitant)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_get_byrel(benchmark):
    """Wrapper function for the IndividualGetByRel benchmark."""
    return IndividualGetByRel.iterate_pytest_benchmark(benchmark,
                                                       size=DEFAULT_SIZE)


class IndividualGetByOclass(Benchmark):
    """Benchmark getting CUDS objects by oclass."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        citizen = city.Citizen(name='Citizen')
        streets = tuple(city.Street(name=f'street {i}')
                        for i in range(self.size - 1))
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            self.city.add(thing, rel=rel.get(i, city.hasPart))

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(oclass=city.Citizen)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_get_byoclass(benchmark):
    """Wrapper function for the IndividualGetByOclass benchmark."""
    return IndividualGetByOclass.iterate_pytest_benchmark(benchmark,
                                                          DEFAULT_SIZE)


# `iter` method

class IndividualIterByUIDUUID(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.citizens = tuple(city.Citizen(name=f'citizen {i}')
                              for i in range(self.size))
        self.uids = tuple(citizen.uid for citizen in self.citizens)
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)
        self.iterator = self.city.iter(*self.uids)

    def _benchmark_iterate(self, iteration: int = None):
        next(self.iterator)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_iter_byuiduuid(benchmark):
    """Wrapper function for the IndividualIterByUIDUUID benchmark."""
    return IndividualIterByUIDUUID.iterate_pytest_benchmark(benchmark,
                                                            size=DEFAULT_SIZE)


class IndividualIterByUIDURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.iris = tuple(rdflib.URIRef(f'http://example.org/city#Citizen_{i}')
                          for i in range(self.size))
        self.citizens = tuple(city.Citizen(name=f'citizen {i}',
                                           iri=self.iris[i])
                              for i in range(self.size))
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)
        self.iterator = self.city.iter(*map(UID, self.iris))

    def _benchmark_iterate(self, iteration: int = None):
        next(self.iterator)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_iter_byuiduriref(benchmark):
    """Wrapper function for the IndividualIterByUIDURIRef benchmark."""
    return IndividualIterByUIDURIRef.iterate_pytest_benchmark(
        benchmark, size=DEFAULT_SIZE)


class IndividualIterByRel(Benchmark):
    """Benchmark getting CUDS objects by relationship."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        citizen = city.Citizen(name='Citizen')
        streets = tuple(city.Street(name=f'street {i}')
                        for i in range(self.size - 1))
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            self.city.add(thing, rel=rel.get(i, city.hasPart))

    def _benchmark_iterate(self, iteration: int = None):
        next(self.city.iter(rel=city.hasInhabitant))

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_iter_byrel(benchmark):
    """Wrapper function for the IndividualIterByRel benchmark."""
    return IndividualIterByRel.iterate_pytest_benchmark(benchmark,
                                                        size=DEFAULT_SIZE)


class IndividualIterByOclass(Benchmark):
    """Benchmark getting CUDS objects by oclass."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        citizen = city.Citizen(name='Citizen')
        streets = tuple(city.Street(name=f'street {i}')
                        for i in range(self.size - 1))
        position = random.randint(0, (self.size - 1) - 1)
        things = list(streets)
        things.insert(position, citizen)
        things = tuple(things)
        rel = {position: city.hasInhabitant}
        for i, thing in enumerate(things):
            self.city.add(thing, rel=rel.get(i, city.hasPart))

    def _benchmark_iterate(self, iteration: int = None):
        next(self.city.iter(oclass=city.Citizen))

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_iter_byoclass(benchmark):
    """Wrapper function for the IndividualIterByOclass benchmark."""
    return IndividualIterByOclass.iterate_pytest_benchmark(benchmark,
                                                           size=DEFAULT_SIZE)


# `is_a` method

class IndividualIsA(Benchmark):
    """Benchmark checking the oclass of CUDS objects."""

    def _benchmark_set_up(self):
        oclasses_noname = (city.LivingBeing, city.ArchitecturalComponent,
                           city.Citizen, city.Person, city.Floor)
        oclasses_name = (city.City, city.ArchitecturalStructure, city.Street,
                         city.Neighborhood, city.PopulatedPlace, city.Building)
        unnamed_stuff = tuple(oclass() for oclass in oclasses_noname)
        named_stuff = tuple(oclass(name='name') for oclass in oclasses_name)
        self.iterator_stuff = itertools.cycle(unnamed_stuff + named_stuff)
        self.oclasses = oclasses_noname + oclasses_name

    def _benchmark_iterate(self, iteration: int = None):
        cuds = next(self.iterator_stuff)
        oclass = random.choice(self.oclasses)
        cuds.is_a(oclass)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_is_a(benchmark):
    """Wrapper function for the IndividualIsA benchmark."""
    return IndividualIsA.iterate_pytest_benchmark(benchmark, size=DEFAULT_SIZE)


# `oclass` property

class IndividualOclass(Benchmark):
    """Benchmark getting the oclass of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.oclass

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_oclass(benchmark):
    """Wrapper function for the IndividualOclass benchmark."""
    return IndividualOclass.iterate_pytest_benchmark(benchmark,
                                                     size=DEFAULT_SIZE)


# `uid` property

class IndividualUID(Benchmark):
    """Benchmark getting the uid of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.uid

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_uid(benchmark):
    """Wrapper function for the IndividualUID benchmark."""
    return IndividualUID.iterate_pytest_benchmark(benchmark, size=DEFAULT_SIZE)


# `iri` property

class IndividualIri(Benchmark):
    """Benchmark getting the iri of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.iri

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_iri(benchmark):
    """Wrapper function for the IndividualIri benchmark."""
    return IndividualIri.iterate_pytest_benchmark(benchmark, size=DEFAULT_SIZE)


# get attributes

class IndividualAttributes(Benchmark):
    """Benchmark fetching attributes of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='Lukas', age=93)
        self.city = city.City(name='Freiburg', coordinates=[108, 49])
        self.address = city.Address(postalCode=79111)
        self.things = itertools.cycle((self.citizen, self.city, self.address))
        self.attributes = itertools.cycle((('age', ),
                                           ('coordinates', ),
                                           ('postalCode', )))

    def _benchmark_iterate(self, iteration: int = None):
        thing = next(self.things)
        attributes = next(self.attributes)
        for attr in attributes:
            getattr(thing, attr)

    def _benchmark_tear_down(self):
        pass


def benchmark_individual_attributes(benchmark):
    """Wrapper function for the IndividualAttributes benchmark."""
    return IndividualAttributes.iterate_pytest_benchmark(benchmark,
                                                         size=DEFAULT_SIZE)


if __name__ == '__main__':
    pass
