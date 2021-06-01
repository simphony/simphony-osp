"""Test the performance of basic API calls."""

import random
import itertools
import rdflib
from .benchmark import Benchmark

try:
    from osp.core.namespaces import city
except ImportError:  # When the city ontology is not installed.
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city


DEFAULT_SIZE = 1000
WARMUP_ROUNDS = 0
ITERATIONS = 1


def template_benchmark_cuds_api(benchmark, benchmark_class):
    """Wrapper function for the any CUDS API benchmark."""
    benchmark_instance = benchmark_class(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


DEFAULT_SIZE = 1000
WARMUP_ROUNDS = 0
ITERATIONS = 1


class CudsCreate(Benchmark):
    """Benchmark the creation of CUDS objects."""

    def _benchmark_set_up(self):
        pass

    def _benchmark_iterate(self, iteration=None):
        city.Citizen(name='citizen ' + str(iteration),
                     age=random.randint(0, 80))

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_create(benchmark):
    """Wrapper function for the CudsCreate benchmark.

    Makes the CudsCreate benchmark compatible with pytest-benchmark."""
    benchmark_instance = CudsCreate(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `add` method.

class Cuds_add_Default(Benchmark):
    """Benchmark the `add` method using the default relationship."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.neighborhoods = tuple(city.Neighborhood(name=f'neighborhood {i}')
                                   for i in range(self.size))

    def _benchmark_iterate(self, iteration=None):
        self.city.add(self.neighborhoods[iteration])

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_add_default(benchmark):
    """Wrapper function for the Cuds_add_Default benchmark.

    Makes the Cuds_add_Default benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_add_Default(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_add_Rel(Benchmark):
    """Benchmark the `add` method, selecting the relationship."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.citizens = tuple(city.Citizen(name=f'citizen {i}')
                              for i in range(self.size))

    def _benchmark_iterate(self, iteration=None):
        self.city.add(self.citizens[iteration], rel=city.hasInhabitant)

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_add_rel(benchmark):
    """Wrapper function for the Cuds_add_Rel benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_add_Rel)


# `get` method

class Cuds_get_ByuidUUID(Benchmark):
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


def benchmark_cuds_get_byuiduuid(benchmark):
    """Wrapper function for the Cuds_get_ByuidUUID benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_get_ByuidUUID)


class Cuds_get_ByuidURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type IRI)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.iris = tuple(rdflib.URIRef(f'http://example.org/city#Citizen_{i}')
                          for i in range(self.size))
        self.citizens = tuple(city.Citizen(name=f'citizen {i}',
                                           uid=self.iris[i])
                              for i in range(self.size))
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(self.iris[iteration])

    def _benchmark_tear_down(self):
        pass


def benchmark_get_byuiduriref(benchmark):
    """Wrapper function for the Cuds_get_ByuidURIRef benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_get_ByuidURIRef)


class Cuds_get_ByRel(Benchmark):
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


def benchmark_get_byrel(benchmark):
    """Wrapper function for the Cuds_get_ByRel benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_get_ByRel)


class Cuds_get_Byoclass(Benchmark):
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


def benchmark_get_byoclass(benchmark):
    """Wrapper function for the Cuds_get_Byoclass benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_get_Byoclass)


# `iter` method

class Cuds_iter_ByuidUUID(Benchmark):
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


def benchmark_cuds_iter_byuiduuid(benchmark):
    """Wrapper function for the Cuds_iter_ByuidUUID benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_iter_ByuidUUID)


class Cuds_iter_ByuidURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.iris = tuple(rdflib.URIRef(f'http://example.org/city#Citizen_{i}')
                          for i in range(self.size))
        self.citizens = tuple(city.Citizen(name=f'citizen {i}',
                                           uid=self.iris[i])
                              for i in range(self.size))
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)
        self.iterator = self.city.iter(*self.iris)

    def _benchmark_iterate(self, iteration: int = None):
        next(self.iterator)

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_iter_byuiduriref(benchmark):
    """Wrapper function for the Cuds_iter_ByuidURIRef benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_iter_ByuidURIRef)


class Cuds_iter_ByRel(Benchmark):
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


def benchmark_cuds_iter_byrel(benchmark):
    """Wrapper function for the Cuds_iter_ByRel benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_iter_ByRel)


class Cuds_iter_Byoclass(Benchmark):
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


def benchmark_iter_byoclass(benchmark):
    """Wrapper function for the Cuds_iter_Byoclass benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_iter_Byoclass)


# `is_a` method

class Cuds_is_a(Benchmark):
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


