"""An ontology namespace."""

import itertools
import logging
from typing import Any, Iterable, Iterator, Optional, TYPE_CHECKING, Tuple, \
    Union

from rdflib import BNode, URIRef
from rdflib.term import Identifier

from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.parser.yml.case_insensitivity import \
    get_case_insensitive_alternative as alt

if TYPE_CHECKING:
    from osp.core.session.session import Session


logger = logging.getLogger(__name__)


class OntologyNamespace:
    """An ontology namespace."""

    @property
    def name(self) -> Optional[str]:
        """The name of this namespace."""
        return self.ontology.get_namespace_bind(self)

    @property
    def iri(self) -> URIRef:
        """The IRI of this namespace."""
        return self._iri

    @property
    def active_relationships(self) -> Tuple[OntologyRelationship]:
        """Get the active relationships defined in the ontology.

        Only returns the relationships that belong to this namespace.
        """
        return tuple(x
                     for x in self.ontology.active_relationships
                     if x in self)

    @active_relationships.setter
    def active_relationships(self, value: Union[None,
                                                Iterable[
                                                    OntologyRelationship]]):
        """Set the active relationships defined in the ontology.

        Only replaces and sets relationships that belong to this namespace.
        """
        value = iter(()) if value is None else value

        # Keep existing relationships not belonging to this namespace.
        relationships_to_keep = (x for x in self.ontology.active_relationships
                                 if x not in self)
        self.ontology.active_relationships = itertools.chain(
            relationships_to_keep,
            value
        )

    @property
    def default_relationship(self) -> Optional[OntologyRelationship]:
        """Get the default relationship for this namespace."""
        return self.ontology.default_relationships.get(self)

    @default_relationship.setter
    def default_relationship(self,
                             value: Optional[OntologyRelationship]):
        """Set the default relationship for this namespace."""
        self.ontology.default_relationships = \
            self.ontology.default_relationships.update(
                {self: value}
            )

    @property
    def reference_style(self) -> bool:
        """Returns the reference style for the namespace.

        Returns:
            True when the references are made by label, false when made by
            suffix.
        """
        return self.ontology.reference_styles[self]

    @property
    def ontology(self) -> 'Session':
        """Returns the session that the namespace is bound to."""
        return self._ontology

    def __init__(self,
                 iri: Union[str, URIRef],
                 ontology: Optional['Session'] = None,
                 name: Optional[str] = None):
        """Initialize the namespace.

        Args:
            iri: The IRI of the namespace.
            ontology: The ontology to which the namespace is connected.
            name: The name of the namespace
        """
        from osp.core.session.session import Session
        ontology = ontology or Session.get_default_session()
        self._iri = URIRef(iri)
        self._ontology = ontology
        ontology.bind(name, iri)

    def __str__(self) -> str:
        """Transform the namespace to a human readable string.

        Returns:
            The resulting string.
        """
        return "%s (%s)" % (self.name, self.iri)

    def __repr__(self) -> str:
        """Transform the namespace to a string.

        Returns:
            The resulting string.
        """
        return "<%s: %s>" % (self.name, self.iri)

    def __eq__(self, other: 'OntologyNamespace') -> bool:
        """Check whether the two namespace objects are the same.

        Args:
            other: The namespace to compare with.

        Returns:
            bool: Whether the given namespace is the same.
        """
        return isinstance(other, OntologyNamespace) and \
            self.ontology is other.ontology and \
            self.iri == other.iri

    def __hash__(self) -> int:
        """Hash the namespace.

        The namespace is defined by its IRI and its underlying data
        structure (the ontology), which are immutable attributes.
        """
        return hash((self.ontology, self.iri))

    # Query content stored in the linked session's bag
    # ↓-----------------------------------------------↓

    def __getattr__(self, name: str) -> OntologyEntity:
        """Get an ontology entity from the associated ontology.

        Args:
            name: The label or namespace suffix of the ontology entity.

        Raises:
            AttributeError: Unknown label or suffix.

        Returns:
            The ontology entity.
        """
        if self.reference_style:
            try:
                return self.from_label(name)
            except KeyError as e:
                raise AttributeError(str(e)) from e
        else:
            try:
                return self.from_suffix(name)
            except KeyError as e:
                raise AttributeError(str(e)) from e

    def __getitem__(self, label: str) -> OntologyEntity:
        """Get an ontology entity from the associated ontology by label.

        Useful for entities whose labels contains characters which are not
        compatible with the Python syntax.

        Args:
            label: The label of the ontology entity.

        Raises:
            KeyError: Unknown label.

        Returns:
            The ontology entity.
        """
        exception = TypeError(f'{str(type(self)).capitalize()} indices must be'
                              f'of type {str} or (label: str, lang: str).')

        if isinstance(label, str):
            iterator = iter((label, None))
        elif isinstance(label, Iterable):
            iterator = label
        else:
            raise exception

        label, lang = tuple(itertools.islice(iterator, 2))

        if next(iterator, exception) is not exception:
            raise exception

        return self.from_label(label, lang, case_sensitive=True)

    def __dir__(self) -> Iterable[str]:
        """Attributes available for the OntologyNamespace class.

        Returns:
            The available attributes, which include the methods and
            the ontology entities in the namespace.
        """
        entity_autocompletion = self._iter_labels() \
            if self.reference_style else self._iter_suffixes()
        return itertools.chain(dir(super()), entity_autocompletion)

    def get(self, name: str,
            default: Optional[Any] = None) -> OntologyEntity:
        """Get an ontology entity from the registry by suffix or label.

        Args:
            name: The label or suffix of the ontology entity.
            default: The value to return if it doesn't exist.

        Returns:
            The ontology entity.
        """
        try:
            return getattr(self, name)
        except AttributeError:
            return default

    def from_iri(self, iri: Union[str, URIRef]) -> OntologyEntity:
        """Get an ontology entity directly from its IRI.

        For consistency, this method only returns entities from this namespace.

        Args:
            iri: The iri of the ontology entity.

        Returns:
            The ontology entity.

        Raises:
            KeyError: When the IRI does not belong to the namespace.
        """
        iri = URIRef(str(iri))
        if iri in self:
            return self.ontology.from_identifier(iri)
        else:
            raise KeyError(f"The IRI {iri} does not belong to the namespace"
                           f"{self}.")

    def from_suffix(self, suffix: str, case_sensitive: bool = False) -> \
            OntologyEntity:
        """Get an ontology entity from its namespace suffix.

        Args:
            suffix: Suffix of the ontology entity.
            case_sensitive: Whether to search also for the same suffix with
                different capitalization. By default, such a search is
                performed.
        """
        iri = URIRef(str(self._iri) + suffix)
        try:
            return self.from_iri(iri)
        except KeyError as e:
            if not case_sensitive:
                return self._get_case_insensitive(suffix,
                                                  self.from_suffix)
            raise e

    def from_label(self,
                   label: str,
                   lang: Optional[str] = None,
                   case_sensitive: bool = False) -> OntologyEntity:
        """Get an ontology entity from its label."""
        try:
            entities = set(
                entity
                for entity in self.ontology.from_label(
                    label, lang=lang, case_sensitive=case_sensitive)
                if entity in self
            )
        except KeyError:
            entities = set()
        if len(entities) == 0:
            error = "No element with label %s was found in namespace %s."\
                    % (label, self)
            raise KeyError(error)
        elif len(entities) >= 2:
            element_suffixes = (r.iri[len(self.iri):] for r in entities)
            error = (f"There are multiple elements "
                     f"({', '.join(element_suffixes)}) with label"
                     f" {label} for namespace {self}."
                     f"\n"
                     f"Please refer to a specific element of the "
                     f"list by calling from_iri(IRI) for "
                     f"namespace {self} for one of the following "
                     f"IRIs: " + "{iris}.")\
                .format(iris=', '.join(entity.iri for entity in entities))
            raise KeyError(error)
        return entities.pop()

    def _iter_labels(self) -> Iterator[str]:
        """Iterate over the labels of the ontology entities in the namespace.

        Returns:
            An iterator of strings containing the labels.
        """
        return itertools.chain(
            *(self.ontology.iter_labels(iri, return_literal=False)
              for iri in self._iter_identifiers()))

    def _iter_suffixes(self) -> Iterator[str]:
        """Iterate over suffixes of the ontology entities in the namespace.

        Returns:
            An iterator of suffixes containing the suffixes.
        """
        return (str(iri)[len(str(self._iri)):] for iri in self._iter_iris())

    def _iter_identifiers(self) -> Iterator[Identifier]:
        """Iterate over the identifiers of the ontology entities.

        For consistency, only returns ontology entities that belong to the
        namespace.

        Returns:
            An iterator of identifiers.
        """
        return (identifier
                for identifier in self.ontology.iter_identifiers()
                if identifier in self)

    def _iter_iris(self) -> Iterator[URIRef]:
        """Iterate over the IRIs of the ontology entities in the namespace.

        Returns:
            An iterator of IRIs.
        """
        return iter(filter(lambda x: isinstance(x, URIRef),
                           self._iter_identifiers()))

    def __iter__(self) -> Iterator['OntologyEntity']:
        """Iterate over the ontology entities in the namespace."""
        return (entity for entity in iter(self.ontology) if entity in self)

    def __len__(self) -> int:
        """Return the number of entities in the namespace."""
        return sum(1 for _ in self)

    def __contains__(self, item: Union[OntologyEntity,
                                       BNode,
                                       URIRef]) -> bool:
        """Check whether the given entity is part of the namespace.

        Args:
            item: An ontology entity or identifier.

        Returns:
            Whether the given entity name or IRI is part of the namespace.
            Blank nodes are never part of a namespace.
        """
        if isinstance(item, BNode):
            return False
        elif isinstance(item, URIRef):
            return item.startswith(self.iri)
        elif isinstance(item, OntologyEntity):
            return item.identifier in self \
                if item.session is self.ontology else \
                False
        else:
            raise TypeError(f'in {type(self)} requires, '
                            f'{Identifier} or {OntologyEntity} as left '
                            f'operand, not {type(item)}.')

    # Query content stored in the linked session's bag
    # ↑-----------------------------------------------↑

    # Backwards compatibility.
    # ↓----------------------↓

    def _get_case_insensitive(self, name: str,
                              method: callable) -> OntologyEntity:
        """Get by trying alternative naming convention of given name.

        Args:
            name: The name of the entity.
            method: The callable that finds the alternative string.

        Returns:
            The ontology entity.

        Raises:
            KeyError: Reference to unknown entity.
        """
        alternative = alt(name, self.name == "cuba")
        if alternative is None:
            raise KeyError(
                f"Unknown entity '{name}' in namespace {self.name}."
            )

        r = None
        exception = None
        try:
            r = method(alternative, case_sensitive=True)
        except KeyError as e:
            if name and name.startswith("INVERSE_OF_"):
                try:
                    r = method(name[11:], case_sensitive=False).inverse
                except KeyError:
                    raise e
            exception = e
        if r is not None:
            logger.warning(
                f"{alternative} is referenced with '{name}'. "
                f"Note that referencing entities will be case sensitive "
                f"in future releases. Additionally, entity names defined "
                f"in YAML ontology are no longer required to be ALL_CAPS. "
                f"You can use the yaml2camelcase "
                f"commandline tool to transform entity names to CamelCase."
            )
        else:
            raise KeyError(
                f"Unknown entity '{name}' in namespace {self.name}. "
                f"For backwards compatibility reasons we also "
                f"looked for {alternative} and failed."
            ) from exception
        return r

    # Backwards compatibility.
    # ↑----------------------↑
