"""Abstract Base Class for all Sessions."""

import itertools
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Set, \
    TYPE_CHECKING, \
    Union

import rdflib
from rdflib import OWL, RDF, RDFS, SKOS, BNode, Graph, Literal, URIRef
from rdflib.graph import ReadOnlyGraphAggregate
from rdflib.term import Identifier
from rdflib.store import Store

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.cuba import cuba_namespace
from osp.core.ontology.datatypes import UID
from osp.core.ontology.individual import OntologyIndividual
from osp.core.ontology.namespace import OntologyNamespace
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.parser.parser import OntologyParser
from osp.core.ontology.relationship import OntologyRelationship

if TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity


class Session:
    """Box with data entities.

    Defines the common standard API and sets the registry.
    """
    _session_stack: List['Session'] = []
    _times_opened: int = 0
    _namespaces: Dict[URIRef, str]
    _graph: Graph
    _overlay: Graph

    @classmethod
    def get_default_session(cls) -> Optional['Session']:
        """Returns the default session."""
        return cls._session_stack[-1] if len(cls._session_stack) > 0 else None

    @classmethod
    def set_default_session(cls, session: 'Session'):
        """Adds a session to the stack of sessions.

        This effectively makes it the default. As the session stack is private,
        calling this command from outside this class is irreversible.
        """
        cls._session_stack.append(session)

    # Public API
    # ↓ ------ ↓
    identifier: Optional[str]
    ontology: Optional['Session'] = None
    label_properties: Tuple[URIRef] = (SKOS.prefLabel, RDFS.label)

    @property
    def namespaces(self) -> List[OntologyNamespace]:
        """Get all the namespaces bound to the session."""
        return [OntologyNamespace(iri=iri,
                                  name=name,
                                  ontology=self.ontology)
                for iri, name in self.ontology._namespaces.items()]

    def bind(self,
             name: Optional[str],
             iri: Union[str, URIRef]):
        """Bind a namespace to this ontology.

        Args:
            name: the name to bind.
            iri: the IRI of the namespace to be bound to such name.
        """
        iri = URIRef(iri)
        for key, value in self.ontology._namespaces.items():
            if value == name and key != iri:
                raise ValueError(f"Namespace {key} is already bound to name "
                                 f"{name} in ontology {self}. "
                                 f"Please unbind it first.")
        else:
            self.ontology._namespaces[iri] = name
            self.ontology._graph.bind(name, iri)

    def unbind(self, name: Union[str, URIRef]):
        """Unbind a namespace from this ontology.

        Args:
            name: the name to which the namespace is already bound, or the
                IRI of the namespace.
        """
        for key, value in dict(self.ontology._namespaces).items():
            if value == name or key == URIRef(name):
                del self.ontology._namespaces[key]

    def __init__(self,
                 store: Store = None,
                 ontology: Optional[Union['Session', bool]] = None,
                 identifier: Optional[str] = None,
                 namespaces: Dict[str, URIRef] = None,
                 from_parser: Optional[OntologyParser] = None):
        """Initialize the session."""
        self._times_opened = 1
        self._graph = Graph() if store is None else Graph(store)

        if isinstance(ontology, Session):
            self.ontology = ontology
        elif ontology is True:
            self.ontology = self
        elif not isinstance(ontology, bool) and ontology is not None:
            raise TypeError(f"Invalid ontology argument: {ontology}."
                            f"Expected either a `Session` or `bool` object, "
                            f"got {type(ontology)} instead.")

        self._storing = list()

        self._namespaces = dict()
        self._overlay = Graph()
        if from_parser:  # Compute session graph from an ontology parser.
            if self.ontology is not self:
                raise RuntimeError("Cannot load parsers in sessions which "
                                   "are not their own ontology. Load the "
                                   "parser on the ontology instead.")
            self.load_parser(from_parser)
            self.identifier = identifier or from_parser.identifier
        else:  # Create an empty session.
            self.identifier = identifier
            namespaces = namespaces if namespaces is not None else dict()
            for key, value in namespaces.items():
                self.bind(key, value)

    def get_namespace_bind(self,
                           namespace: Union[OntologyNamespace, URIRef, str]) \
            -> Optional[str]:
        """Returns the name used to bind a namespace to the ontology.

        Args:
            namespace: Either an OntologyNamespace or the IRI of a namespace.

        Raises:
            KeyError: Namespace not bound to to the ontology.
        """
        ontology = self.ontology
        if isinstance(namespace, OntologyNamespace):
            ontology = namespace.ontology
            namespace = namespace.iri
        else:
            namespace = URIRef(namespace)

        not_bound_error = KeyError(f"Namespace {namespace} not bound to "
                                   f"ontology {self}.")
        if ontology is not self.ontology:
            raise not_bound_error
        try:
            return self.ontology._namespaces[namespace]
        except KeyError:
            raise not_bound_error

    @property
    def active_relationships(self) -> Tuple[OntologyRelationship]:
        """Get the active relationships defined in the ontology."""
        # TODO: Transitive closure.
        return tuple(OntologyRelationship(UID(s), self) for s in
                     self.ontology._overlay.subjects(
                         RDFS.subPropertyOf,
                         cuba_namespace.activeRelationship))

    @active_relationships.setter
    def active_relationships(self, value: Union[None,
                                                Iterable[
                                                    OntologyRelationship]]):
        """Set the active relationships defined in the ontology."""
        value = iter(()) if value is None else value

        for triple in self.ontology._overlay.triples(
                (None, RDFS.subPropertyOf, cuba_namespace.activeRelationship)):
            self.ontology._overlay.remove(triple)
        for relationship in value:
            self.ontology._overlay.add(
                (relationship.iri, RDFS.subPropertyOf,
                 cuba_namespace.activeRelationship))

    @property
    def default_relationships(self) -> Dict[OntologyNamespace,
                                            OntologyRelationship]:
        """Get the default relationship defined in the ontology.

        Each namespace can have a different default relationship.
        """
        default_relationships = {
            ns: (OntologyRelationship(UID(o), self.ontology), )
            for ns in self.namespaces
            for o in self.ontology._overlay.objects(
                ns.iri, cuba_namespace._default_rel)}
        for key, value in default_relationships.items():
            if len(value) > 1:
                raise RuntimeError(f'Multiple default relationships defined'
                                   f'for namespace {key}.')
            else:
                default_relationships[key] = value[0]
        return default_relationships

    @default_relationships.setter
    def default_relationships(self,
                              value: Union[None,
                                           OntologyRelationship,
                                           Dict[OntologyNamespace,
                                                OntologyRelationship]]):
        """Set the default relationships defined in the ontology.

        Each namespace can have a different default relationship.

        Args:
            value: Sets the same default relationship for all namespaces
                value is an OntologyRelationship, set different
                relationships when a dict is provided..
        """
        if value is None:
            remove = ((None, cuba_namespace._default_rel, None), )
            add = dict()
        elif isinstance(value, OntologyRelationship):
            remove = ((None, cuba_namespace._default_rel, None), )
            add = {ns.iri: value.iri for ns in self.namespaces}
        elif isinstance(value, Dict):
            remove = ((ns.iri, cuba_namespace._default_rel, None)
                      for ns in value.keys())
            add = {ns.iri: rel.iri for ns, rel in value.items()}
        else:
            raise TypeError(f"Expected either None, an OntologyRelationship "
                            f"or a mapping (dictionary) from "
                            f"OntologyNamespace to OntologyRelationship, "
                            f"not {type(value)}.")

        for pattern in remove:
            self.ontology._overlay.remove(pattern)
        for ns_iri, rel_iri in add.items():
            self.ontology._overlay.add(
                (ns_iri, cuba_namespace._default_rel, rel_iri))

    @property
    def reference_styles(self) -> Dict[OntologyNamespace,
                                       bool]:
        """Get the reference styles defined in the ontology.

        Can be either by label (True) or by iri suffix (False).
        """
        reference_styles = {ns: False for ns in self.namespaces}
        true_reference_styles = (s for s in
                                 self.ontology._overlay.subjects(
                                     cuba_namespace._reference_by_label,
                                     Literal(True)))
        for s in true_reference_styles:
            reference_styles[self.get_namespace(s)] = True
        return reference_styles

    @reference_styles.setter
    def reference_styles(self, value: Union[bool,
                                            Dict[OntologyNamespace, bool]]):
        """Set the reference style defined in the ontology.

        Can be either by label (True) or by iri suffix (False).
        """
        if isinstance(value, bool):
            value = {ns: value for ns in self.namespaces}
        self.ontology._overlay.remove(
            (None, cuba_namespace._reference_by_label, None))
        for key, value in value.items():
            self.ontology._overlay.add(
                (key.iri, cuba_namespace._reference_by_label, Literal(value)))

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

    def load_parser(self, parser: OntologyParser):
        """Merge ontology packages with this ontology from a parser object.

        Args:
            parser: the ontology parser from where to load the new namespaces.
        """
        # Force default relationships to be installed before installing a new
        # ontology.
        self._check_default_relationship_installed(parser)
        self.ontology._graph += parser.graph
        self.ontology._overlay += self._overlay_from_parser(parser)
        for name, iri in parser.namespaces.items():
            self.bind(name, iri)

    def __enter__(self):
        """Enter session context manager."""
        self._session_stack.append(self)
        return self

    def __exit__(self, *args):
        """Close the connection to the backend."""
        if self is not self._session_stack[-1]:
            raise RuntimeError("Trying to exit the context manager of a "
                               "session that was not the latest session "
                               "context manager to be entered.")
        self._session_stack.pop()
        if self not in self._session_stack:
            self.close()

    def close(self):
        """Close the connection to the backend."""
        self._times_opened -= 1
        if self._times_opened <= 0:
            self.graph.close()

    def __contains__(self, item: 'OntologyEntity'):
        """Check whether an ontology entity is stored on the session."""
        return item.session is self

    def __iter__(self) -> Iterator['OntologyEntity']:
        """Iterate over all the ontology entities in the session."""
        # Warning: entities can be repeated.
        return (self.from_identifier(identifier)
                for identifier in self.iter_identifiers())

    def from_identifier(self, identifier: Identifier) -> 'OntologyEntity':
        """Get an entity from its identifier.

        Args:
            identifier: The identifier of the entity.

        Raises:
            KeyError: The ontology entity is not stored in this session.

        Returns:
            The OntologyEntity.
        """
        from osp.core.ontology.oclass_composition import \
            get_composition
        from osp.core.ontology.oclass_restriction import \
            get_restriction
        # TODO: make return type hint more specific.

        # Try to instantiate classes, attributes, relationships,
        # restrictions, compositions.
        # TODO: Use transitive closure just in case a subclass is identified.
        for o in self.ontology._graph.objects(identifier, RDF.type):
            if o == OWL.DatatypeProperty:
                return OntologyAttribute(UID(identifier),
                                         session=self.ontology)
            elif o == OWL.ObjectProperty:
                return OntologyRelationship(UID(identifier),
                                            session=self.ontology)
            elif o == OWL.Class:
                try:
                    x = get_composition(identifier,
                                        self.ontology)
                except ValueError:
                    x = None
                return x or OntologyClass(uid=UID(identifier),
                                          session=self.ontology)
            elif o == OWL.Restriction:
                x = get_restriction(identifier,
                                    self.ontology)
                if x:
                    return x
            elif o == RDFS.Class:
                # Appears in FOAF ontology, OWL is supported, not RDFS.
                continue

        # Try to instantiate an ontology individual.
        for o in self._graph.objects(identifier, RDF.type):
            try:
                entity = self.ontology.from_identifier(o)
            except KeyError:
                continue
            if any(sp.identifier == cuba_namespace.Container for sp in
                   entity.superclasses):
                from osp.core.ontology.interactive.container import Container
                return Container(uid=UID(identifier))
            else:
                return OntologyIndividual(uid=UID(identifier),
                                          session=self)

        supported_types = frozenset({OWL.DatatypeProperty,
                                     OWL.ObjectProperty,
                                     OWL.Class,
                                     OWL.Restriction})
        raise KeyError(f"Identifier {identifier} not found in graph, "
                       f"not an ontology individual from any of the "
                       f"installed ontologies nor any entity "
                       f"of any type in the set {supported_types}.")

    def from_label(self,
                   label: str,
                   lang: Optional[str] = None,
                   case_sensitive: bool = False) -> Set['OntologyEntity']:
        """Get an ontology entity from the registry by label.

        Args:
            label: The label of the ontology entity.
            lang: The language of the label.
            case_sensitive: when false, look for similar labels with
                different capitalization.

        Raises:
            KeyError: Unknown label.

        Returns:
            OntologyEntity: The ontology entity.
        """
        results = set()
        for identifier in self.iter_identifiers():
            entity_labels = self.iter_labels(entity=identifier,
                                             lang=lang,
                                             return_prop=False,
                                             return_literal=False)
            if case_sensitive is False:
                entity_labels = (label.lower() for label in entity_labels)
                comp_label = label.lower()
            else:
                comp_label = label
            if comp_label in entity_labels:
                results.add(self.from_identifier(identifier))
        if len(results) == 0:
            error = "No element with label %s was found in ontology %s."\
                    % (label, self)
            raise KeyError(error)
        return results

    def commit(self) -> None:
        """Commit the changes made to the session's graph."""
        self._graph.commit()
        if self.ontology is not self:
            self.ontology.commit()
        else:
            self._overlay.commit()

    # ↑ ------ ↑
    # Public API

    @property
    def graph(self) -> Graph:
        """Returns the session's graph."""
        return self._graph

    @property
    def ontology_graph(self) -> Graph:
        """Returns an aggregate of the session's graph and overlay."""
        return ReadOnlyGraphAggregate([self.ontology._graph,
                                       self.ontology._overlay])

    def iter_identifiers(self) -> Iterator[Identifier]:
        """Iterate over all the identifiers in the session."""
        # Warning: identifiers can be repeated.
        # TODO: Aren't identifiers of ontology individuals omitted?
        supported_types = frozenset({OWL.DatatypeProperty,
                                     OWL.ObjectProperty,
                                     OWL.Class,
                                     OWL.Restriction})
        return (s for t in supported_types
                for s in self._graph.subjects(RDF.type, t))

    def iter_labels(self,
                    entity: Optional[Union[
                        Identifier,
                        'OntologyEntity']] = None,
                    lang: Optional[str] = None,
                    return_prop: bool = False,
                    return_literal: bool = True
                    ) -> Iterator[Union[Literal,
                                        str,
                                        Tuple[Literal, URIRef],
                                        Tuple[str, URIRef]]]:
        """Iterate over all the labels of the entities in the session."""
        from osp.core.ontology.entity import OntologyEntity
        if isinstance(entity, OntologyEntity):
            entity = entity.identifier

        def filter_language(literal):
            if lang is None:
                return True
            elif lang == "":
                return literal.language is None
            else:
                return literal.language == lang

        labels = filter(lambda label_tuple: filter_language(label_tuple[1]),
                        ((prop, literal) for prop in self.label_properties
                         for literal in self._graph.objects(entity, prop))
                        )
        if not return_prop and not return_literal:
            return (str(x[1]) for x in labels)
        elif return_prop and not return_literal:
            return ((str(x[1]), x[0]) for x in labels)
        elif not return_prop and return_literal:
            return (x[1] for x in labels)
        else:
            return ((x[1], x[0]) for x in labels)

    def get_identifiers(self) -> Set[Identifier]:
        """Get all the identifiers in the session."""
        return set(self.iter_identifiers())

    def get_entities(self) -> Set['OntologyEntity']:
        """Get all the entities stored in the session."""
        return set(x for x in self)

    def store(self, entity: 'OntologyEntity') -> None:
        """Store a copy of given ontology entity in the session.

        Args:
            entity: The ontology entity to store.
        """
        if entity not in self:
            self._graph.remove((entity.identifier, None, None))
            for t in entity.triples:
                self._graph.add(t)

    def merge(self, entity: 'OntologyEntity') -> None:
        """Merge a given ontology entity with what is in the session.

        Copies the ontology entity to the session, but does not remove any
        old triples referring to the entity.

        Args:
            entity: The ontology entity to store.
        """
        if entity not in self:
            for t in entity.triples:
                self._graph.add(t)

    def delete(self, entity: 'OntologyEntity'):
        """Remove the ontology entity from the session."""
        self._graph.remove((entity.identifier, None, None))

    def clear(self):
        """Clear all the data stored in the session."""
        self._graph.remove((None, None, None))

    def __str__(self):
        """Convert the session to a string."""
        # TODO: Return the kind of rdflib store attached.
        return f"Session {self.identifier} at {hex(id(self))}"