def benchmark_cuds_is_a(benchmark):
    """Wrapper function for the Cuds_is_a benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_is_a)


# `oclass` property

class Cuds_oclass(Benchmark):
    """Benchmark getting the oclass of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.oclass

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_oclass(benchmark):
    """Wrapper function for the Cuds_oclass benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_oclass)


# `uid` property

class Cuds_uid(Benchmark):
    """Benchmark getting the uid of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.uid

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_uid(benchmark):
    """Wrapper function for the Cuds_uid benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_uid)


# `iri` property

class Cuds_iri(Benchmark):
    """Benchmark getting the iri of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.iri

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_iri(benchmark):
    """Wrapper function for the Cuds_iri benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_iri)


# get attributes

class Cuds_attributes(Benchmark):
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


def benchmark_cuds_attributes(benchmark):
    """Wrapper function for the Cuds_attributes benchmark."""
    return template_benchmark_cuds_api(benchmark, Cuds_attributes)


def benchmark_cuds_add_rel(benchmark):
    """Wrapper function for the Cuds_add_Rel benchmark.

    Makes the Cuds_add_Rel benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_add_Rel(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `get` method

class Cuds_get_ByuidUUID(Benchmark):
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


def benchmark_cuds_get_byuiduuid(benchmark):
    """Wrapper function for the Cuds_get_ByuidUUID benchmark.

    Makes the Cuds_get_ByuidUUID benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_get_ByuidUUID(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_get_ByuidURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type IRI)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.iris = tuple(rdflib.URIRef(f'http://example.org/city#Citizen_{i}')
                          for i in range(self.size))
        self.citizens = tuple(city.Citizen(name=f'citizen {i}',
                                           uid=self.iris[i])
                              for i in range(self.size))
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)

    def _benchmark_iterate(self, iteration: int = None):
        self.city.get(self.iris[iteration])

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_get_byuiduriref(benchmark):
    """Wrapper function for the Cuds_get_ByuidURIRef benchmark.

    Makes the Cuds_get_ByuidURIRef benchmark compatible with
    pytest-benchmark."""
    benchmark_instance = Cuds_get_ByuidURIRef(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_get_ByRel(Benchmark):
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


def benchmark_cuds_get_byrel(benchmark):
    """Wrapper function for the Cuds_get_ByRel benchmark.

    Makes the Cuds_get_ByRel benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_get_ByRel(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_get_Byoclass(Benchmark):
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


def benchmark_cuds_get_byoclass(benchmark):
    """Wrapper function for the Cuds_get_Byoclass benchmark.

    Makes the Cuds_get_Byoclass benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_get_Byoclass(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `iter` method

class Cuds_iter_ByuidUUID(Benchmark):
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


def benchmark_cuds_iter_byuiduuid(benchmark):
    """Wrapper function for the Cuds_iter_ByuidUUID benchmark.

    Makes the Cuds_iter_ByuidUUID benchmark compatible with
    pytest-benchmark."""
    benchmark_instance = Cuds_iter_ByuidUUID(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_iter_ByuidURIRef(Benchmark):
    """Benchmark getting CUDS objects by uid (of type UUID)."""

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.iris = tuple(rdflib.URIRef(f'http://example.org/city#Citizen_{i}')
                          for i in range(self.size))
        self.citizens = tuple(city.Citizen(name=f'citizen {i}',
                                           uid=self.iris[i])
                              for i in range(self.size))
        for citizen in self.citizens:
            self.city.add(citizen, rel=city.hasInhabitant)
        self.iterator = self.city.iter(*self.iris)

    def _benchmark_iterate(self, iteration: int = None):
        next(self.iterator)

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_iter_byuiduriref(benchmark):
    """Wrapper function for the Cuds_iter_ByuidURIRef benchmark.

    Makes the Cuds_iter_ByuidURIRef benchmark compatible with
    pytest-benchmark."""
    benchmark_instance = Cuds_iter_ByuidURIRef(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_iter_ByRel(Benchmark):
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


def benchmark_cuds_iter_byrel(benchmark):
    """Wrapper function for the Cuds_iter_ByRel benchmark.

    Makes the Cuds_iter_ByRel benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_iter_ByRel(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


class Cuds_iter_Byoclass(Benchmark):
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


def benchmark_cuds_iter_byoclass(benchmark):
    """Wrapper function for the Cuds_iter_Byoclass benchmark.

    Makes the Cuds_iter_Byoclass benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_iter_Byoclass(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `is_a` method

class Cuds_is_a(Benchmark):
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


def benchmark_cuds_is_a(benchmark):
    """Wrapper function for the Cuds_is_a benchmark.

    Makes the Cuds_is_a benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_is_a(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `oclass` property

class Cuds_oclass(Benchmark):
    """Benchmark getting the oclass of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.oclass

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_oclass(benchmark):
    """Wrapper function for the Cuds_oclass benchmark.

    Makes the Cuds_oclass benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_oclass(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `uid` property

class Cuds_uid(Benchmark):
    """Benchmark getting the uid of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.uid

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_uid(benchmark):
    """Wrapper function for the Cuds_uid benchmark.

    Makes the Cuds_uid benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_uid(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# `iri` property

class Cuds_iri(Benchmark):
    """Benchmark getting the iri of CUDS objects."""

    def _benchmark_set_up(self):
        self.citizen = city.Citizen(name='someone')

    def _benchmark_iterate(self, iteration: int = None):
        self.citizen.iri

    def _benchmark_tear_down(self):
        pass


def benchmark_cuds_iri(benchmark):
    """Wrapper function for the Cuds_iri benchmark.

    Makes the Cuds_iri benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_iri(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


# get attributes

class Cuds_attributes(Benchmark):
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


def benchmark_cuds_attributes(benchmark):
    """Wrapper function for the Cuds_attributes benchmark.

    Makes the Cuds_attributes benchmark compatible with pytest-benchmark."""
    benchmark_instance = Cuds_attributes(size=DEFAULT_SIZE)
    benchmark_instance.set_up()
    benchmark.pedantic(benchmark_instance.iterate,
                       rounds=benchmark_instance.size,
                       warmup_rounds=WARMUP_ROUNDS,
                       iterations=ITERATIONS)
    benchmark_instance.tear_down()


if __name__ == '__main__':
    pass
