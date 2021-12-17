"""A class defined in the ontology."""

import logging
from functools import lru_cache
from typing import Any, Dict, Iterable, Iterator, Optional, Set, Tuple, \
    TYPE_CHECKING, Union
from uuid import UUID

from rdflib import OWL, RDFS, RDF, BNode, URIRef
from rdflib.term import Identifier

from osp.core.ontology.entity import OntologyEntity
from osp.core.utils.cuba_namespace import cuba_namespace
from osp.core.utils.datatypes import AttributeValue, Triple, UID

if TYPE_CHECKING:
    from osp.core.ontology.attribute import OntologyAttribute
    from osp.core.ontology.oclass_restriction import Restriction
    from osp.core.session.session import Session

logger = logging.getLogger(__name__)

BLACKLIST = {OWL.Nothing, OWL.Thing,
             OWL.NamedIndividual}


class OntologyClass(OntologyEntity):
    """A class defined in the ontology."""

    rdf_type = {OWL.Class, RDFS.Class}
    rdf_identifier = URIRef

    def __init__(self,
                 uid: UID,
                 session: Optional['Session'] = None,
                 triples: Optional[Iterable[Triple]] = None,
                 merge: bool = False,
                 ) -> None:
        """Initialize the ontology class.

        Args:
            uid: UID identifying the ontology class.
            session: Session where the entity is stored.
            triples: Construct the class with the provided triples.
            merge: Whether overwrite the potentially existing entity in the
                session with the provided triples or just merge them with
                the existing ones.
        """
        super().__init__(uid, session, triples, merge=merge)
        logger.debug("Instantiated ontology class %s" % self)

    @property
    def attributes(self) -> Dict['OntologyAttribute', Set[Any]]:
        """Get the class attributes.

        Non-mandatory attributes or attributes without a default value will
        not be returned. Mandatory attributes without a default value will
        have None as value.

        Returns:
            The resulting attributes.
        """
        attributes = self.attribute_declaration
        result = dict()
        for attribute, (default, mandatory) \
                in self.attribute_declaration.items():
            if default is not None or mandatory:
                attributes[attribute] = default
        return result

    @property
    @lru_cache(maxsize=None)
    def axioms(self) -> Tuple['Restriction']:
        """Get all the axioms for the ontology class.

        Include axioms of superclasses.

        Returns:
            Tuple of axioms for the ontology class.
        """
        axioms = tuple()
        for superclass in self.superclasses:
            axioms += self._compute_axioms(
                superclass.identifier, RDFS.subClassOf)
            axioms += self._compute_axioms(
                superclass.identifier, OWL.equivalentClass)
        return tuple(axioms)

    def _compute_axioms(self,
                        identifier: Identifier,
                        predicate: URIRef) -> Tuple['Restriction']:
        """Compute the axioms for the class with the given identifier.

        Does not include superclasses.

        Args:
            identifier: The IRI of the class.
            predicate: The predicate to which the class is connected to
                axioms (subclass or equivalentClass).

        Returns:
            Tuple of computed axioms.
        """
        axioms = tuple()
        for o in self.session.graph.objects(identifier, predicate):
            if not isinstance(o, BNode):
                continue
            try:
                axioms += (self.session.from_identifier(o), )
            except KeyError:
                pass
        return axioms

    @property
    def attribute_declaration(self) -> Dict['OntologyAttribute',
                                            Tuple[Optional[AttributeValue],
                                                  bool]]:
        """Get the attributes of this ontology class, and their settings.

        Returns:
            Mapping from attributes to default attribute values and whether
            they are mandatory or not.
        """
        attributes = self._direct_attributes
        for superclass in self.direct_superclasses:
            for attribute, (new_default, new_mandatory) in \
                    superclass.attribute_declaration.items():
                default, mandatory = attributes.get(attribute, (None, False))
                default, mandatory = default or new_default, \
                    False if default or new_default else \
                    mandatory or new_mandatory
                attributes[attribute] = default, mandatory
        return attributes

    @property
    def _direct_attributes(self) -> Dict['OntologyAttribute',
                                         Tuple[Optional[AttributeValue],
                                               bool]]:
        """Get the non-inherited attributes of this ontology class.

        Returns:
            Mapping from attributes to a tuple indicating:
            - default value of the attribute,
            - whether the attribute is mandatory or not,
            - IRI of the attribute datatype.
        """
        identifier = self.identifier
        graph = self.session.graph
        attributes = dict()

        # Case 1: class is part of the domain of a DatatypeProperty.
        blacklist = [OWL.topDataProperty, OWL.bottomDataProperty]
        for s in graph.subjects(RDFS.domain, self.identifier):
            if (s, RDF.type, OWL.DatatypeProperty) not in graph\
                    or s in blacklist:
                continue
            attribute = self.session.from_identifier(s)
            default = self._get_default_python_object(attribute)
            attributes[attribute] = (default, False)

        # Case 2: from axioms.
        for r in graph.objects(identifier, RDFS.subClassOf):
            # Must be a restriction.
            if (r, RDF.type, OWL.Restriction) not in graph:
                continue

            # Must the property must be a DatatypeProperty.
            a = graph.value(r, OWL.onProperty)
            if (a, RDF.type, OWL.DatatypeProperty) not in graph:
                continue

            attribute = self.session.from_identifier(a)
            cuba_default = self._get_default_python_object(attribute)

            # TODO: Move restriction default and obligatory logic to
            #  restriction class?
            # restriction = self.session.from_identifier(r)
            restriction_default = graph.value(r, OWL.hasValue)
            obligatory = any((
                self.session.graph.value(r, OWL.someValuesFrom),
                self.session.graph.value(r, OWL.allValuesFrom),
                self.session.graph.value(r, OWL.hasValue),
                self.session.graph.value(r, OWL.cardinality) != 0,
                self.session.graph.value(r, OWL.minCardinality != 0)
            ))

            default = cuba_default or restriction_default
            obligatory = default is None and obligatory

            attributes[attribute] = (default, obligatory)

        # TODO more cases
        return attributes

    def _get_default_python_object(self,
                                   attribute: "OntologyAttribute") \
            -> AttributeValue:
        """Get the default python object for the given attribute.

        Args:
            attribute: The attribute.

        Returns:
            The default python object.
        """
        for bnode in self.session.ontology_graph.objects(
                self.iri, cuba_namespace._default):
            if (bnode, cuba_namespace._default_attribute, attribute.iri) in \
                    self.session.graph:
                literal = self.session.ontology_graph.value(
                    bnode, cuba_namespace._default_value)
                return attribute.convert_to_datatype(literal) \
                    if literal is not None \
                    else None

    def _get_direct_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct superclasses of this ontology class.

        Returns:
            The direct superclasses.
        """
        return filter(lambda x: isinstance(x, OntologyClass),
                      (self.session.from_identifier(o)
                       for o in self.session.graph.objects(self.iri,
                                                           RDFS.subClassOf))
                      )

    def _get_direct_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the direct subclasses of this ontology class.

        Returns:
            The direct subclasses.
        """
        return filter(lambda x: isinstance(x, OntologyClass),
                      (self.session.from_identifier(s) for s in
                       self.session.graph.subjects(RDFS.subClassOf, self.iri))
                      )

    def _get_superclasses(self) -> Iterator[OntologyEntity]:
        """Get all the superclasses of this ontology class.

        Yields:
            The superclasses.
        """
        yield self

        def closure(node, graph):
            for o in graph.objects(node, RDFS.subClassOf):
                yield o

        yield from filter(lambda x: isinstance(x, OntologyClass),
                          (self.session.from_identifier(x)
                           for x in
                           self.session.graph.transitiveClosure(
                               closure, self.identifier))
                          )

    def _get_subclasses(self) -> Iterator[OntologyEntity]:
        """Get all the subclasses of this ontology class.

        Yields:
            The subclasses.
        """
        yield self

        def closure(node, graph):
            for s in graph.subjects(RDFS.subClassOf, node):
                yield s

        yield from filter(lambda x: isinstance(x, OntologyClass),
                          (self.session.from_identifier(x)
                           for x in
                           self.session.graph.transitiveClosure(
                               closure, self.identifier))
                          )

    def _kwargs_to_attributes(self,
                              kwargs,
                              _skip_checks: bool) -> Dict["OntologyAttribute",
                                                          Set[Any]]:
        """Combine class attributes with the ones from the given kwargs.

        Args:
            kwargs: The user specified keyword arguments.
            _skip_checks: When true, allow mandatory attributes to be left
                undefined.

        Raises:
            TypeError: Unexpected keyword argument.
            TypeError: Missing keyword argument.

        Returns:
            The resulting mixture.
        """
        kwargs = dict(kwargs)
        attributes = dict()
        for attribute, (default, obligatory) \
                in self.attribute_declaration.items():
            if attribute.label is not None \
                    and attribute.label in kwargs:
                attributes[attribute] = kwargs[attribute.label]
                del kwargs[attribute.label]
            elif not _skip_checks and obligatory:
                raise TypeError("Missing keyword argument: %s" %
                                attribute.label)
            elif default is not None:
                attributes[attribute] = default
            else:
                continue

            # Turn attribute into a mutable sequence.
            if not isinstance(attributes[attribute], Set):
                attributes[attribute] = [attributes[attribute]]
            else:
                attributes[attribute] = list(attributes[attribute])

            # Set the appropriate hashable data type for the arguments.
            for i, value in enumerate(attributes[attribute]):
                attributes[attribute][i] = attribute.convert_to_datatype(value)

        # Check validity of arguments
        if not _skip_checks and kwargs:
            raise TypeError("Unexpected keyword arguments: %s"
                            % kwargs.keys())
        return attributes

    def __call__(self,
                 session=None,
                 iri: Optional[Union[URIRef, str, UID]] = None,
                 uid: Optional[Union[UUID, str, UID]] = None,
                 _force: bool = False,
                 **kwargs):
        """Create an OntologyIndividual object from this ontology class.

        Args:
            uid: The identifier of the Cuds object. Should be set to None in
                most cases. Then a new identifier is generated, defaults to
                None. Defaults to None.
            iri: The same as the uid, but exclusively for IRI identifiers.
            session (Session, optional): The session to create the cuds object
                in, defaults to None. Defaults to None.
            _force: Skip validity checks. Defaults to False.

        Raises:
            TypeError: Error occurred during instantiation.

        Returns:
            Cuds, The created cuds object
        """
        # TODO: Create ontology individuals, NOT CUDS objects.
        if None not in (uid, iri):
            raise ValueError("Tried to initialize a CUDS object specifying, "
                             "both its IRI and UID. A CUDS object is "
                             "constrained to have just one UID.")
        elif uid is not None and not isinstance(uid, (UUID, int, UID)):
            raise ValueError('Provide either a UUID or a URIRef object '
                             'as UID.')
            # NOTE: The error message is not wrong, the user is not meant to
            #  provide a UID object, only OSP-core itself.
        elif iri is not None and not isinstance(iri, (URIRef, str, UID)):
            raise ValueError('Provide either a string or an URIRef object as '
                             'IRI.')
            # NOTE: The error message is not wrong, the user is not meant to
            #  provide a UID object, only OSP-core itself.
        else:
            uid = (UID(uid) if uid else None) or \
                (UID(iri) if iri else None) or \
                UID()

        from osp.core.namespaces import cuba
        from osp.core.ontology.individual import OntologyIndividual

        if self.is_subclass_of(cuba.Nothing):
            raise TypeError("Cannot instantiate cuds object for ontology class"
                            " cuba.Nothing.")

        if self.is_subclass_of(cuba.Container):
            from osp.core.ontology.interactive.container import Container
            result = Container(uid=uid,
                               session=session,
                               attributes=self._kwargs_to_attributes(
                                   kwargs, _skip_checks=_force),
                               )
            return result
        elif self.is_subclass_of(cuba.File):
            from osp.core.ontology.interactive.file import File
            path = kwargs.get('path', None)
            if 'path' in kwargs:
                del kwargs['path']
            result = File(uid=uid,
                          session=session,
                          attributes=self._kwargs_to_attributes(
                              kwargs, _skip_checks=_force),
                          )
            result[cuba.path] = path
            return result
        # TODO: Multiclass individuals.

        # build attributes dictionary by combining
        # kwargs and defaults
        return OntologyIndividual(
            uid=uid,
            session=session,
            class_=self,
            attributes=self._kwargs_to_attributes(kwargs, _skip_checks=_force),
        )
