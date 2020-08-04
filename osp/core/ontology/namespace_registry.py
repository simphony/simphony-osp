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
        return other.lower() in self._namespaces.keys()

    def get(self, name, fallback=None):
        """Get the namespace by name, return given fallback value if not found.

        Args:
            name (str): Name of the namespace
            fallback (Any, optional): Fallback value. Defaults to None.

        Returns:
            Any: OntologyNamespace or fallback value
        """
        try:
            return self._get(name)
        except KeyError:
            return fallback

    def _get(self, name):
        """Get the namespace by name.

        Args:
            name (str): The name of the namespace.

        Raises:
            KeyError: Namespace not installed.

        Returns:
            OntologyNamespace: The namespace with the given name.
        """
        name = name.lower()
        if name in self._namespaces:
            return OntologyNamespace(name=name,
                                     namespace_registry=self,
                                     iri=self._namespaces[name])
        raise KeyError("Namespace %s not installed." % name)

    def update_namespaces(self, modules=[]):
        """Update the namespaces of the namespace registry from the
        namespaces of the graph."""
        self._namespaces = dict()
        for name, iri in self._graph.namespace_manager.namespaces():
            self._namespaces[name.lower()] = iri
        for module in modules:
            for namespace in self:
                setattr(module, namespace.get_name().upper(), namespace)
                setattr(module, namespace.get_name().lower(), namespace)

    def from_iri(self, iri):
        """Get an entity from IRI.

        Args:
            iri (URIRef): The IRI of the entity.

        Returns:
            OntologyEntity: The OntologyEntity.
        """
        for name, ns_iri in self._graph.namespace_manager.namespaces():
            if str(iri).startswith(str(ns_iri)):
                ns = OntologyNamespace(
                    name=name,
                    namespace_registry=self,
                    iri=ns_iri
                )
                if ns._reference_by_label:
                    return ns._get(None, _force_by_iri=iri[len(ns_iri):])
                else:
                    return ns._get(iri[len(ns_iri):])

    def clear(self):
        """Clear the loaded Graph and load cuba only.

        Returns:
            [type]: [description]
        """
        self._graph = rdflib.Graph()
        self._load_cuba()
        return self._graph

    def store(self, path):
        """Store the current graph to the given directory,

        Args:
            path (Path): Directory to store current graph in.
        """
        path_graph = os.path.join(path, "graph.xml")
        path_ns = os.path.join(path, "namespaces.txt")
        self._graph.serialize(destination=path_graph, format="xml")
        with open(path_ns, "w") as f:
            for name, iri in self._graph.namespace_manager.namespaces():
                print("%s\t%s" % (name, iri), file=f)

    def load(self, path):
        """Load the installed graph from at the given path.

        Args:
            path (Path): path to directory where the ontology has been
                installed.
        """
        if os.path.exists(os.path.join(path, "yml")):
            from osp.core.ontology.installation import pico_migrate
            pico_migrate(self, path)
        path_graph = os.path.join(path, "graph.xml")
        path_ns = os.path.join(path, "namespaces.txt")
        if os.path.exists(path_graph):
            self._graph.parse(path_graph, format="xml")
            if os.path.exists(path_ns):
                with open(path_ns, "r") as f:
                    for line in f:
                        name, iri = line.strip("\n").split("\t")
                        self._graph.bind(name, rdflib.URIRef(iri))
                self.update_namespaces()
        else:
            self._load_cuba()

    def _load_cuba(self):
        """Load the cuba namespace"""
        path_cuba = os.path.join(os.path.dirname(__file__), "docs", "cuba.ttl")
        self._graph.parse(path_cuba, format="ttl")
        self._graph.bind("cuba",
                         rdflib.URIRef("http://www.osp-core.com/cuba#"))
        self.update_namespaces()
