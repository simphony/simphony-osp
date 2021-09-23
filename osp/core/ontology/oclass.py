"""A class defined in the ontology."""

import logging
from typing import Any, Dict, List, Optional, Set, Union
from uuid import UUID

from rdflib import OWL, RDFS, RDF, BNode, URIRef

from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.datatypes import UID
from osp.core.ontology.entity import OntologyEntity

logger = logging.getLogger(__name__)

BLACKLIST = {OWL.Nothing, OWL.Thing,
             OWL.NamedIndividual}


class OntologyClass(OntologyEntity):
    """A class defined in the ontology."""

    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        """Initialize the ontology class.

        Args:
            namespace_registry (OntologyNamespaceRegistry): The namespace
                registry where all namespaces are stored.
            namespace_iri (URIRef): The IRI of the namespace.
            name (str): The name of the class.
            iri_suffix (str): namespace_iri +  namespace_registry make up the
                namespace of this entity.
        """
        super().__init__(namespace_registry, namespace_iri, name, iri_suffix)
        logger.debug("Created ontology class %s" % self)
        self._cached_axioms = None

    @property
    def attributes(self):
        """Get all the attributes of this oclass.

        Returns:
            Dict[OntologyAttribute, str]: Mapping from attribute to default
        """
        attributes = dict()
        for superclass in self.superclasses:
            for attr, v in self._get_attributes(superclass.iri).items():
                x = attributes.get(attr, (None, None, None))
                x = (x[0] or v[0], False if x[0] or v[0] else x[1] or v[1],
                     x[2] or v[2])
                attributes[attr] = x
        return attributes

    @property
    def own_attributes(self):
        """Get the non-inherited attributes of this oclass.

        Returns:
            Dict[OntologyAttribute, str]: Mapping from attribute to default
        """
        return self._get_attributes(self.iri)

    @property
    def axioms(self):
        """Get all the axioms for the ontology class.

        Include axioms of superclasses.

        Returns:
            List[Restriction]: The list of axioms for the ontology class.
        """
        if self._cached_axioms is None:
            for superclass in self.superclasses:
                iri = superclass.iri
                self._compute_axioms(iri, RDFS.subClassOf)
                self._compute_axioms(iri, OWL.equivalentClass)
        return self._cached_axioms

    def _compute_axioms(self, iri, rdflib_predicate):
        """Compute the axioms for the class with the given IRI.

        Does not include superclasses.

        Args:
            iri (UriRef): The IRI of the class.
            rdflib_predicate (UriRef): The predicate to which the class is
                connected to axioms (subclass or equivalentClass).
        """
        self._cached_axioms = self._cached_axioms or []
        triple = (iri, rdflib_predicate, None)
        for _, _, o in self.namespace._graph.triples(triple):
            if not isinstance(o, BNode):
                continue
            try:
                self._cached_axioms.append(
                    self._namespace_registry.from_bnode(o)
                )
            except KeyError:
                pass

    def _get_attributes(self, iri):
        """Get the non-inherited attributes of the oclass with the given iri.

        Args:
            iri (URIRef): The iri of the oclass.

        Returns:
            Dict[OntologyAttribute, str]: Mapping from attribute to default
        """
        graph = self._namespace_registry._graph
        attributes = dict()

        blacklist = [OWL.topDataProperty, OWL.bottomDataProperty]
        # Case 1: domain of Datatype
        triple = (None, RDFS.domain, iri)
        for a_iri, _, _ in self.namespace._graph.triples(triple):
            triple = (a_iri, RDF.type, OWL.DatatypeProperty)
            if triple not in graph or isinstance(a_iri, BNode) \
                    or a_iri in blacklist:
                continue
            a = self.namespace._namespace_registry.from_iri(a_iri)
            default = self._get_default(a, iri)
            attributes[a] = (default, False, None)

        # Case 2: axioms
        triple = (iri, RDFS.subClassOf, None)
        for _, _, o in self.namespace._graph.triples(triple):
            if (o, RDF.type, OWL.Restriction) not in graph:
                continue
            a_iri = graph.value(o, OWL.onProperty)
            triple = (a_iri, RDF.type, OWL.DatatypeProperty)
            if triple not in graph or isinstance(a_iri, BNode):
                continue
            a = self.namespace._namespace_registry.from_iri(a_iri)
            cuba_default = self._get_default(a, iri)
            restriction_default = graph.value(o, OWL.hasValue)
            default = cuba_default or restriction_default
            dt, obligatory = self._get_datatype_for_restriction(o)
            obligatory = default is None and obligatory
            attributes[a] = (default, obligatory, dt)

        # TODO more cases
        return attributes

    def _get_datatype_for_restriction(self, r):
        obligatory = False
        dt = None
        g = self.namespace._graph

        dt = g.value(r, OWL.someValuesFrom)
        obligatory = dt is not None
        dt = dt or g.value(r, OWL.allValuesFrom)
        dt = dt or g.value(r, OWL.hasValue)
        obligatory = obligatory or (r, OWL.cardinality) != 0
        obligatory = obligatory or (r, OWL.minCardinality) != 0
        return dt, obligatory

    def _get_default(self,
                     attribute: OntologyAttribute,
                     superclass_iri: URIRef):
        """Get the default of the attribute with the given iri.

        Args:
            attribute_iri: The attribute.
            superclass_iri: IRI of the superclass that defines the default.

        Returns:
            Any: the default
        """
        triple = (superclass_iri, rdflib_cuba._default, None)
        for _, _, bnode in self.namespace._graph.triples(triple):
            x = (bnode, rdflib_cuba._default_attribute, attribute.iri)
            if x in self.namespace._graph:
                in_graph = self.namespace._graph.value(
                    bnode, rdflib_cuba._default_value)
                return attribute.convert_to_datatype(in_graph) \
                    if in_graph is not None \
                    else None

    def get_attribute_by_argname(self, name):
        """Get the attribute object with the argname of the object.

        Args:
            name (str): The argname of the attribute

        Returns:
            OntologyAttribute: The attribute
        """
        for attribute in self.attributes:
            if attribute.argname == name:
                return attribute
            elif attribute.argname.lower() == name:
                logger.warning(
                    f"Attribute {attribute.argname} is referenced "
                    f"with '{attribute.argname.lower()}'. "
                    f"Note that you must match the case of the definition in "
                    f"the ontology in future releases. Additionally, entity "
                    f"names defined in YAML ontology are no longer required "
                    f"to be ALL_CAPS. You can use the yaml2camelcase "
                    f"commandline tool to transform entity names to CamelCase."
                )
                return attribute

    def _get_attributes_values(self,
                               kwargs: Dict[str, Union[Any, Set[Any]]],
                               _force: bool) -> Dict[OntologyAttribute,
                                                     List[Any]]:
        """Get the cuds object's attributes from the given kwargs.

        Combine defaults and given attribute attributes

        Args:
            kwargs: The user specified keyword arguments.
            _force: Skip checks.

        Raises:
            TypeError: Unexpected keyword argument.
            TypeError: Missing keyword argument.

        Returns:
            The resulting attributes.
        """
        kwargs = dict(kwargs)
        attributes = dict()
        for attribute, (default, obligatory, dt) in self.attributes.items():
            if attribute.argname in kwargs:
                attributes[attribute] = kwargs[attribute.argname]
                del kwargs[attribute.argname]
            elif attribute.argname.lower() in kwargs:
                attributes[attribute] = kwargs[attribute.argname.lower()]
                del kwargs[attribute.argname.lower()]
                logger.warning(
                    f"Attribute {attribute.argname} is referenced "
                    f"with '{attribute.argname.lower()}'. "
                    f"Note that you must match the case of the definition in "
                    f"the ontology in future releases. Additionally, entity "
                    f"names defined in YAML ontology are no longer required "
                    f"to be ALL_CAPS. You can use the yaml2camelcase "
                    f"commandline tool to transform entity names to CamelCase."
                )
            elif not _force and obligatory:
                raise TypeError("Missing keyword argument: %s" %
                                attribute.argname)
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
        if not _force and kwargs:
            raise TypeError("Unexpected keyword arguments: %s"
                            % kwargs.keys())
        return attributes

    def _direct_superclasses(self):
        return self._directly_connected(RDFS.subClassOf,
                                        blacklist=BLACKLIST)

    def _direct_subclasses(self):
        return self._directly_connected(RDFS.subClassOf,
                                        inverse=True, blacklist=BLACKLIST)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(
            RDFS.subClassOf,
            blacklist=BLACKLIST)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(
            RDFS.subClassOf, inverse=True,
            blacklist=BLACKLIST)

    def __call__(self,
                 session=None,
                 iri: Optional[Union[URIRef, str, UID]] = None,
                 uid: Optional[Union[UUID, str, UID]] = None,
                 _force: bool = False,
                 **kwargs):
        """Create a Cuds object from this ontology class.

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
        if len(set(filter(lambda x: x is not None, (uid, iri)))) > 1:
            raise ValueError("Tried to initialize a CUDS object specifying, "
                             "both its IRI and UID. A CUDS object is "
                             "constrained to have just one UID.")
        elif uid is not None and not isinstance(uid, (UUID, int, UID)):
            raise ValueError('Provide either a UUID or a URIRef object'
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

        from osp.core.cuds import Cuds
        from osp.core.namespaces import cuba

        if self.is_subclass_of(cuba.Wrapper) and session is None:
            raise TypeError("Missing keyword argument 'session' for wrapper.")

        if self.is_subclass_of(cuba.Nothing):
            raise TypeError("Cannot instantiate cuds object for ontology class"
                            " cuba.Nothing.")

        # build attributes dictionary by combining
        # kwargs and defaults
        return Cuds(
            attributes=self._get_attributes_values(kwargs, _force=_force),
            oclass=self,
            session=session,
            uid=uid
        )
