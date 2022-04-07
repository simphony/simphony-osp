"""A dictionary interface for the related object of a CUDS."""

import uuid
from abc import ABC, abstractmethod

import rdflib

from osp.core.namespaces import from_iri
from osp.core.ontology.namespace_registry import namespace_registry
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.utils.general import iri_from_uid, uid_from_iri


class NeighborDict(ABC):
    """A dictionary that notifies the session on changes.

    Used to map uids to ontology classes
    for each relationship.
    """

    def __init__(self, cuds_object, key_check, value_check):
        """Initialize the dictionary."""
        self.cuds_object = cuds_object
        self.key_check = key_check
        self.value_check = value_check

    def __iter__(self):
        """Notify on iteration."""
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return self._iter()
        # TODO maybe it's more secure to notify read after each iteration step?

    def __contains__(self, item):
        """Notify on containment check."""
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return self._contains(item)

    def __getitem__(self, key):
        """Notify on read."""
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return self._getitem(key)

    def __setitem__(self, key, value):
        """Notify on update."""
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if not self.value_check(value):
            raise ValueError("Invalid value %s" % value)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        r = self._setitem(key, value)
        if self.cuds_object.session:
            self.cuds_object.session._notify_update(self.cuds_object)
        return r

    def __delitem__(self, key):
        """Notify on deletion."""
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        r = self._delitem(key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_update(self.cuds_object)
        return r

    def __eq__(self, E):
        """Check equality."""
        return dict(self.items()) == E

    def update(self, E):
        """Update."""
        for key, value in E.items():
            self[key] = value

    def items(self):
        """Get the items."""
        for k in self:
            yield k, self[k]

    def keys(self):
        """Get the set of keys."""
        return {k for k in self}

    def values(self):
        """Get the values."""
        for k in self:
            yield self[k]

    @property
    def graph(self):
        """Get the graph this dictionary acts on."""
        return self.cuds_object._graph

    @abstractmethod
    def _delitem(self, key):
        pass

    @abstractmethod
    def _setitem(self, key, value):
        pass

    @abstractmethod
    def _getitem(self, key):
        pass

    @abstractmethod
    def _iter(self):
        pass


class NeighborDictRel(NeighborDict):
    """Maps a relationship to CUDS objects related with that relationship.

    Value is of type NeighborDictTarget.
    Acts on the graph of the CUDS object.
    """

    def __init__(self, cuds_object):
        """Initialize the dictionary."""
        super().__init__(
            cuds_object,
            key_check=lambda k: isinstance(k, OntologyRelationship),
            value_check=lambda v: isinstance(v, dict),
        )

    def _delitem(self, rel):
        """Delete an item."""
        self.graph.remove((self.cuds_object.iri, rel.iri, None))

    def _setitem(self, rel, target_dict):
        """Set an element."""
        x = NeighborDictTarget(cuds_object=self.cuds_object, rel=rel)
        x._init(target_dict)

    def _getitem(self, rel):
        """Get an element of the dictionary."""
        return NeighborDictTarget(cuds_object=self.cuds_object, rel=rel)

    def __bool__(self):
        """Check if there are elements in the dictionary."""
        for s, p, o in self.graph.triples((self.cuds_object.iri, None, None)):
            if (
                p,
                rdflib.RDF.type,
                rdflib.OWL.ObjectProperty,
            ) in namespace_registry._graph:
                return True
        return False

    def _contains(self, item: OntologyRelationship):
        """Checks if an item belongs to the dictionary."""
        return (self.cuds_object.iri, item.iri, None) in self.graph

    def _iter(self):
        """Iterate over the dictionary."""
        predicates = set(self.graph.predicates(self.cuds_object.iri, None))
        # Using set(..) instead of the iterator directly makes the code 2x
        #  faster.
        for p in predicates:
            try:
                obj = from_iri(p)
                if isinstance(obj, OntologyRelationship):
                    yield obj
            except KeyError:
                pass


class NeighborDictTarget(NeighborDict):
    """Maps related CUDS' object UUID to its ontology class.

    Acts on the graph of the CUDS object.
    """

    def __init__(self, cuds_object, rel):
        """Initialize the dictionary."""
        self.rel = rel
        super().__init__(
            cuds_object,
            key_check=lambda k: isinstance(k, (uuid.UUID, rdflib.URIRef)),
            value_check=lambda v: (
                isinstance(v, list)
                and all(isinstance(x, OntologyClass) for x in v)
            ),
        )

    def _init(self, dictionary):
        """Initialize the dictionary. Add the given elements."""
        self.graph.remove((self.cuds_object.iri, self.rel.iri, None))
        self.update(dictionary)

    def _delitem(self, uid):
        """Delete an item from the dictionary."""
        iri = iri_from_uid(uid)
        self.graph.remove((self.cuds_object.iri, self.rel.iri, iri))

    def _setitem(self, uid, oclasses):
        """Add the UUID of a related CUDS object to the dictionary.

        Also add the oclass of the related CUDS object.
        """
        iri = iri_from_uid(uid)
        self.cuds_object._check_valid_add(oclasses, self.rel)
        self.graph.add((self.cuds_object.iri, self.rel.iri, iri))
        for oclass in oclasses:
            self.graph.add((iri, rdflib.RDF.type, oclass.iri))

    def _getitem(self, uid):
        """Get the oclass of the object with the given UUID."""
        iri = iri_from_uid(uid)
        if (self.cuds_object.iri, self.rel.iri, iri) in self.graph:
            result = list()
            for _, _, o in self.graph.triples((iri, rdflib.RDF.type, None)):
                result.append(from_iri(o))
            return result
        raise KeyError(uid)

    def _iter(self):
        """Iterate over the over the UUIDs of the related CUDS objects.

        Yields:
            UUID: The UUIDs of the CUDS object related with self.rel.
        """
        for o in self.graph.objects(self.cuds_object.iri, self.rel.iri):
            yield uid_from_iri(o)

    def _contains(self, item):
        """Checks if an item belongs to the dictionary."""
        return (
            self.cuds_object.iri,
            self.rel.iri,
            iri_from_uid(item),
        ) in self.graph
