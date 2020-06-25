# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import logging
import rdflib
from osp.core.ontology.namespace import OntologyNamespace

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

    def clear(self):
        self._graph = rdflib.Graph()
        return self._graph

    def store(self, path):
        path_graph = os.path.join(path, "graph.ttl")
        path_ns = os.path.join(path, "namespaces.txt")
        self._graph.serialize(destination=path_graph, format="turtle")
        with open(path_ns, "w") as f:
            for name, iri in self._graph.namespace_manager.namespaces():
                print("%s\t%s" % (name, iri), file=f)

    def load(self, path):
        path_graph = os.path.join(path, "graph.ttl")
        path_ns = os.path.join(path, "namespaces.txt")
        path_cuba = os.path.join(os.path.dirname(__file__), "docs", "cuba.ttl")
        if os.path.exists(path_graph):
            self._graph.parse(path_graph, format="ttl")
            if os.path.exists(path_ns):
                with open(path_ns, "r") as f:
                    for line in f:
                        name, iri = line.strip("\n").split("\t")
                        self._graph.bind(name, rdflib.URIRef(iri))
                self.update_namespaces()
        else:
            self._graph.parse(path_cuba, format="ttl")
            self._graph.bind("CUBA",
                             rdflib.URIRef("http://www.osp-core.com/CUBA#"))
            self.update_namespaces()
