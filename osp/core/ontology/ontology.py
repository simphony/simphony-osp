from copy import deepcopy
from typing import Union, Set, Dict, Tuple, Optional, Iterable
import logging
from rdflib import RDF, RDFS, OWL, Graph, URIRef, Literal
import rdflib
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.parser.parser import OntologyParser

logger = logging.getLogger(__name__)


class Ontology:
    identifier: str
    namespaces: Dict[str, URIRef]
    requirements: Set[str]
    _ontology_graph: Graph
    _ontology_overlay: Graph

    @property
    def active_relationships(self) -> Tuple[URIRef]:
        return tuple(iri for iri in self._ontology_overlay.subjects(
            RDFS.subPropertyOf, rdflib_cuba.activeRelationship))

    @property
    def default_relationship(self) -> Optional[URIRef]:
        default_relationships = (o for s, o in
                                 self._ontology_overlay.subject_objects(
                                     rdflib_cuba._default_rel)
                                 if s in self.namespaces.values())
        try:
            default_relationship = next(default_relationships)
        except StopIteration:
            default_relationship = None
        return default_relationship

    @property
    def reference_style(self) -> bool:
        true_reference_styles = (s for s in
                                 self._ontology_overlay.subjects(
                                     rdflib_cuba._reference_by_label,
                                     Literal(True))
                                 if s in self.namespaces.values())
        try:
            default_relationship = next(true_reference_styles)
        except StopIteration:
            default_relationship = None
        return default_relationship

    @property
    def graph(self) -> Graph:
        return self._ontology_graph + self._ontology_overlay

    def __init__(self, identifier: str = None,
                 namespaces: Dict[str, str] = None,
                 requirements: Iterable[str] = None,
                 from_parser: OntologyParser = None):
        if from_parser:  # Compute ontology graph from an ontology parser.
            parser = from_parser
            self._ontology_graph = deepcopy(parser.graph)
            self._ontology_overlay = self._overlay_from_parser(parser)
            for attr in ('identifier', 'namespaces', 'requirements'):
                setattr(self, attr, getattr(parser, attr))
        else:  # Create an empty ontology.
            self._ontology_graph = Graph()
            self._ontology_overlay = Graph()
            self.identifier = identifier
            self.namespaces = namespaces
            self.requirements = requirements

    def _overlay_from_parser(self, parser: OntologyParser) -> Graph:
        graph = parser.graph
        overlay = Graph()
        for namespace, iri in parser.namespaces.items():
            # Look for duplicate labels.
            if parser.reference_style:
                _check_duplicate_labels(graph, iri)
        _check_namespaces(parser.namespaces.values(), graph)
        self._overlay_from_parser_add_cuba_triples(parser, overlay)
        self._overlay_from_parser_add_default_rel_triples(parser, overlay)
        self._overlay_from_parser_add_reference_style_triples(parser, overlay)
        return overlay

    @staticmethod
    def _overlay_from_parser_add_default_rel_triples(parser: OntologyParser,
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
                rdflib_cuba._default_rel,
                URIRef(parser.default_relationship)
            ))

    @staticmethod
    def _overlay_from_parser_add_cuba_triples(parser: OntologyParser,
                                              overlay: Graph):
        """Add the triples to connect the owl ontology to CUBA."""
        for iri in parser.active_relationships:
            if (iri, RDF.type, OWL.ObjectProperty) not in parser.graph:
                raise ValueError(f"Specified relationship {iri} as "
                                 f"active relationship, which is not "
                                 f"a valid object property in the ontology.")
            overlay.add(
                (iri, RDFS.subPropertyOf,
                 rdflib_cuba.activeRelationship)
            )

    @staticmethod
    def _overlay_from_parser_add_reference_style_triples(parser: OntologyParser,
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
                    rdflib_cuba._reference_by_label,
                    Literal(True)
                ))


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
