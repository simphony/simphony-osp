
import time
from typing import Union
from abc import ABC, abstractmethod


class Benchmark(ABC):

    def __init__(self, size: int = 500, *args, **kwargs):
        """Set-up the internal attributes of the benchmark.

        Args:
            size (int): the number of iterations to be performed by the
                benchmark for it to be considered as finished.
        """
        super().__init__(*args, **kwargs)
        self._size = size
        self._iter_times = []
        self._finished = False

    @property
    def started(self) -> bool:
        """Whether the benchmark was iterated at least once."""
        return self.iterations > 0

    @property
    def finished(self) -> bool:
        """Whether the benchmark finished all its programmed iterations."""
        return self._finished or self.iterations >= self.size

    @property
    def executed(self) -> bool:
        """True of the benchmark is started and finished."""
        return self.started and self.finished

    @property
    def duration(self) -> float:
        """The process time of the benchmark.

        The process time is calculated using the time module from the Python
        Standard Library. Check its definition on the library's docs
        https://docs.python.org/dev/library/time.html#time.process_time .
        """
        return float(sum(self._iter_times))

    @property
    def iterations(self) -> int:
        """The number of iterations already executed."""
        return len(self._iter_times)

    @property
    def iteration(self) -> Union[int, None]:
        """The current iteration.

        Returns:
            Union[int, None]: either the current iteration or None if no
                iterations were yet run.
        """
        if self.iterations > 0:
            return self.iterations - 1
        else:
            return None

    @property
    def size(self) -> int:
        """The number of iterations programmed on initialization.

        When the number of executed iterations reaches the value of this
        parameter, the benchmark is finished.
        """
        return self._size

    def _set_up(self):
        """Set up the benchmark. The time spent in the setup is not counted.
        """
        self._benchmark_set_up()

    @abstractmethod
    def _benchmark_set_up(self):
        """Implementation of the setup for a specific benchmark."""
        pass

    def _tear_down(self):
        """Clean up after the benchmark. The time spent is not counted."""
        self._benchmark_tear_down()

    @abstractmethod
    def _benchmark_tear_down(self):
        """Implementation of the teardown for a specific benchmark."""
        pass

    def _iterate(self):
        """Perform one iteration of the benchmark.

        Raises:
            StopIteration: when all the iterations of the benchmark were
                already executed.
        """
        if self.finished:
            raise StopIteration('This benchmark is finished.')
        start = time.process_time()
        self._benchmark_iterate(iteration=self.iterations)
        end = time.process_time()
        self._iter_times.append(end - start)

    @abstractmethod
    def _benchmark_iterate(self, iteration: int = None):
        """Implementation of a benchmark iteration for a specific benchmark.

        The time taken to execute any code inside this method is registered.

        Args:
            iteration (int): the iteration number to be performed.
        """

    def run(self):
        """Run a benchmark from start to finish.

        This method will only work on a benchmark that has not been started
        already. It runs all of its programmed iterations.
        """
        if not self.started and not self.finished:
            self._set_up()
            for i in range(self.size):
                self._iterate()
            self._tear_down()
        elif self.started and not self.finished:
            raise RuntimeError('This benchmark has already started.')
        else:  # Both are true.
            raise StopIteration('This benchmark is finished.')
