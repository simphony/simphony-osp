"""Utility resources for the ontology module."""

from abc import ABC, abstractmethod
from typing import Any, Iterable, Iterator, MutableSet, Set


class DataStructureSet(ABC, MutableSet):
    """As set-like object that acts as an interface to another data structure.

    This class looks like and acts like the standard `set`, but the data it
    holds is stored on a different data structure. When an instance is read
    or when it is modified in-place, specific methods defined to interact
    with the data structure are called to reflect the changes.

    This class does not hold any object-related information itself, thus
    it is safe to spawn multiple instances linked to the same data
    structure (when single-threading).
    """

    @property
    @abstractmethod
    def _underlying_set(self) -> set:
        """The associated set of values from the connected data structured.

        Returns:
            The mentioned underlying set.
        """
        pass

    @abstractmethod
    def update(self, other: Iterable) -> None:
        """Update a set with the union of itself and others."""
        pass

    @abstractmethod
    def intersection_update(self, other: Iterable):
        """Update a set with the intersection of itself and another."""

    @abstractmethod
    def difference_update(self, other: Iterable):
        """Remove all elements of another set from this set."""
        pass

    @abstractmethod
    def symmetric_difference_update(self, other: Iterable):
        """Update a set with the symmetric difference of itself and another."""
        pass

    def __repr__(self) -> str:
        """Return repr(self)."""
        return self._underlying_set.__repr__()

    def __str__(self) -> str:
        """Return str(self)."""
        return self._underlying_set.__str__()

    def __format__(self, format_spec: str) -> str:
        """Default object formatter."""
        return self._underlying_set.__format__(format_spec)

    def __contains__(self, item: Any) -> bool:
        """Return y in x."""
        return item in self._underlying_set

    def __iter__(self) -> Iterator:
        """Implement iter(self)."""
        yield from self._underlying_set

    def __len__(self) -> int:
        """Return len(self)."""
        return len(self._underlying_set)

    def __le__(self, other: Set) -> bool:
        """Return self<=other."""
        return self._underlying_set.__le__(other)

    def __lt__(self, other: Set) -> bool:
        """Return self<other."""
        return self._underlying_set.__lt__(other)

    def __eq__(self, other: Set) -> bool:
        """Return self==other."""
        return self._underlying_set.__eq__(other)

    def __ne__(self, other: Set) -> bool:
        """Return self!=other."""
        return self._underlying_set.__ne__(other)

    def __gt__(self, other: Set) -> bool:
        """Return self>other."""
        return self._underlying_set.__gt__(other)

    def __ge__(self, other: Set) -> bool:
        """Return self>=other."""
        return self._underlying_set.__ge__(other)

    def __and__(self, other: Set) -> set:
        """Return self&other."""
        return self._underlying_set.__and__(other)

    def __radd__(self, other: Set) -> set:
        """Return other&self."""
        return other & self._underlying_set

    def __ror__(self, other: Set) -> set:
        """Return other|self."""
        return other | self._underlying_set

    def __rsub__(self, other: set) -> set:
        """Return value-self."""
        return other - self._underlying_set

    def __rxor__(self, other: set) -> set:
        """Return value^self."""
        return other ^ self._underlying_set

    def __or__(self, other: Set) -> set:
        """Return self|other."""
        return self._underlying_set.__or__(other)

    def __sub__(self, other: Set) -> set:
        """Return self-other."""
        return self._underlying_set.__sub__(other)

    def __xor__(self, other: Set) -> set:
        """Return self^other."""
        return self._underlying_set.__xor__(other)

    def __iadd__(self, other: Any) -> 'DataStructureSet':
        """Return self+=other (equivalent to self|=other)."""
        if isinstance(other, (Set, MutableSet)):
            # Apparently instances of MutableSet are not instances of Set.
            return self.__ior__(other)
        else:
            return self.__ior__({other})

    def __isub__(self, other: Any) -> 'DataStructureSet':
        """Return self-=other.

        Based on `difference_update`.
        """
        if isinstance(other, (Set, MutableSet)):
            # Apparently instances of MutableSet are not instances of Set.
            self.difference_update(other)
        else:
            self.difference_update({other})
        return self

    def __ior__(self, other: Set) -> 'DataStructureSet':
        """Return self|=other.

        Should perform the union on the underlying data structure.
        """
        self.update(other)
        return self

    def __iand__(self, other: Set) -> 'DataStructureSet':
        """Return self&=other.

        Should perform the intersection on the underlying data structure.
        """
        self.intersection_update(other)
        return self

    def __ixor__(self, other: Set) -> 'DataStructureSet':
        """Return self^=other.

        Should perform the XOR operation on the underlying data structure.
        """
        self.symmetric_difference_update(other)
        return self

    def isdisjoint(self, other: set) -> bool:
        """Return True if two sets have a null intersection."""
        return self._underlying_set.isdisjoint(other)

    def clear(self) -> None:
        """Remove all elements from this set."""
        self.__iand__(set())

    def pop(self) -> Any:
        """Remove and return an arbitrary set element.

        Raises KeyError if the set is empty.
        """
        item = self._underlying_set.pop()
        self.__isub__({item})
        return item

    def copy(self) -> set:
        """Return a shallow copy of a set."""
        return self._underlying_set

    def difference(self, other: Iterable) -> set:
        """Return the difference of two or more sets as a new set.

        (i.e. all elements that are in this set but not the others.)
        """
        return self._underlying_set.difference(other)

    def discard(self, other: Any) -> None:
        """Remove an element from a set if it is a member.

        If the element is not a member, do nothing.
        """
        self.__isub__({other})

    def intersection(self, other: Set) -> set:
        """Return the intersection of two sets as a new set.

        (i.e. all elements that are in both sets.)
        """
        return self._underlying_set.intersection(other)

    def issubset(self, other: Set) -> bool:
        """Report whether another set contains this set."""
        return self <= other

    def issuperset(self, other: Set) -> bool:
        """Report whether this set contains another set."""
        return self >= other

    def add(self, other: Any) -> None:
        """Add an element to a set.

        This has no effect if the element is already present.
        """
        self.__ior__({other})

    def remove(self, other: Any) -> None:
        """Remove an element from a set; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        if other not in self:
            raise KeyError(f"{other}")
        self.__isub__({other})

    def symmetric_difference(self, other: Set) -> set:
        """Return the symmetric difference of two sets as a new set."""
        return self._underlying_set.symmetric_difference(other)

    def union(self, other: Set) -> set:
        """Return the union of sets as a new set."""
        return self._underlying_set.union(other)
