"""Test the performance of basic API calls."""

import random
# from .benchmarks import Benchmark
from benchmark import Benchmark

try:
    from osp.core.namespaces import city
except ImportError:  # When the city ontology is not installed.
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city


class CudsCreate(Benchmark):

    def _benchmark_set_up(self):
        pass

    def _benchmark_iterate(self, iteration=None):
        city.Citizen(name='citizen ' + str(iteration),
                     age=random.randint(0, 80))

    def _benchmark_tear_down(self):
        pass


class CudsAddDefault(Benchmark):

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.neighborhoods = [city.Neighborhood(name='neighborhood ' + str(i))
                              for i in range(self.size)]

    def _benchmark_iterate(self, iteration=None):
        """Test the instantiation and type of the objects."""
        self.city.add(self.neighborhoods[iteration])

    def _benchmark_tear_down(self):
        pass


class CudsAddRel(Benchmark):

    def _benchmark_set_up(self):
        self.city = city.City(name='Freiburg')
        self.citizens = [city.Citizen(name='neighborhood ' + str(i))
                         for i in range(self.size)]

    def _benchmark_iterate(self, iteration=None):
        """Test the instantiation and type of the objects."""
        self.city.add(self.citizens[iteration], rel=city.hasInhabitant)

    def _benchmark_tear_down(self):
        pass


if __name__ == '__main__':
    benchmarks = [CudsCreate(), CudsAddDefault(), CudsAddRel()]
    for benchmark in benchmarks:
        benchmark.run()
