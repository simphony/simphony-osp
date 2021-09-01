"""Defines an ontology."""

import itertools
import logging
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union

import rdflib
from rdflib import RDF, RDFS, OWL, Graph, URIRef, Literal

from osp.core.ontology.cuba import cuba_namespace
from osp.core.ontology.datatypes import UID
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.parser.parser import OntologyParser
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.session.session import Session

logger = logging.getLogger(__name__)


class Ontology(Session):
    """Represents an ontology.

    The Ontology class extends the Session class, as it is not merely a graph,
    but has a few more characteristics that define it, such as an identifier,
    a list of namespaces included in the ontology, dependencies on other
    ontologies...

    The most notable difference between an Ontology and a session is that it
    not only has a `_graph` attribute like the session, but also an additional
    `_overlay` graph, that contains this metadata.
    """

    identifier: Optional[str]
    namespaces: List[OntologyNamespace]
    requirements: Set[str]
    _graph: Graph
    _overlay: Graph

    @property
    def active_relationships(self) -> Tuple[OntologyRelationship]:
        """Get the active relationships defined in the ontology."""
        # TODO: Transitive closure.
        return tuple(OntologyRelationship(UID(s), self) for s in
                     self._overlay.subjects(RDFS.subPropertyOf,
                                            cuba_namespace.activeRelationship))

    @active_relationships.setter
    def active_relationships(self, value: Iterable[OntologyRelationship]):
        """Set the active relationships defined in the ontology."""
        for triple in self._overlay.triples(
                (None, RDFS.subPropertyOf, cuba_namespace.activeRelationship)):
            self._overlay.remove(triple)
        for relationship in value:
            self._overlay.add((relationship.iri, RDFS.subPropertyOf,
                               cuba_namespace.activeRelationship))

    @property
    def default_relationship(self) -> Optional[OntologyRelationship]:
        """Get the default relationship defined in the ontology."""
        namespace_iris = tuple(ns.iri for ns in self.namespaces)
        default_relationships = (OntologyRelationship(UID(o), self)
                                 for s, o in
                                 self._overlay.subject_objects(
                                     cuba_namespace._default_rel)
                                 if s in namespace_iris)
        default_relationships = tuple(
            itertools.islice(default_relationships, 2))
        if len(default_relationships) > 1:
            raise ValueError(f"Multiple default relationships for ontology"
                             f"{self}.")
        elif len(default_relationships) == 0:
            default_relationship = None
        else:
            default_relationship = default_relationships[0]
        return default_relationship

    @default_relationship.setter
    def default_relationship(self, value: Optional[OntologyRelationship]):
        """Set the default relationship defined in the ontology."""
        namespace_iris = tuple(ns.iri for ns in self.namespaces)
        default_relationships = (o for s, o in
                                 self._overlay.subject_objects(
                                     cuba_namespace._default_rel)
                                 if s in namespace_iris)
        for o in default_relationships:
            self._overlay.remove((None, cuba_namespace._default_rel, o))
        if value is not None:
            for iri in namespace_iris:
                self._overlay.add((iri, cuba_namespace._default_rel,
                                   value.iri))

    @property
    def reference_style(self) -> bool:
        """Get the reference style defined in the ontology.

        Can be either by label (True) or by iri suffix (False).
        """
        namespace_iris = tuple(ns.iri for ns in self.namespaces)
        true_reference_styles = (s for s in
                                 self._overlay.subjects(
                                     cuba_namespace._reference_by_label,
                                     Literal(True))
                                 if s in namespace_iris)
        true_reference_styles = tuple(
            itertools.islice(true_reference_styles, 2))
        if len(true_reference_styles) > 1:
            raise ValueError(f"Multiple reference styles for ontology"
                             f"{self}.")
        elif len(true_reference_styles) == 0:
            reference_style = False
        else:
            reference_style = True
        return reference_style

    @reference_style.setter
    def reference_style(self, value: bool):
        """Set the reference style defined in the ontology.

        Can be either by label (True) or by iri suffix (False).
        """
        namespace_iris = tuple(ns.iri for ns in self.namespaces)
        reference_style_triples = (
            (s, p, o) for s, p, o in self._overlay.triples(
                (None, cuba_namespace._reference_by_label, Literal(True)))
            if s in namespace_iris
        )
        for triple in reference_style_triples:
            self._overlay.remove(triple)
        for iri in namespace_iris:
            self._overlay.add((iri, cuba_namespace._reference_by_label,
                               Literal(value)))

    @property
    def graph(self) -> Graph:
        """Get the ontology graph."""
        return self._graph + self._overlay

    def get_namespace(self, name: Union[str, URIRef]) -> OntologyNamespace:
        """Get a namespace registered with the ontology.

        Args:
            name: The namespace name to search for.

        Returns:
            The ontology namespace.

        Raises:
            KeyError: Namespace not found.
        """
        coincidences = iter(tuple())
        if isinstance(name, URIRef):
            coincidences_iri = (x for x in self.namespaces if x.iri == name)
            coincidences = itertools.chain(coincidences, coincidences_iri)
        elif isinstance(name, str):
            coincidences_name = (x for x in self.namespaces if x.name == name)
            coincidences = itertools.chain(coincidences, coincidences_name)
            # Last resort: user provided string but may be an IRI.
            coincidences_fallback = (x for x in self.namespaces
                                     if x.iri == URIRef(name))
            coincidences = itertools.chain(coincidences, coincidences_fallback)

        result = next(coincidences, None)
        if result is None:
            raise KeyError(f"Namespace {name} not found in ontology {self}.")
        return result

    def __init__(self,
                 identifier: Optional[str] = None,
                 namespaces: Dict[str, URIRef] = None,
                 requirements: Iterable[str] = None,
                 from_parser: Optional[OntologyParser] = None):
        """Initialize the ontology.

        A few metadata can be specified, but the ontology will be essentially
        empty unless it is created from a parser object.
        """
        super().__init__()
        if from_parser:  # Compute ontology graph from an ontology parser.
            parser = from_parser
            self._graph += parser.graph
            self._overlay = self._overlay_from_parser(parser)
            self.namespaces = [OntologyNamespace(iri=iri,
                                                 ontology=self,
                                                 name=name)
                               for name, iri in parser.namespaces.items()]
            for attr in ('identifier', 'requirements'):
                setattr(self, attr, getattr(parser, attr))
        else:  # Create an empty ontology.
            self._overlay = Graph()
            self.identifier = identifier
            self.namespaces = [
                OntologyNamespace(iri=value, name=key, ontology=self)
                for key, value in namespaces.keys()] \
                if namespaces else list()
            self.requirements = requirements if requirements else set()

    def __str__(self):
        """Human readable string representation for the ontology object."""
        return f"{self.identifier}"

    def _update_overlay(self) -> Graph:
        graph = self._graph
        overlay = Graph()
        for namespace, iri in ((ns, ns.iri) for ns in self.namespaces):
            # Look for duplicate labels.
            if self.reference_style:
                _check_duplicate_labels(graph, iri)
        _check_namespaces((ns.iri for ns in self.namespaces), graph)
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
    def _overlay_add_default_rel_triples(parser: Union[OntologyParser,
                                                       'Ontology'],
                                         overlay: Graph):
        """Add the triples to the graph that indicate the default rel.

        The default rel is defined per namespace. However, only one is
        currently supported per ontology, therefore all namespaces defined in
        the ontology will have the same default relationship (the one of the
        package).
        """
        if parser.default_relationship is None:
            return
        for namespace in parser.namespaces.values():
            overlay.add((
                URIRef(namespace),
                cuba_namespace._default_rel,
                URIRef(parser.default_relationship)
            ))

    @staticmethod
    def _overlay_add_cuba_triples(parser: Union[OntologyParser, 'Ontology'],
                                  overlay: Graph):
        """Add the triples to connect the owl ontology to CUBA."""
        for iri in parser.active_relationships:
            if (iri, RDF.type, OWL.ObjectProperty) not in parser.graph:
                logger.warning(f"Specified relationship {iri} as "
                               f"active relationship, which is not "
                               f"a valid object property in the ontology."
                               f"If such relationship belongs to another"
                               f"ontology, and such ontology is installed, "
                               f"then you may safely ignore this warning.")
                # This requirement is checked later on in
                # `namespace_registry.py`
                # (NamespaceRegistry._check_default_relationship_installed).
            overlay.add(
                (iri, RDFS.subPropertyOf,
                 cuba_namespace.activeRelationship)
            )

    @staticmethod
    def _overlay_add_reference_style_triples(parser: Union[OntologyParser,
                                                           'Ontology'],
                                             overlay: Graph):
        """Add a triple to store how the user should reference the entities.

        The reference style (by entity label or by iri suffix) is defined per
        namespace. However, only one is currently supported per ontology,
        therefore all namespaces defined in the ontology will have the same
        reference style (the one of the package).
        """
        for namespace in parser.namespaces.values():
            if parser.reference_style:
                overlay.add((
                    URIRef(namespace),
                    cuba_namespace._reference_by_label,
                    Literal(True)
                ))

    def _notify_delete(self, cuds_object):
        pass

    def _notify_update(self, cuds_object):
        pass

    def _notify_read(self, cuds_object):
        pass

    def _get_full_graph(self):
        pass


