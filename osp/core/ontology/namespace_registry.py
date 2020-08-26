import os
import logging
import rdflib
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.attribute import OntologyAttribute

logger = logging.getLogger(__name__)


class NamespaceRegistry():
    def __init__(self):
        # Do not instantiate you own namespace registry.
        # Instead you can use osp.core.namespaces._namespace_registry.
        self._graph = rdflib.Graph()
        self._namespaces = dict()

    def __iter__(self):
        """Iterate over the installed namespace.

        :return: An iterator over the namespaces.
        :rtype: Iterator[OntologyNamespace]
        """
        for namespace_name in self._namespaces:
            if namespace_name:
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
        """Update the namespaces of the namespace registry.

        Use the namespaces of the graph for that.
        """
        self._namespaces = dict()
        for name, iri in self._graph.namespace_manager.namespaces():
            self._namespaces[name.lower()] = iri
        for module in modules:
            for namespace in self:
                setattr(module, namespace.get_name().upper(), namespace)
                setattr(module, namespace.get_name().lower(), namespace)

    def namespace_from_iri(self, ns_iri):
        ns_name, ns_iri = self._get_namespace_name_and_iri(ns_iri)
        if ns_name in self._namespaces:
            return self._get(ns_name)
        return OntologyNamespace(name=ns_name,
                                 namespace_registry=self,
                                 iri=ns_iri)

    def from_iri(self, iri, raise_error=True,
                 allow_types=frozenset({rdflib.OWL.DatatypeProperty,
                                        rdflib.OWL.ObjectProperty,
                                        rdflib.OWL.Class}),
                 _name=None):
        """Get an entity from IRI.

        Args:
            iri (URIRef): The IRI of the entity.
            raise_error(bool): Whether an error should be raised if IRI invalid
            allow_types(bool): The owl types allowed to be returned.

        Returns:
            OntologyEntity: The OntologyEntity.
        """
        iri = rdflib.URIRef(iri)
        ns_name, ns_iri = self._get_namespace_name_and_iri(iri)
        if _name is None:
            _name = self._get_entity_name(iri, ns_iri)
        iri_suffix = iri[len(ns_iri):]

        kwargs = {"namespace_registry": self,
                  "namespace_iri": ns_iri,
                  "name": _name,
                  "iri_suffix": iri_suffix}
        for s, p, o in self._graph.triples((iri, rdflib.RDF.type, None)):
            if o not in allow_types:
                continue
            if o == rdflib.OWL.DatatypeProperty:
                # assert (iri, rdflib.RDF.type, rdflib.OWL.FunctionalProperty)
                #     in self._graph  # TODO allow non functional attributes
                return OntologyAttribute(**kwargs)
            if o == rdflib.OWL.ObjectProperty:
                return OntologyRelationship(**kwargs)
            if o == rdflib.OWL.Class:
                return OntologyClass(**kwargs)
        if raise_error:
            raise KeyError(f"IRI {iri} not found in graph or not of any "
                           f"type in the set {allow_types}")

    def _get_namespace_name_and_iri(self, iri):
        """Get the namespace name and namespace iri for an entity iri.

        Args:
            iri (URIRef): The IRI for an entity or namespace

        Returns:
            Tuple[str, URIRef]: The name of the namespace and the IRI
        """
        for _name, _ns_iri in self._graph.namespace_manager.namespaces():
            if str(iri).startswith(str(_ns_iri)) and _name:
                return _name, _ns_iri

        if "#" in str(iri):
            ns_iri = str(iri).split("#")[0] + "#"
        else:
            ns_iri = "/".join(str(iri).split("/")[:-1]) + "/"
        return str(ns_iri), rdflib.URIRef(ns_iri)

    def _get_reference_by_label(self, ns_iri):
        """Check how entities in namespace should be referenced in code.

        Check for given namespace iri whether the entities in this namespace
        should be referenced by label when accessing them through python
        code

        Args:
            ns_iri (URIRef): The IRI of the namespace

        Returns:
            bool: Whether entities should be referenced by label
        """
        return (
            ns_iri, rdflib_cuba._reference_by_label, rdflib.Literal(True)
        ) in self._graph

    def _get_entity_name(self, entity_iri, ns_iri):
        """Get the name of the given entity.

        The name depends whether
        the namespace references the entities by label or iri suffix.

        Args:
            entity_iri (URIRef): The IRI of the entity
            ns_iri (URIRef): The IRI of the namespace

        Returns:
            str: The name of the entity with the given IRI
        """
        if self._get_reference_by_label(ns_iri):
            return self._graph.value(entity_iri, rdflib.RDFS.label).toPython()
        return entity_iri[len(ns_iri):]

    def clear(self):
        """Clear the loaded Graph and load cuba only.

        Returns:
            [type]: [description]
        """
        self._graph = rdflib.Graph()
        self._load_cuba()
        return self._graph

    def store(self, path):
        """Store the current graph to the given directory.

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
        """Load the cuba namespace."""
        path_cuba = os.path.join(os.path.dirname(__file__), "docs", "cuba.ttl")
        self._graph.parse(path_cuba, format="ttl")
        self._graph.bind("cuba",
                         rdflib.URIRef("http://www.osp-core.com/cuba#"))
        self.update_namespaces()
