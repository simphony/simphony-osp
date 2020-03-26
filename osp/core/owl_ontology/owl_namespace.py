# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import rdflib
import logging

from osp.core.owl_ontology.owl_oclass import OntologyClass
from osp.core.owl_ontology.owl_object_property import OntologyObjectProperty
from osp.core.owl_ontology.owl_data_property import OntologyDataProperty

logger = logging.getLogger(__name__)


class OntologyNamespace():
    def __init__(self, name, graph, iri):
        self._name = name
        self._graph = graph
        self._default_rel = None
        self._iri = iri
        # TODO use graph IRI, different graph for each namespace

    def __str__(self):
        return "%s: %s" % (self.name, self.iri)

    def __repr__(self):
        return "<%s: %s>" % (self.name, self.iri)

    @property
    def name(self):
        """Get the name of the namespace"""
        return self._name

    @property
    def default_rel(self):
        """Get the default relationship of the namespace"""
        return self._default_rel

    @property
    def iri(self):
        """Get the IRI of the namespace"""
        return self._iri

    @property
    def graph(self):
        """Get the RDF graph of the namespace"""
        return self._graph

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

    def __getitem__(self, name):
        """Get an ontology entity from the registry by name.

        :param name: The name of the ontology entity
        :type name: str
        :return: The ontology entity
        :rtype: OntologyEntity
        """
        return self._get(name)

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
        for s, p, o in self.graph.triples((iri, rdflib.RDF.type, None)):
            if o == rdflib.OWL.DataProperty:
                return OntologyDataProperty(self, name)
            if o == rdflib.OWL.ObjectProperty:
                return OntologyObjectProperty(self, name)
            if o == rdflib.OWL.Class:
                return OntologyClass(self, name)

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
