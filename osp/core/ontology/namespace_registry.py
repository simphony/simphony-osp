"""Stores all the loaded namespaces."""

import logging
import os
from functools import lru_cache
from typing import Iterable

import rdflib

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.ontology import Ontology
from osp.core.ontology.parser.parser import OntologyParser
from osp.core.ontology.relationship import OntologyRelationship

logger = logging.getLogger(__name__)


class NamespaceRegistry:
    """Stores all the loaded namespaces."""

    def __init__(self):
        """Initialize the namespace registry.

        Do NOT instantiate you own namespace registry. It is meant to be a
        singleton. Instead, you should use
        osp.core.ontology.namespace_registry.namespace_registry.
        """
        self._graph = rdflib.Graph()
        self._namespaces = dict()

    def __iter__(self):
        """Iterate over the installed namespaces.

        :return: An iterator over the namespaces.
        :rtype: Iterator[OntologyNamespace]
        """
        for namespace_name in self._namespaces:
            if namespace_name:
                yield self._get(namespace_name)

    def __getattr__(self, name):
        """Get a namespace object by name.

        Args:
            name (str): The name of a namespace.

        Returns:
            OntologyNamespace: The namespace object with the given name.
        """
        try:
            return self._get(name)
        except KeyError as e:
            raise AttributeError(str(e)) from e

    def __getitem__(self, name):
        """Get a namespace object by name.

        Args:
            name (str): The name of a namespace.

        Returns:
            OntologyNamespace: The namespace object with the given name.
        """
        return self._get(name)

    def __contains__(self, other):
        """Check if the given namespace name is loaded.

        Args:
            other (str): The name of a namespace.

        Returns:
            bool: Whether the given namespace is loaded in the namespace
                registry.
        """
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

    @lru_cache(maxsize=5000)
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
            return OntologyNamespace(
                name=name, namespace_registry=self, iri=self._namespaces[name]
            )
        raise KeyError("Namespace %s not installed." % name)

    def update_namespaces(
        self, modules: Iterable = tuple(), remove: Iterable = tuple()
    ):
        """Update the namespaces of the namespace registry.

        Only needed for Python 3.6.
        """
        for module in modules:
            for namespace in remove:
                delattr(module, namespace.get_name().lower())
            for namespace in self:
                setattr(module, namespace.get_name().upper(), namespace)
                setattr(module, namespace.get_name().lower(), namespace)

    def namespace_from_iri(self, ns_iri):
        """Get a namespace object from the IRI of the namespace.

        Args:
            ns_iri (rdflib.URIRef): The IRI of the namespace.

        Returns:
            OntologyNamespace: The namespace with the given IRI.
        """
        ns_name, ns_iri = self._get_namespace_name_and_iri(ns_iri)
        if ns_name in self._namespaces:
            return self._get(ns_name)
        return OntologyNamespace(
            name=ns_name, namespace_registry=self, iri=ns_iri
        )

    @lru_cache(maxsize=10000)
    def from_iri(
        self,
        iri,
        raise_error=True,
        allow_types=frozenset(
            {
                rdflib.OWL.DatatypeProperty,
                rdflib.OWL.ObjectProperty,
                rdflib.OWL.Class,
                rdflib.RDFS.Class,
            }
        ),
        _name=None,
    ):
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
        iri_suffix = iri[len(ns_iri) :]

        kwargs = {
            "namespace_registry": self,
            "namespace_iri": ns_iri,
            "name": _name,
            "iri_suffix": iri_suffix,
        }
        for s, p, o in self._graph.triples((iri, rdflib.RDF.type, None)):
            if o not in allow_types:
                continue
            if o == rdflib.OWL.DatatypeProperty:
                # assert (iri, rdflib.RDF.type, rdflib.OWL.FunctionalProperty)
                #     in self._graph  # TODO allow non functional attributes
                return OntologyAttribute(**kwargs)
            if o == rdflib.OWL.ObjectProperty:
                return OntologyRelationship(**kwargs)
            if o in (rdflib.OWL.Class, rdflib.RDFS.Class):
                return OntologyClass(**kwargs)
        if raise_error:
            raise KeyError(
                f"IRI {iri} not found in graph or not of any "
                f"type in the set {allow_types}"
            )

    def from_bnode(self, bnode, btype=None):
        """Return restriction, composition represented by given bnode.

        Args:
            bnode (BNode): A blank node in the triple store.
            btype (URIRef): The rdf.type of the blank node.
        """
        from osp.core.ontology.oclass_composition import get_composition
        from osp.core.ontology.oclass_restriction import get_restriction

        t = btype or self._graph.value(bnode, rdflib.RDF.type)

        if t == rdflib.OWL.Restriction:
            x = get_restriction(bnode, self)
            if x:
                return x
        elif t == rdflib.OWL.Class:
            x = get_composition(bnode, self)
            if x:
                return x
        raise KeyError(bnode)

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
            ns_iri,
            rdflib_cuba._reference_by_label,
            rdflib.Literal(True),
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
            namespace = self.namespace_from_iri(ns_iri)
            labels = tuple(
                namespace._get_labels_for_iri(
                    entity_iri,
                    _return_literal=True,
                    _return_label_property=True,
                )
            )
            if not labels:
                logger.debug(f"No label for {entity_iri}")
            else:
                labels = sorted(
                    labels,
                    key=lambda x: (
                        self._get_entity_name_order_label[x[0]],
                        self._get_entity_name_order_language(x[1].language),
                    ),
                )
                labels = tuple(label[1].toPython() for label in labels)
                return labels[0]
        return entity_iri[len(ns_iri) :]

    _get_entity_name_order_label = {
        rdflib.SKOS.prefLabel: 0,
        rdflib.RDFS.label: 1,
    }

    @staticmethod
    def _get_entity_name_order_language(language):
        if language == "en":
            return ""
        elif language is None:
            return "_"
        else:
            return language

    def bind(self, name: str, iri: rdflib.URIRef):
        """Bind a namespace to this namespace registry.

        Args:
            name (str): the name to use for the new namespace.
            iri (rdflib.URIRef): the iri prefix of the new namespace.
        """
        # if name in self._namespaces:
        #    logger.warning(f'Namespace {name} already defined in the'
        #                   f'namespace registry, replacing with new'
        #                   f'prefix {iri}.')
        self._namespaces[name] = iri
        self._graph.bind(name, iri)

    def clear(self):
        """Clear the loaded Graph and load cuba only.

        Returns:
            [type]: [description]
        """
        self._namespaces = dict()
        self._graph = rdflib.Graph()
        self._load_cuba()
        self.from_iri.cache_clear()
        self._get.cache_clear()
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
            for name, iri in self._namespaces.items():
                print("%s\t%s" % (name, iri), file=f)

    def load_graph_file(self, path):
        """Load the installed graph from at the given path.

        Args:
            path (Path): path to directory where the ontology has been
                installed.
        """
        # Migrate old ontology formats if needed.
        if os.path.exists(os.path.join(path, "parser/yml")):
            from osp.core.ontology.installation import pico_migrate

            pico_migrate(self, path)
        # Migrate to 3.5.3.1 format if needed.
        migration_version_filename = "last-migration-osp-core-version.txt"
        migration_version_file_path = os.path.join(
            path, migration_version_filename
        )
        if os.path.exists(migration_version_file_path):
            with open(migration_version_file_path, "r") as version_file:
                from ..pico import CompareOperations, compare_version

                version = version_file.read().strip()
                do_migration = not version or compare_version(
                    version, "3.5.3.1", operation=CompareOperations.l
                )
        else:
            do_migration = True
        if do_migration:
            from osp.core.ontology.installation import pico_migrate_v3_5_3_1

            pico_migrate_v3_5_3_1(
                path, migration_version_filename, namespace_registry=self
            )

        path_graph = os.path.join(path, "graph.xml")
        path_ns = os.path.join(path, "namespaces.txt")
        if os.path.exists(path_graph):
            self._graph.parse(path_graph, format="xml")
            if os.path.exists(path_ns):
                with open(path_ns, "r") as f:
                    for line in f:
                        name, iri = line.strip("\n").split("\t")
                        self.bind(name, rdflib.URIRef(iri))
        else:
            self._load_cuba()

    def _load_cuba(self):
        """Load the cuba namespace."""
        path_cuba = os.path.join(os.path.dirname(__file__), "docs", "cuba.ttl")
        self._graph.parse(path_cuba, format="ttl")
        self.bind("cuba", rdflib.URIRef("http://www.osp-core.com/cuba#"))

    def load_parser(self, parser: OntologyParser):
        """Load new namespace(s) from a parser object.

        Args:
            parser (OntologyParser): the ontology parser from where to load
                the new namespaces
        """
        namespaces = (
            parser.namespaces.items()
            if isinstance(parser.namespaces, dict)
            else dict()
        )
        logger.info(
            "Loading namespaces %s."
            % "; ".join([f"{name}, {uri}" for name, uri in namespaces])
        )
        ontology = Ontology(from_parser=parser)
        # Force default relationships to be installed before installing a new
        # ontology.
        self._check_default_relationship_installed(ontology)
        # Merge ontology graph.
        self._graph += ontology.graph
        # Bind namespaces.
        for name, iri in namespaces:
            if not (iri.endswith("#") or iri.endswith("/")):
                iri += "#"
            self.bind(name, iri)

    def _check_default_relationship_installed(
        self,
        ontology: Ontology,
        allow_types=frozenset(
            {
                rdflib.OWL.ObjectProperty,
            }
        ),
    ):
        if not ontology.default_relationship:
            return
        found = False
        # Check if it is in the namespace to be installed.
        for s, p, o in ontology.graph.triples(
            (ontology.default_relationship, rdflib.RDF.type, None)
        ):
            if o in allow_types:
                found = True
                break
        # If not, found, find it in the namespace registry.
        if not found:
            try:
                print(ontology.default_relationship)
                self.from_iri(ontology.default_relationship)
                found = True
            except KeyError:
                pass
        if not found:
            raise ValueError(
                f"The default relationship "
                f"{ontology.default_relationship} defined for "
                f"the ontology package {ontology.identifier} "
                f"is not installed."
            )


namespace_registry = NamespaceRegistry()