def _check_duplicate_labels(graph: Graph, namespace: Union[str, URIRef]):
    # Recycle code methods from the Namespace class. A namespace class
    # cannot be used directly, as the namespace is being spawned.
    # This may be useful if the definition of containment for ontology
    # namespaces ever changes.
    placeholder = type('', (object,),
                       {'_iri': rdflib.URIRef(namespace),
                        '_graph': graph,
                        '_label_properties':
                            OntologyNamespace._label_properties})

    def in_namespace(item):
        return OntologyNamespace.__contains__(placeholder, item)

    def labels_for_iri(iri):
        return OntologyNamespace._get_labels_for_iri(placeholder, iri,
                                                     lang=None,
                                                     _return_literal=True)

    # Finally check for the duplicate labels.
    subjects = set(subject for subject in graph.subjects()
                   if in_namespace(subject))
    results = sorted(((label.toPython(), label.language), iri)
                     for iri in subjects for label
                     in labels_for_iri(iri))
    labels, iris = tuple(result[0] for result in results), \
        tuple(result[1] for result in results)
    coincidence_search = tuple(i
                               for i in range(1, len(labels))
                               if labels[i - 1] == labels[i])
    conflicting_labels = {labels[i]: set() for i in coincidence_search}
    for i in coincidence_search:
        conflicting_labels[labels[i]] |= {iris[i - 1], iris[i]}
    if len(conflicting_labels) > 0:
        texts = (f'{label[0]}, language {label[1]}: '
                 f'{", ".join(tuple(str(iri) for iri in iris))}'
                 for label, iris in conflicting_labels.items())
        raise KeyError(f'The following labels are assigned to more than '
                       f'one entity in namespace {namespace}; '
                       f'{"; ".join(texts)}.')


def _check_namespaces(namespace_iris: Iterable[URIRef],
                      graph: Graph):
    namespaces = list(namespace_iris)
    for s, p, o in graph:
        pop = None
        for ns in namespaces:
            if s.startswith(ns):
                pop = ns
                logger.debug(f"There exists an entity for namespace {ns}:"
                             f"\n\t{s, p, o}.")
        if pop:
            namespaces.remove(pop)
        if not namespaces:
            break
    for namespace in namespaces:
        logger.warning(f"There exists no entity for namespace {namespace}.")


tbox = Ontology()
