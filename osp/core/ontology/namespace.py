"""An ontology namespace."""

import itertools
import logging
from collections.abc import Iterable
from typing import Any, Iterator, Optional, TYPE_CHECKING, Union

import rdflib
from rdflib import BNode, Literal, URIRef
from rdflib.term import Identifier

from osp.core.ontology.parser.yml.case_insensitivity import \
    get_case_insensitive_alternative as alt

if TYPE_CHECKING:
    from osp.core.ontology.entity import OntologyEntity
    from osp.core.ontology.ontology import Ontology


logger = logging.getLogger(__name__)


class OntologyNamespace:
    """An ontology namespace."""

    @property
    def name(self) -> Optional[str]:
        """The name of this namespace."""
        return self._name

    @property
    def iri(self) -> URIRef:
        """The IRI of this namespace."""
        return self._iri

    def __init__(self,
                 iri: URIRef,
                 ontology: 'Ontology',
                 name: Optional[str] = None):
        """Initialize the namespace.

        Args:
            iri: The IRI of the namespace.
            ontology: The ontology to which the namespace is connected.
            name: The name of the namespace
        """
        self._name = name
        self._iri = iri
        self.ontology = ontology

    def __str__(self) -> str:
        """Transform the namespace to a human readable string.

        Returns:
            The resulting string.
        """
        return "%s (%s)" % (self._name, self._iri)

    def __repr__(self) -> str:
        """Transform the namespace to a string.

        Returns:
            The resulting string.
        """
        return "<%s: %s>" % (self._name, self._iri)

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

    # Query content stored in the linked session's bag
    # ↓-----------------------------------------------↓

    def __getattr__(self, name: str) -> 'OntologyEntity':
        """Get an ontology entity from the associated ontology.

        Args:
            name: The label or namespace suffix of the ontology entity.

        Raises:
            AttributeError: Unknown label or suffix.

        Returns:
            The ontology entity.
        """
        if self.ontology.reference_style:
            try:
                return self.get_from_label(name)
            except KeyError as e:
                raise AttributeError(str(e)) from e
        else:
            try:
                return self.get_from_suffix(name)
            except KeyError as e:
                raise AttributeError(str(e)) from e

    def __getitem__(self, label: str) -> 'OntologyEntity':
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

        return self.get_from_label(label, lang, case_sensitive=True)

    def __dir__(self) -> Iterable[str]:
        """Attributes available for the OntologyNamespace class.

        Returns:
            The available attributes, which include the methods and
            the ontology entities in the namespace.
        """
        entity_autocompletion = self._iter_labels() \
            if self.ontology.reference_style else self._iter_suffixes()
        return itertools.chain(dir(super()), entity_autocompletion)

    def __hash__(self) -> int:
        """Compute a hash value."""
        # TODO: the session can be changed, should the namespace be hashable?
        return hash(self.iri)

    def get(self, name: str, default: Optional[Any] = None) -> OntologyEntity:
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

    def get_from_iri(self, iri: Union[str, URIRef]) -> 'OntologyEntity':
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

    def get_from_suffix(self, suffix: str, case_sensitive: bool = False) -> \
            'OntologyEntity':
        """Get an ontology entity from its namespace suffix.

        Args:
            suffix: Suffix of the ontology entity.
            case_sensitive: Whether to search also for the same suffix with
                different capitalization. By default, such a search is
                performed.
        """
        iri = URIRef(str(self._iri) + suffix)
        try:
            return self.get_from_iri(iri)
        except KeyError as e:
            if not case_sensitive:
                return self._get_case_insensitive(suffix,
                                                  self.get_from_suffix)
            raise e

    def get_from_label(self,
                       label: str,
                       lang: Optional[str] = None,
                       case_sensitive: bool = False) -> 'OntologyEntity':
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
        results = []
        for identifier in self.ontology.iter_identifiers():
            entity_labels = self.ontology.iter_labels(identifier,
                                                      lang=lang,
                                                      return_literal=True)
            if case_sensitive is False:
                entity_labels = (Literal(label.lower(),
                                         lang=label.lang,
                                         datatype=label.datatype)
                                 for label in entity_labels)
                comp_label = label.lower()
            else:
                comp_label = label
            if comp_label in entity_labels:
                results.append(self.get_from_iri(identifier))
        if len(results) == 0:
            error = "No element with label %s was found in namespace %s."\
                    % (label, self)
            raise KeyError(error)
        elif len(results) >= 2:
            element_suffixes = (r.iri[len(self.iri):] for r in results)
            error = (f"There are multiple elements "
                     f"({', '.join(element_suffixes)}) with label"
                     f" {label} for namespace {self}."
                     f"\n"
                     f"Please refer to a specific element of the "
                     f"list by calling get_from_iri(IRI) for "
                     f"namespace {self} for one of the following "
                     f"IRIs: " + "{iris}.")\
                .format(iris=', '.join(entity.iri for entity in results))
            raise KeyError(error)
        return results[0]

    def _iter_labels(self) -> Iterator[str]:
        """Iterate over the labels of the ontology entities in the namespace.

        Returns:
            An iterator of strings containing the labels.
        """
        return itertools.chain(*(self.session.iter_labels(iri,
                                                          return_literal=False)
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

    def __contains__(self, item: Union['OntologyEntity', Identifier]) -> bool:
        """Check whether the given entity is part of the namespace.

        Args:
            item: An ontology entity or identifier.

        Returns:
            Whether the given entity name or IRI is part of the namespace.
            Blank nodes are never part of a namespace.
        """
        from osp.core.ontology.entity import OntologyEntity

        if not isinstance(item, (rdflib.URIRef, rdflib.BNode)):
            raise TypeError(f'in {type(self)} requires, '
                            f'{Identifier} or  {OntologyEntity} as left '
                            f'operand, not {type(item)}.')

        if isinstance(item, BNode):
            return False
        elif isinstance(item, URIRef):
            return str(item).startswith(self.iri)
        elif isinstance(item, Identifier):
            return item in self._iter_identifiers()
        elif isinstance(item, OntologyEntity) and item.session is self.ontology:
            if isinstance(item.identifier, BNode):
                return item.identifier in self._iter_identifiers()
            else:
                return item.identifier in self
        else:
            return False

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
        alternative = alt(name, self._name == "cuba")
        if alternative is None:
            raise KeyError(
                f"Unknown entity '{name}' in namespace {self._name}."
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
                f"Unknown entity '{name}' in namespace {self._name}. "
                f"For backwards compatibility reasons we also "
                f"looked for {alternative} and failed."
            ) from exception
        return r

    # Backwards compatibility.
    # ↑----------------------↑
