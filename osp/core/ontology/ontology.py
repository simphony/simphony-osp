"""Defines an ontology."""
import logging
from copy import deepcopy
from typing import Dict, Iterable, Optional, Set, Tuple, Union

import rdflib
from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef

from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.parser.parser import OntologyParser

logger = logging.getLogger(__name__)


class Ontology:
    """Defines an ontology.

    Sets the basis for editable ontologies. This object is the one meant to be
    loaded by the namespace registry.
    """

    identifier: str
    namespaces: Dict[str, URIRef]
    requirements: Set[str]
    _ontology_graph: Graph
    _ontology_overlay: Graph

    @property
    def active_relationships(self) -> Tuple[URIRef]:
        """Get the active relationships defined in the ontology."""
        return tuple(
            iri
            for iri in self._ontology_overlay.subjects(
                RDFS.subPropertyOf, rdflib_cuba.activeRelationship
            )
        )

    @active_relationships.setter
    def active_relationships(self, value: Tuple[URIRef]):
        """Set the active relationships defined in the ontology."""
        for triple in self._ontology_overlay.triples(
            (None, RDFS.subPropertyOf, rdflib_cuba.activeRelationship)
        ):
            self._ontology_overlay.remove(triple)
        for relationship in value:
            self._ontology_overlay.add(
                (
                    relationship,
                    RDFS.subPropertyOf,
                    rdflib_cuba.activeRelationship,
                )
            )

    @property
    def default_relationship(self) -> Optional[URIRef]:
        """Get the default relationship defined in the ontology."""
        default_relationships = (
            o
            for s, o in self._ontology_overlay.subject_objects(
                rdflib_cuba._default_rel
            )
            if s in self.namespaces.values()
        )
        try:
            default_relationship = next(default_relationships)
        except StopIteration:
            default_relationship = None
        return default_relationship

    @default_relationship.setter
    def default_relationship(self, value: Optional[URIRef]):
        """Set the default relationship defined in the ontology."""
        default_relationships = (
            o
            for s, o in self._ontology_overlay.subject_objects(
                rdflib_cuba._default_rel
            )
            if s in self.namespaces.values()
        )
        for triple in default_relationships:
            self._ontology_overlay.remove(triple)
        if value is not None:
            for iri in self.namespaces.values():
                self._ontology_overlay.add(
                    (iri, rdflib_cuba._default_rel, value)
                )

    @property
    def reference_style(self) -> bool:
        """Get the reference style defined in the ontology.

        Can be either by label (True) or by iri suffix (False).
        """
        true_reference_styles = (
            s
            for s in self._ontology_overlay.subjects(
                rdflib_cuba._reference_by_label, Literal(True)
            )
            if s in self.namespaces.values()
        )
        try:
            default_relationship = next(true_reference_styles)
        except StopIteration:
            default_relationship = None
        return default_relationship

    @reference_style.setter
    def reference_style(self, value: bool) -> bool:
        """Set the reference style defined in the ontology.

        Can be either by label (True) or by iri suffix (False).
        """
        reference_style_triples = (
            (s, p, o)
            for s, p, o in self._ontology_overlay.triples(
                (None, rdflib_cuba._reference_by_label, Literal(True))
            )
            if s in self.namespaces.values()
        )
        for triple in reference_style_triples:
            self._ontology_overlay.remove(triple)
        for iri in self.namespaces.values():
            self._ontology_overlay.add(
                (iri, rdflib_cuba._reference_by_label, Literal(value))
            )

    @property
    def graph(self) -> Graph:
        """Get the ontology graph."""
        return self._ontology_graph + self._ontology_overlay

    def __init__(
        self,
        identifier: str = None,
        namespaces: Dict[str, str] = None,
        requirements: Iterable[str] = None,
        from_parser: OntologyParser = None,
    ):
        """Initialize the ontology.

        A few metadata can be specified, but the ontology will be essentially
        empty unless it is created from a parser object.
        """
        if from_parser:  # Compute ontology graph from an ontology parser.
            parser = from_parser
            self._ontology_graph = deepcopy(parser.graph)
            self._ontology_overlay = self._overlay_from_parser(parser)
            for attr in ("identifier", "namespaces", "requirements"):
                setattr(self, attr, getattr(parser, attr))
        else:  # Create an empty ontology.
            self._ontology_graph = Graph()
            self._ontology_overlay = Graph()
            self.identifier = identifier if identifier else ""
            self.namespaces = namespaces if namespaces else dict()
            self.requirements = requirements if requirements else set()

    def _update_overlay(self) -> Graph:
        graph = self._ontology_graph
        overlay = Graph()
        for namespace, iri in self.namespaces.items():
            # Look for duplicate labels.
            if self.reference_style:
                _check_duplicate_labels(graph, iri)
        _check_namespaces(self.namespaces.values(), graph)
        self._overlay_add_cuba_triples(self, overlay)
        self._overlay_add_default_rel_triples(self, overlay)
        self._overlay_add_reference_style_triples(self, overlay)
        return overlay

    def _overlay_from_parser(self, parser: OntologyParser) -> Graph:
        graph = parser.graph
        overlay = Graph()
        for namespace, iri in parser.namespaces.items():
            # Look for duplicate labels.
            if parser.reference_style:
                _check_duplicate_labels(graph, iri)
        _check_namespaces(parser.namespaces.values(), graph)
        self._overlay_add_cuba_triples(parser, overlay)
        self._overlay_add_default_rel_triples(parser, overlay)
        self._overlay_add_reference_style_triples(parser, overlay)
        return overlay

    @staticmethod
    def _overlay_add_default_rel_triples(
        parser: Union[OntologyParser, "Ontology"], overlay: Graph
    ):
        """Add the triples to the graph that indicate the default rel.

        The default rel is defined per namespace. However, only one is
        currently supported per ontology, therefore all namespaces defined in
        the ontology will have the same default relationship (the one of the
        package).
        """
        if parser.default_relationship is None:
            return
        for namespace in parser.namespaces.values():
            overlay.add(
                (
                    URIRef(namespace),
                    rdflib_cuba._default_rel,
                    URIRef(parser.default_relationship),
                )
            )

    @staticmethod
    def _overlay_add_cuba_triples(
        parser: Union[OntologyParser, "Ontology"], overlay: Graph
    ):
        """Add the triples to connect the owl ontology to CUBA."""
        for iri in parser.active_relationships:
            if (iri, RDF.type, OWL.ObjectProperty) not in parser.graph:
                logger.warning(
                    f"Specified relationship {iri} as "
                    f"active relationship, which is not "
                    f"a valid object property in the ontology."
                    f"If such relationship belongs to another "
                    f"ontology, and such ontology is installed, "
                    f"then you may safely ignore this warning."
                )
                # This requirement is checked later on in
                # `namespace_registry.py`
                # (NamespaceRegistry._check_default_relationship_installed).
            overlay.add(
                (iri, RDFS.subPropertyOf, rdflib_cuba.activeRelationship)
            )

    @staticmethod
    def _overlay_add_reference_style_triples(
        parser: Union[OntologyParser, "Ontology"], overlay: Graph
    ):
        """Add a triple to store how the user should reference the entities.

        The reference style (by entity label or by iri suffix) is defined per
        namespace. However, only one is currently supported per ontology,
        therefore all namespaces defined in the ontology will have the same
        reference style (the one of the package).
        """
        for namespace in parser.namespaces.values():
            if parser.reference_style:
                overlay.add(
                    (
                        URIRef(namespace),
                        rdflib_cuba._reference_by_label,
                        Literal(True),
                    )
                )


