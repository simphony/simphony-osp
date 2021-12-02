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

    @abstractmethod
    def __iter__(self) -> Iterator[Any]:
        """Implement iter(self).

        Returns the associated values from the connected data structure.

        The values provided MUST NOT be repeated, as instances of this class
        are expected to behave like sets. Remember that the definition of
        membership for sets in Python is `any(x is e or x == e for e in y)`,
        see https://docs.python.org/3/reference/expressions.html
        #membership-test-details. Therefore, if you implemented this method
        correctly, letting `y` be this object, then
        `sum(sum(x is e or x == e for e in y) for x in y)` should evaluate to
        `len(list(y))`.


        Returns:
            An iterator providing the values from the connected data
            structure.
        """
        pass

    @abstractmethod
    def __contains__(self, item: Any) -> bool:
        """Return y in x.

        Check if the item is in the connected data structure.

        You can also choose to just call `return super().__contains__(item)` to
        use this naive implementation instead of implementing something
        yourself.
        """
        for x in self:
            if x is item or x == item:
                return True
        return False

    @abstractmethod
    def update(self, other: Iterable) -> None:
        """Update a set with the union of itself and others.

        Updates the connected data structure with the result of performing a
        set union operation with another iterable.
        """
        pass

    @abstractmethod
    def intersection_update(self, other: Iterable) -> None:
        """Update a set with the intersection of itself and another.

        Updates the connected data structure performing a set intersection
        operation with another iterable.
        """

    @abstractmethod
    def difference_update(self, other: Iterable) -> None:
        """Remove all elements of another set from this set.

        Updates the connected data structure performing a set difference
        operation with another iterable.
        """
        pass

    @abstractmethod
    def symmetric_difference_update(self, other: Iterable) -> None:
        """Update a set with the symmetric difference of itself and another.

        Updates the connected data structure performing an XOR set operation
        with another iterable.
        """
        pass

    def __repr__(self) -> str:
        """Return repr(self)."""
        return set(self).__repr__()

    def __str__(self) -> str:
        """Return str(self)."""
        return set(self).__str__()

    def __format__(self, format_spec: str) -> str:
        """Default object formatter."""
        return set(self).__format__(format_spec)

    def __len__(self) -> int:
        """Return len(self)."""
        return sum(1 for _ in self)

    def __le__(self, other: Set) -> bool:
        """Return self<=other."""
        return set(self).__le__(other)

    def __lt__(self, other: Set) -> bool:
        """Return self<other."""
        return set(self).__lt__(other)

    def __eq__(self, other: Set) -> bool:
        """Return self==other."""
        return set(self).__eq__(other)

    def __ne__(self, other: Set) -> bool:
        """Return self!=other."""
        return set(self).__ne__(other)

    def __gt__(self, other: Set) -> bool:
        """Return self>other."""
        return set(self).__gt__(other)

    def __ge__(self, other: Set) -> bool:
        """Return self>=other."""
        return set(self).__ge__(other)

    def __and__(self, other: Set) -> set:
        """Return self&other."""
        return set(self).__and__(other)

    def __radd__(self, other: Set) -> set:
        """Return other&self."""
        return other & set(self)

    def __ror__(self, other: Set) -> set:
        """Return other|self."""
        return other | set(self)

    def __rsub__(self, other: set) -> set:
        """Return value-self."""
        return other - set(self)

    def __rxor__(self, other: set) -> set:
        """Return value^self."""
        return other ^ set(self)

    def __or__(self, other: Set) -> set:
        """Return self|other."""
        return set(self).__or__(other)

    def __sub__(self, other: Set) -> set:
        """Return self-other."""
        return set(self).__sub__(other)

    def __xor__(self, other: Set) -> set:
        """Return self^other."""
        return set(self).__xor__(other)

    def __iadd__(self, other: Any) -> 'DataStructureSet':
        """Return self+=other (equivalent to self|=other)."""
        if isinstance(other, (Set, MutableSet)):
            # Apparently instances of MutableSet are not instances of Set.
            self.update(other)
        else:
            self.update({other})
        return self

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
        return set(self).isdisjoint(other)

    def clear(self) -> None:
        """Remove all elements from this set."""
        self.intersection_update(set())

    def pop(self) -> Any:
        """Remove and return an arbitrary set element.

        Raises KeyError if the set is empty.
        """
        try:
            item = next(iter(self))
        except StopIteration:
            return set().pop()  # Underlying data structure is empty.
        self.difference_update({item})
        return item

    def copy(self) -> set:
        """Return a shallow copy of a set."""
        return set(self)

    def difference(self, other: Iterable) -> set:
        """Return the difference of two or more sets as a new set.

        (i.e. all elements that are in this set but not the others.)
        """
        return set(self).difference(other)

    def discard(self, other: Any) -> None:
        """Remove an element from a set if it is a member.

        If the element is not a member, do nothing.
        """
        self.difference_update({other})

    def intersection(self, other: Set) -> set:
        """Return the intersection of two sets as a new set.

        (i.e. all elements that are in both sets.)
        """
        return set(self).intersection(other)

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
        self.update({other})

    def remove(self, other: Any) -> None:
        """Remove an element from a set; it must be a member.

        If the element is not a member, raise a KeyError.
        """
        if other not in self:
            raise KeyError(f"{other}")
        self.difference_update({other})

    def symmetric_difference(self, other: Set) -> set:
        """Return the symmetric difference of two sets as a new set."""
        return set(self).symmetric_difference(other)

    def union(self, other: Set) -> set:
        """Return the union of sets as a new set."""
        return set(self).union(other)
