# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import rdflib
import logging

from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.object_property import OntologyObjectProperty
from osp.core.ontology.data_property import OntologyDataProperty

logger = logging.getLogger(__name__)


class OntologyNamespace():
    def __init__(self, name, namespace_registry, iri):
        self._name = name
        self._namespace_registry = namespace_registry
        self._iri = rdflib.URIRef(str(iri))
        self._label_cache = dict()
        self._default_rel = -1

    def __str__(self):
        return "%s (%s)" % (self.name, self.iri)

    def __repr__(self):
        return "<%s: %s>" % (self.name, self.iri)

    @property
    def name(self):
        """Get the name of the namespace"""
        return self._name

    @property
    def _graph(self):
        return self._namespace_registry._graph

    @property
    def default_rel(self):
        """Get the default relationship of the namespace"""
        if self._default_rel == -1:
            from osp.core.ontology.parser import DEFAULT_REL_IRI
            for s, p, o in self._graph.triples((self._iri,
                                                DEFAULT_REL_IRI,
                                                None)):
                self._default_rel = self._namespace_registry.from_iri(o)
        return self._default_rel

    @property
    def iri(self):
        """Get the IRI of the namespace"""
        return self._iri

    def __getattr__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        try:
            return self._get(name)
        except KeyError as e:
            raise AttributeError(str(e)) from e

    def __getitem__(self, label):
        """Get an ontology entity from the registry by name.

        :param label: The label of the ontology entity
        :type label: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        if isinstance(label, str):
            label = rdflib.term.Literal(label, lang="en")
        if isinstance(label, tuple):
            label = rdflib.term.Literal(label[0], lang=label[1])
        if label in self._label_cache:
            return self._label_cache[label]
        for s, p, o in self._graph.triples((None, rdflib.RDFS.label, label)):
            if str(s).startswith(self._iri):  # TODO more efficient
                name = str(s)[len(self._iri):]
                self._label_cache[label] = self.get(name)
                return self._label_cache[label]
        raise KeyError("No element with label %s in namespace %s"
                       % (label, self))

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def get(self, name, fallback=None):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :param default: The value to return if it doesn't exist
        :type default: Any
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        try:
            return self._get(name)
        except KeyError:
            return fallback

    def _get(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        iri = rdflib.URIRef(str(self.iri) + name)
        for s, p, o in self._graph.triples((iri, rdflib.RDF.type, None)):
            if o == rdflib.OWL.DataProperty:
                return OntologyDataProperty(self, name)
            if o == rdflib.OWL.ObjectProperty:
                return OntologyObjectProperty(self, name)
            if o == rdflib.OWL.Class:
                return OntologyClass(self, name)
        raise KeyError("Unknown entity %s in namespace %s" % (name, self))

        # if (  # TODO case insensitivity
        #     any(x.islower() for x in name)
        #     and any(x.isupper() for x in name)
        # ):
        #     given = name
        #     name = name[0]
        #     for x in given[1:]:
        #         if x.isupper():
        #             name += "_"
        #         name += x
        # try:
        #     return self._entities[name.lower()]
        # except KeyError as e:
        #     raise KeyError("%s not defined in namespace %s"
        #                    % (name, self.name)) from e

    # def __iter__(self):  TODO
    #     """Iterate over the ontology entities in the namespace.

    #     :return: An iterator over the entities.
    #     :rtype: Iterator[OntologyEntity]
    #     """
    #     return iter(self._entities.values())

    # def __contains__(self, obj):  TODO
    #     if isinstance(obj, str):
    #         return obj.lower() in self._entities.keys()
    #     return obj in self._entities.values()

    # def _add_entity(self, entity):  TODO for YAML
    #     """Add an entity to the namespace.

    #     :param entity: The entity to add.
    #     :type entity: OntologyEntity
    #     """
    #     from osp.core.ontology.entity import OntologyEntity
    #     assert isinstance(entity, OntologyEntity)
    #     self._entities[entity.name.lower()] = entity

    @property
    def author(self):
        """Get the author of the namespace"""
        logger.warning("The use of OntologyNamespace.author is deprecated.")
        return self._author

    @property
    def version(self):
        """Get the version of the namespace"""
        logger.warning("The use of OntologyNamespace.version is deprecated.")
        return self._version