def _check_duplicate_labels(graph: Graph, namespace: Union[str, URIRef]):
    # Recycle code methods from the Namespace class. A namespace class
    # cannot be used directly, as the namespace is being spawned.
    # This may be useful if the definition of containment for ontology
    # namespaces ever changes.
    placeholder = type(
        "",
        (object,),
        {
            "_iri": rdflib.URIRef(namespace),
            "_graph": graph,
            "_label_properties": OntologyNamespace._label_properties,
        },
    )

    def in_namespace(item):
        return OntologyNamespace.__contains__(placeholder, item)

    def labels_for_iri(iri):
        return OntologyNamespace._get_labels_for_iri(
            placeholder, iri, lang=None, _return_literal=True
        )

    # Finally, check for the duplicate labels.
    subjects = set(
        subject for subject in graph.subjects() if in_namespace(subject)
    )
    results = set(
        ((label.toPython(), label.language or ""), iri)
        for iri in subjects
        for label in labels_for_iri(iri)
    )
    results = sorted(results)
    labels, iris = tuple(result[0] for result in results), tuple(
        result[1] for result in results
    )
    coincidence_search = tuple(
        i for i in range(1, len(labels)) if labels[i - 1] == labels[i]
    )
    conflicting_labels = {labels[i]: set() for i in coincidence_search}
    for i in coincidence_search:
        conflicting_labels[labels[i]] |= {iris[i - 1], iris[i]}
    if len(conflicting_labels) > 0:
        texts = (
            f"{label[0]}, language "
            f'{label[1] if label[1] != "" else None}: '
            f'{", ".join(tuple(str(iri) for iri in iris))}'
            for label, iris in conflicting_labels.items()
        )
        raise KeyError(
            f"The following labels are assigned to more than "
            f"one entity in namespace {namespace}; "
            f'{"; ".join(texts)} .'
        )


def _check_namespaces(namespace_iris: Iterable[URIRef], graph: Graph):
    namespaces = list(namespace_iris)
    for s, p, o in graph:
        pop = None
        for ns in namespaces:
            if s.startswith(ns):
                pop = ns
                logger.debug(
                    f"There exists an entity for namespace {ns}:"
                    f"\n\t{s, p, o}."
                )
        if pop:
            namespaces.remove(pop)
        if not namespaces:
            break
    for namespace in namespaces:
        logger.warning(f"There exists no entity for namespace {namespace}.")
