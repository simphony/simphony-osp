import uuid
import rdflib
from abc import ABC, abstractmethod
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.oclass import OntologyClass
from osp.core.utils import iri_from_uid, uid_from_iri
from osp.core.namespaces import from_iri, _namespace_registry


class NeighborDict(ABC):
    """A dictionary that notifies the session if
    any update occurs. Used to map uids to ontology classes
    for each relationship.
    """

    def __init__(self, dictionary, cuds_object, key_check, value_check):
        self.cuds_object = cuds_object
        self.key_check = key_check
        self.value_check = value_check

        invalid_keys = [k for k in dictionary.keys()
                        if not self.key_check(k)]
        if invalid_keys:
            raise ValueError("Invalid keys %s" % invalid_keys)
        invalid_values = [v for v in dictionary.values()
                          if not self.value_check(v)]

        if invalid_values:
            raise ValueError("Invalid values %s" % invalid_values)

    def __iter__(self):
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return self._iter()
        # TODO maybe it's more secure to notify read after each iteration step?

    def __getitem__(self, key):
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return self._getitem(key)

    def __setitem__(self, key, value):
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
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        r = self._delitem(key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_update(self.cuds_object)
        return r

    def __eq__(self, E):
        return dict(self.items()) == E

    def update(self, E):
        for key, value in E.items():
            self[key] = value

    def items(self):
        for k in self:
            yield k, self[k]

    def keys(self):
        return {k for k in self}

    def values(self):
        for k in self:
            yield self[k]

    @property
    def graph(self):
        return self.cuds_object._rel_graph

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
    def __init__(self, cuds_object):
        super().__init__(
            {}, cuds_object,
            key_check=lambda k: isinstance(k, OntologyRelationship),
            value_check=lambda v: isinstance(v, NeighborDictTarget)
        )

    def _delitem(self, rel):
        self.graph.remove((self.cuds_object.iri, rel.iri, None))

    def _setitem(self, rel, target_dict):
        target_dict._init()

    def _getitem(self, rel):
        return NeighborDictTarget({}, cuds_object=self.cuds_object, rel=rel)

    def __bool__(self):
        try:
            next(self.graph.triples((self.cuds_object.iri, None, None)))
            return True
        except StopIteration:
            return False

    def _iter(self):
        predicates = set([
            p for _, p, _ in self.graph.triples((self.cuds_object.iri,
                                                 None, None))
        ])
        for p in predicates:
            if (p, rdflib.RDF.type, rdflib.OWL.ObjectProperty) \
                    in _namespace_registry._graph:
                yield from_iri(p)


class NeighborDictTarget(NeighborDict):
    def __init__(self, dictionary, cuds_object, rel):
        self.rel = rel
        for uid, oclass in dictionary.items():
            cuds_object._check_valid_add(oclass, rel)
        super().__init__(
            dictionary, cuds_object,
            key_check=lambda k: isinstance(k, uuid.UUID),
            value_check=lambda v: isinstance(v, OntologyClass)
        )
        self.dictionary = dictionary

    def _init(self):  # move __init__ arguments here
        self.graph.remove((self.cuds_object.iri, self.rel.iri, None))
        self.update(self.dictionary)
        del self.dictionary

    def _delitem(self, uid):
        iri = iri_from_uid(uid)
        self.graph.remove((self.cuds_object.iri, self.rel.iri, iri))

    def _setitem(self, uid, oclass):
        iri = iri_from_uid(uid)
        self.cuds_object._check_valid_add(oclass, self.rel)
        self.graph.add((self.cuds_object.iri, self.rel.iri, iri))
        self.graph.set((iri, rdflib.RDF.type, oclass.iri))

    def _getitem(self, uid):
        iri = iri_from_uid(uid)
        if (self.cuds_object.iri, self.rel.iri, iri) in self.graph:
            return from_iri(self.graph.value(iri, rdflib.RDF.type))
        raise KeyError(uid)

    def _iter(self):
        for s, p, o in self.graph.triples((self.cuds_object.iri,
                                           self.rel.iri, None)):
            yield uid_from_iri(o)