# Legacy code
# ↓ ------- ↓

    def _update_overlay(self) -> Graph:
        graph = self._graph
        overlay = Graph()
        for namespace, iri in ((ns, ns.iri) for ns in self.namespaces):
            # Look for duplicate labels.
            if self.reference_styles:
                _check_duplicate_labels(graph, iri)
        _check_namespaces((ns.iri for ns in self.namespaces), graph)
        self._overlay_add_cuba_triples(self, overlay)
        self._overlay_add_default_rel_triples(self, overlay)
        self._overlay_add_reference_style_triples(self, overlay)
        return overlay

    def _overlay_from_parser(self, parser: OntologyParser) -> Graph:
        graph = parser.graph
        overlay = Graph()
        if parser.reference_style:
            for namespace, iri in parser.namespaces.items():
                # Look for duplicate labels.
                _check_duplicate_labels(graph, iri)
        _check_namespaces(parser.namespaces.values(), graph)
        self._overlay_add_cuba_triples(parser, overlay)
        self._overlay_add_default_rel_triples(parser, overlay)
        self._overlay_add_reference_style_triples(parser, overlay)
        return overlay

    def _overlay_add_default_rel_triples(self,
                                         parser: Union[OntologyParser,
                                                       'Session'],
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
            self._graph.remove((URIRef(namespace),
                                cuba_namespace._default_rel,
                                None))
            overlay.remove((URIRef(namespace),
                            cuba_namespace._default_rel,
                            None))
            overlay.add((
                URIRef(namespace),
                cuba_namespace._default_rel,
                URIRef(parser.default_relationship)
            ))

    @staticmethod
    def _overlay_add_cuba_triples(parser: Union[OntologyParser, 'Session'],
                                  overlay: Graph):
        """Add the triples to connect the owl ontology to CUBA."""
        for iri in parser.active_relationships:
            # if (iri, RDF.type, OWL.ObjectProperty) not in parser.graph:
            #     logger.warning(f"Specified relationship {iri} as "
            #                    f"active relationship, which is not "
            #                    f"a valid object property in the ontology."
            #                    f"If such relationship belongs to another "
            #                    f"ontology, and such ontology is installed, "
            #                    f"then you may safely ignore this warning.")
            #     # This requirement is checked later on in
            #     # `namespace_registry.py`
            #     # (NamespaceRegistry._check_default_relationship_installed).
            overlay.add(
                (iri, RDFS.subPropertyOf,
                 cuba_namespace.activeRelationship)
            )

    @staticmethod
    def _overlay_add_reference_style_triples(parser: Union[OntologyParser,
                                                           'Session'],
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

    def _check_default_relationship_installed(self, parser: OntologyParser,
                                              allow_types=frozenset(
                                                  {rdflib.OWL.ObjectProperty,
                                                   })
                                              ):
        if not parser.default_relationship:
            return
        found = False
        # Check if it is in the namespace to be installed.
        for s, p, o in parser.graph.triples((parser.default_relationship,
                                             rdflib.RDF.type,
                                             None)):
            if o in allow_types:
                found = True
                break
        # If not, found, find it in the namespace registry.
        if not found:
            try:
                self.from_identifier(parser.default_relationship)
                found = True
            except KeyError:
                pass
        if not found:
            raise ValueError(f'The default relationship '
                             f'{parser.default_relationship} defined for '
                             f'the ontology package {parser.identifier} '
                             f'is not installed.')


def _check_duplicate_labels(graph: Graph, namespace: Union[str, URIRef]):
    # Recycle code methods from the Namespace class. A namespace class
    # cannot be used directly, as the namespace is being spawned.
    # This may be useful if the definition of containment for ontology
    # namespaces ever changes.
    namespace = rdflib.URIRef(namespace)

    def in_namespace(item):
        # TODO: very similar to
        #  `osp.core.ontology.namespace.OntologyNamespace.__contains__`,
        #  integrate somehow.
        if isinstance(item, BNode):
            return False
        elif isinstance(item, URIRef):
            return item.startswith(namespace)
        else:
            return False

    mock_session = type('', (object,),
                        {'_graph': graph,
                         'label_properties': Session.label_properties})

    def labels_for_iri(iri):
        return Session.iter_labels(mock_session,
                                   iri,
                                   return_prop=False,
                                   return_literal=True)

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
        if pop:
            namespaces.remove(pop)
        if not namespaces:
            break

# Legacy code
# ↑ ------- ↑


Session.set_default_session(Session())
Session.ontology = Session(identifier='installed_ontologies',
                           ontology=True)
