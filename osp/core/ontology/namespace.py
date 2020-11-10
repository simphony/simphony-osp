"""A namespace in the ontology."""


import rdflib
import logging

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
        """Get an ontology entity from the registry by name.

        Args:
            name (str): The name of the ontology entity

        Raises:
            AttributeError: Unknown name.

        Returns:
            OntologyEntity: The ontology entity
        """
        try:
            return self._get(name)
        except KeyError as e:
            raise AttributeError(str(e)) from e

    def __getitem__(self, label):
        """Get an ontology entity from the registry by label.

        Args:
            label (str): The label of the ontology entity.

        Raises:
            KeyError: Unknown label.

        Returns:
            OntologyEntity: The ontology entity.
        """
        if isinstance(label, str):
            label = rdflib.term.Literal(label, lang="en")
        if isinstance(label, tuple):
            label = rdflib.term.Literal(label[0], lang=label[1])
        result = list()
        pattern = (None, rdflib.SKOS.prefLabel, label)
        for s, p, o in self._graph.triples(pattern):
            if str(s).startswith(self._iri):  # TODO more efficient
                name = str(s)[len(self._iri):]
                result.append(
                    self._get(str(label) if self._reference_by_label else name,
                              _case_sensitive=True, _force_by_iri=name))
        if not result:
            raise KeyError("No element with label %s in namespace %s"
                           % (label, self))
        return result

    def get(self, name, fallback=None):
        """Get an ontology entity from the registry by name.

        Args:
            name (str): The name of the ontology entity.
            default (Any): The value to return if it doesn't exist.
            fallback (Any): The fallback value, defaults to None..

        Returns:
            OntologyEntity: The ontology entity

        """
        try:
            return self._get(name)
        except KeyError:
            return fallback

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
        try:
            return self._do_get(name, _case_sensitive, _force_by_iri)
        except KeyError as e:
            if name and name.startswith("INVERSE_OF_"):
                return self._do_get(name[11:], _case_sensitive,
                                    _force_by_iri).inverse
            raise e

    def _do_get(self, name, _case_sensitive, _force_by_iri):
        """Get an ontology entity from the registry by name.

        Args:
            name(str): The name of the ontology entity
            _case_sensitive: Name should be case sensitive,
            _force_by_iri: Name is IRI suffix,

        Returns:
            OntologyEntity: The ontology entity

        """
        if self._reference_by_label and not _force_by_iri:
            return self[name][0]
        iri_suffix = name if not _force_by_iri else _force_by_iri
        iri = rdflib.URIRef(str(self._iri) + iri_suffix)
        try:
            return self._namespace_registry.from_iri(iri, _name=name)
        except KeyError as e:
            if not _case_sensitive:
                return self._get_case_insensitive(name)
            raise e

    def _get_case_insensitive(self, name):
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
        try:
            r = self._get(alternative, _case_sensitive=True)
            logger.warning(
                f"{alternative} is referenced with '{name}'. "
                f"Note that referencing entities will be case sensitive "
                f"in future releases. Additionally, entity names defined "
                f"in YAML ontology are no longer required to be ALL_CAPS. "
                f"You can use the yaml2camelcase "
                f"commandline tool to transform entity names to CamelCase."
            )
            return r
        except KeyError as e:
            raise KeyError(
                f"Unknown entity '{name}' in namespace {self._name}. "
                f"For backwards compatibility reasons we also "
                f"looked for {alternative} and failed."
            ) from e

    def __iter__(self):
        """Iterate over the ontology entities in the namespace.

        :return: An iterator over the entities.
        :rtype: Iterator[OntologyEntity]
        """
        types = [rdflib.OWL.DatatypeProperty,
                 rdflib.OWL.ObjectProperty,
                 rdflib.OWL.Class]
        for t in types:
            for s, _, _ in self._graph.triples((None, rdflib.RDF.type, t)):
                if str(s).startswith(str(self._iri)):
                    iri_suffix = str(s)[len(str(self._iri)):]
                    yield self._get(name=None, _force_by_iri=iri_suffix)

    def __contains__(self, name):
        """Check whether the given entity name is part of the namespace.

        Args:
            name (str): The name of an entity.

        Returns:
            bool: Whether the given entity name is part of the namespace.
        """
        return bool(self._get(name))
