# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import logging
import rdflib
from osp.core.owl_ontology.owl_namespace import OntologyNamespace

logger = logging.getLogger(__name__)


class NamespaceRegistry():
    def __init__(self):
        self._graph = rdflib.Graph()
        self._namespaces = dict()

    def __iter__(self):
        """Iterate over the installed namespace.

        :return: An iterator over the namespaces.
        :rtype: Iterator[OntologyNamespace]
        """
        for namespace_name in self._namespaces:
            yield self._get(namespace_name)

    def __getattr__(self, name):
        try:
            return self._get(name)
        except KeyError as e:
            raise AttributeError(str(e)) from e

    def __getitem__(self, name):
        return self._get(name)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __contains__(self, other):
        if isinstance(other, str):
            return other.lower() in self._namespaces.keys()
        return other in self._namespaces.values()

    def get(self, name, fallback=None):
        try:
            return self._get(name)
        except KeyError:
            return fallback

    def _get(self, name):
        if name in self._namespaces:
            return OntologyNamespace(name=name,
                                     namespace_registry=self,
                                     iri=self._namespaces[name])
        raise KeyError("Namespace %s not installed." % name)

    def update_namespaces(self):
        for name, iri in self._graph.namespace_manager.namespaces():
            self._namespaces[name] = iri

    def from_iri(self, iri):
        for name, ns_iri in self._graph.namespace_manager.namespaces():
            if str(iri).startswith(str(ns_iri)):
                return OntologyNamespace(
                    name=name,
                    namespace_registry=self,
                    iri=ns_iri
                ).get(iri[len(ns_iri):])
