"""Utility resources for the ontology module."""

from abc import ABC, abstractmethod
import functools
import importlib
import os
import pkgutil
from typing import Any, Dict,Iterable, Iterator, MutableSet, Set, Tuple

from osp.core.ontology.entity import OntologyEntity


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


"""Define a `compatible_classes` function that lists the Python classes that
can be spawned for a particular RDF.type and type of node identifier.

This function used by `osp.core.session.Session.from_identifier` to
determine which Python class should be spawned for a given IRI or BNode.

Read the docstrings of the functions defined in this section for more details.
"""
# ↓ --------------- ↓


@functools.lru_cache(maxsize=None)
def _compute_mappings() -> Tuple[Dict[Any, Any], Dict[Any, Any]]:
    """Maps RDF types and node identifier types to Python classes.

    The classes defined in OSP-core that are meant to represent ontology
    entities (all subclasses of `OntologyEntity`), have two attributes,
    `rdf_type` and `rdf_identifier` that determine the combination of RDF
    types (e.g. owl:Class) and node identifier types (e.g. URIRef, BNode) that
    the class is meant to represent.

    This function imports the `osp.core.ontology` module and all of its
    submodules recursively, as all subclasses of `OntologyEntity` are
    expected to be stored there.

    After that, it generates two mappings, `mapping_rdf_to_python_class` and
    `mapping_identifier_to_python_class`, that map each rdf type and node
    identifier type to compatible Python classes.

    Using such mappings, other functions can find out the compatible classes
    for a specific pair of RDF type and node identifier type.

    This function is cached, as it is called by `compatible_classes`
    repeatedly, but the computation is only needed once. In fact, this code
    could be defined outside of a function, but it has been incorporated
    into a function because of the need to evaluate it lazily (to avoid
    circular imports).

    Returns:
        A tuple `mapping_rdf_to_python_class,
        mapping_identifier_to_python_class` containing the aforementioned
        mappings.
    """
    # First, import the ontology module and all of its submodules recursively.
    self = __import__(__name__)
    package_paths = [
        os.path.abspath(
            os.path.join(path, 'core/ontology')
        )
        for path in self.__path__
    ]
    package_prefix = f'{self.__name__}.core.ontology.'

    def import_modules_recursively(paths, prefix):
        for module_info in pkgutil.iter_modules(
                paths,
                prefix
        ):
            module = importlib.import_module(module_info.name)
            if module_info.ispkg:
                import_modules_recursively(module.__path__,
                                           f'{module_info.name}.')

    import_modules_recursively(package_paths, package_prefix)

    # Then compute the mappings, remember that the python class to instantiate
    # for a given ontology entity depends on two things:
    # - The RDF.type(s) of the identifier.
    # - The RDF node type of the identifier (URIRef, Node or Literal)

    mapping_rdf_to_python_class = dict()
    mapping_identifier_to_python_class = dict()

    def recursive_iterator(class_):
        for sub_class in class_.__subclasses__():
            yield from recursive_iterator(sub_class)
            yield sub_class

    for subclass in recursive_iterator(OntologyEntity):
        rdf_types = subclass.rdf_type \
            if isinstance(subclass.rdf_type, set) else {subclass.rdf_type}
        for rdf_type in rdf_types:
            mapping_rdf_to_python_class[rdf_type] = \
                mapping_rdf_to_python_class.get(rdf_type, set()) | {subclass}
        rdf_identifiers = subclass.rdf_identifier \
            if isinstance(subclass.rdf_identifier, set) \
            else {subclass.rdf_identifier}
        for rdf_identifier in rdf_identifiers:
            mapping_identifier_to_python_class[rdf_identifier] = \
                mapping_identifier_to_python_class.get(rdf_identifier, set()) \
                | {subclass}
    return mapping_rdf_to_python_class, mapping_identifier_to_python_class


def compatible_classes(type_, identifier):
    """Given a pair of a RDF type and an identifier get a Python class.

    Given a pair of a RDF type and an identifier, the compatible Python
    classes are computed. In fact, for the latter only the type of
    identifier matters.
    """
    mapping_rdf_to_python_class, mapping_identifier_to_python_class = \
        _compute_mappings()
    # Remember that the call above is cached (see `_compute_mappings`).

    from_type = mapping_rdf_to_python_class.get(type_, set())
    from_identifier = functools.reduce(
        lambda x, y: x | y,
        (value
         for key, value in mapping_identifier_to_python_class.items()
         if isinstance(identifier, key)),
        set()
    )
    return from_type & from_identifier

# ↑ --------------- ↑
