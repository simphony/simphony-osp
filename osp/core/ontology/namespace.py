"""A namespace in the ontology."""


from collections.abc import Iterable
from functools import lru_cache
import rdflib
import logging

from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.yml.case_insensitivity import \
    get_case_insensitive_alternative as alt

logger = logging.getLogger(__name__)


class OntologyNamespace():
    """A namespace in the ontology."""

    def __init__(self, name, namespace_registry, iri):
        """Initialize the namespace.

        Args:
            name (str): The name of the namespace.
            namespace_registry (OntologyNamespace): The namespace registry.
            iri (rdflib.URIRef): The IRI of the namespace.
        """
        self._name = name
        self._namespace_registry = namespace_registry
        self._iri = rdflib.URIRef(str(iri))
        self._default_rel = -1
        self._reference_by_label = \
            namespace_registry._get_reference_by_label(self._iri)

    def __str__(self):
        """Transform the namespace to a human readable string.

        Returns:
            str: The resulting string.
        """
        return "%s (%s)" % (self._name, self._iri)

    def __repr__(self):
        """Transform the namespace to a string.

        Returns:
            str: The resulting string.
        """
        return "<%s: %s>" % (self._name, self._iri)

    def __eq__(self, other):
        """Check whether the two namespace objects are the same.

        Args:
            other (OntologyNamespace): The namespace to compare with.

        Returns:
            bool: Whether the given namespace is the same.
        """
        return self._name == other._name and self._iri == other._iri \
            and self._namespace_registry is other._namespace_registry

    def __hash__(self):
        """Compute a has value."""
        return hash(str(self))

    def get_name(self):
        """Get the name of the namespace."""
        return self._name

    @property
    def _graph(self):
        """Return the graph of the namespace registry."""
        return self._namespace_registry._graph

    @property
    @lru_cache(maxsize=1024)
    def _label_properties(self):
        """Returns a tuple with the preferred properties to be used as labels.

        Returns (tuple): The properties to be used as labels, ordered by
                         preference.
        """
        defaults = (rdflib.SKOS.prefLabel, rdflib.RDFS.label)
        for s, p, o in self._graph.triples((self._iri,
                                            rdflib_cuba._preferred_label_type,
                                            None)):
            return tuple((o, *(pr for pr in defaults if pr not in (o, ))))
        else:
            return defaults

    def get_default_rel(self):
        """Get the default relationship of the namespace."""
        if self._default_rel == -1:
            self._default_rel = None
            for s, p, o in self._graph.triples((self._iri,
                                                rdflib_cuba._default_rel,
                                                None)):
                self._default_rel = self._namespace_registry.from_iri(o)
        return self._default_rel

    def get_iri(self):
        """Get the IRI of the namespace."""
        return self._iri

    def __getattr__(self, name):
        """Get an ontology entity from the registry by label or suffix.

        Args:
            name (str): The label or namespace suffix of the ontology entity.

        Raises:
            AttributeError: Unknown label or suffix.

        Returns:
            OntologyEntity: The ontology entity.
        """
        if name and name.startswith("INVERSE_OF_"):  # Backwards compatibility
            try:
                return getattr(self, name[11:]).inverse
            except AttributeError:
                pass

        if self._reference_by_label:
            try:
                return self._get_from_label(name)
            except KeyError as e:
                raise AttributeError(str(e)) from e
        else:
            try:
                return self.get_from_suffix(name)
            except KeyError as e:
                raise AttributeError(str(e)) from e

    def __getitem__(self, label):
        """Get an ontology entity from the registry by label.

        Useful for entities whose labels contains characters which are not
        compatible with the Python syntax.

        Args:
            label (str): The label of the ontology entity.

        Raises:
            KeyError: Unknown label.

        Returns:
            OntologyEntity: The ontology entity.
        """
        if type(label) is str:
            lang = None
        elif isinstance(label, Iterable):
            contents = tuple(label)
            if len(contents) == 2:
                label = contents[0]
                lang = contents[1]
        else:
            raise TypeError(f'{type(self).capitalize()} indices must be of '
                            f'type {str} or (label: str, lang: str).')

        return self._get_from_label(label, lang, case_sensitive=True)

    def get(self, name, fallback=None):
        """Get an ontology entity from the registry by suffix or label.

        Args:
            name (str): The label or suffix of the ontology entity.
            default (Any): The value to return if it doesn't exist.
            fallback (Any): The fallback value, defaults to None.

        Returns:
            OntologyEntity: The ontology entity

        """
        try:
            return getattr(self, name)
        except AttributeError:
            return fallback

    def get_from_iri(self, iri, _name=None):
        """Get an ontology entity directly from its IRI.

        For consistency, this method only returns entities from this namespace.

        Args:
            iri (Union[str, rdlib.URIRef]): The iri of the ontology entity.
            _name (str): Not mean to be provided by the user. Just passed to
                        the `from_iri` method of the namespace registry.

        Returns:
            OntologyEntity: The ontology entity.

        Raises:
            KeyError: When the iri does not belong to the namespace.
        """
        if rdflib.URIRef(str(iri)) in self:
            return self._namespace_registry.from_iri(str(iri), _name=_name)
        else:
            raise KeyError(f"The IRI {iri} does not belong to the namespace"
                           f"{self}.")

    def get_from_suffix(self, suffix, case_sensitive=False):
        """Get an ontology entity from its namespace suffix.

        Args:
            suffix (str): Suffix of the ontology entity.
            case_sensitive (bool): Whether to search also for the same suffix
                                   with different capitalization. By default,
                                   such a search is performed.
        """
        iri = rdflib.URIRef(str(self._iri) + suffix)
        try:
            return self.get_from_iri(iri, _name=suffix)
        except KeyError as e:
            if not case_sensitive:
                return self._get_case_insensitive(suffix,
                                                  self.get_from_suffix)
            raise e

    def _get_from_label(self, label, lang=None, case_sensitive=False):
        """Get an ontology entity from the registry by label.

        Args:
            label (str): The label of the ontology entity.

        Raises:
            KeyError: Unknown label.

        Returns:
            OntologyEntity: The ontology entity.
        """
        results = []
        for iri in self._get_namespace_subjects():
            # The method preferredLabel returns a list of tuples where the
            # first element is the kind of label found, and the second the
            # label itself (a rdflib.Literal).
            entity_labels = (label_tuple[1].toPython()
                             for label_tuple in
                             self._graph.preferredLabel(iri, lang=lang,
                                                        labelProperties=self.
                                                        _label_properties)
                             if label_tuple is not None)
            if case_sensitive is False:
                entity_labels = (label.lower() for label in entity_labels)
                comp_label = label.lower()
            else:
                comp_label = label
            if comp_label in entity_labels:
                _name = label if self._reference_by_label else None
                results.append(self.get_from_iri(iri, _name=_name))
        else:
            if len(results) == 0:
                raise KeyError("No element with label %s in namespace %s"
                               % (label, self))
            elif len(results) >= 2:
                raise KeyError(f"There are multiple elements "
                               f"({', '.join(results)}) with label {label} in "
                               f"language {lang} for namespace {self}."
                               f"\n"
                               f"Please refer to a specific element of the "
                               f"list by calling get_from_iri(IRI) for "
                               f"namespace {self} for one of the following "
                               f"IRIs: " + "{iris}."
                               .format(iris=', '.join(entity.iri for entity in
                                                      results)))
            else:
                return results[0]

    def __iter__(self):
        """Iterate over the ontology entities in the namespace.

        :return: An iterator over the entities.
        :rtype: Iterator[OntologyEntity]
        """
        types = [rdflib.OWL.DatatypeProperty,
                 rdflib.OWL.ObjectProperty,
                 rdflib.OWL.Class]
        return (self._namespace_registry.from_iri(s)
                for t in types
                for s, _, _ in self._graph.triples((None, rdflib.RDF.type, t))
                if s in self)

    def __contains__(self, item):
        """Check whether the given entity is part of the namespace.

        Args:
            item (Union[str, rdflib.URIRef, OntologyEntity, rdflib.BNode]):
                    The name, IRI of an entity, the entity itself or a blank
                    node.

        Returns:
            bool: Whether the given entity name or IRI is part of the
                  namespace. Blank nodes are never part of a namespace.
        """
        if type(item) is str:
            iri_suffix = item
            item = rdflib.URIRef(str(self._iri) + iri_suffix)
        elif isinstance(item, OntologyEntity):
            item = item.iri

        if not isinstance(item, (rdflib.URIRef, rdflib.BNode)):
            raise TypeError(f'in {type(self)} requires {str}, '
                            f'{rdflib.URIRef}, {OntologyEntity} or '
                            f'{rdflib.BNode} as left operand, '
                            f'not {type(item)}.')

        if isinstance(item, rdflib.BNode):
            return False
        elif str(item).startswith(self._iri):
            return True
        else:
            return False

    # TODO: Cache or write a more efficient algorithm.
    def _get_namespace_subjects(self, unique=True):
        """Returns all the subjects in the namespace.

        Args:
            unique (bool): When true, does not return duplicates. This is the
                           default option.

        Returns:
            iter: An iterator that goes through all the subjects belonging
                  to the namespace.
        """
        subjects = (subject for subject in self._graph.subjects()
                    if subject in self)
        if unique:
            return set(subjects)
        else:
            return subjects

    # Backwards compatibility.
    # ↓----------------------↓

    def _get(self, name, _case_sensitive=False, _force_by_iri=False):
        """Get an ontology entity from the registry by name.

        Args:
            name(str): The name of the ontology entity
            _case_sensitive(bool): Name should be case sensitive,
                defaults to False
            _force_by_iri(bool):  Name is IRI suffix,
                defaults to False

        Returns:
            OntologyEntity: The ontology entity

        """
        if _force_by_iri is True:
            return self.get_from_suffix(name)
        else:
            return self._get_from_label(name, case_sensitive=_case_sensitive)

    def _get_case_insensitive(self, name, method):
        """Get by trying alternative naming convention of given name.

        Args:
            name(str): The name of the entity.

        Returns:
            OntologyEntity: The Entity to return

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
