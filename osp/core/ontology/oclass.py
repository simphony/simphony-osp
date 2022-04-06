"""A class defined in the ontology."""

import logging
import uuid

import rdflib
from rdflib import OWL, RDF, RDFS, BNode

from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.entity import OntologyEntity

logger = logging.getLogger(__name__)

BLACKLIST = {OWL.Nothing, OWL.Thing, OWL.NamedIndividual}

# CACHE Introduced because getting URIRef terms from the namespaces is
#  computationally expensive.
CACHE = {
    "cuba:_default": rdflib_cuba._default,
    "cuba:_default_attribute": rdflib_cuba._default_attribute,
    "cuba:_default_value": rdflib_cuba._default_value,
    "owl:DatatypeProperty": OWL.DatatypeProperty,
    "owl:Restriction": OWL.Restriction,
    "owl:allValuesFrom": OWL.allValuesFrom,
    "owl:cardinality": OWL.cardinality,
    "owl:minCardinality": OWL.minCardinality,
    "owl:hasValue": OWL.hasValue,
    "owl:someValuesFrom": OWL.someValuesFrom,
    "owl:onProperty": OWL.onProperty,
    "rdf:type": RDF.type,
    "rdfs:domain": RDFS.domain,
    "rdfs:subClassOf": RDFS.subClassOf,
}


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
            Dict[OntologyAttribute, Any]: Mapping from attribute to default
        """
        attributes = dict()
        for superclass in self.superclasses:
            for attr, v in self._get_attributes(superclass.iri).items():
                x = attributes.get(attr, (None, None, None))
                x = (
                    x[0] or v[0],
                    False if x[0] or v[0] else x[1] or v[1],
                    x[2] or v[2],
                )
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
        for o in self._namespace_registry._graph.objects(
            iri, rdflib_predicate
        ):
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
        attributes = dict()
        # Case 1: domain of Datatype
        for a_iri in self._get_attributes_identifiers_from_domain(iri):
            a = self._namespace_registry.from_iri(a_iri)
            default = self._get_default(a_iri, iri)
            attributes[a] = (default, False, None)

        # Case 2: axioms
        graph = self._namespace_registry._graph
        for a_iri, o in self._get_attributes_identifiers_from_axioms(
            iri, return_restriction=True
        ):
            a = self._namespace_registry.from_iri(a_iri)
            cuba_default = self._get_default(a_iri, iri)
            restriction_default = graph.value(o, CACHE["owl:hasValue"])
            default = cuba_default or restriction_default
            dt, obligatory = self._get_datatype_for_restriction(o)
            obligatory = default is None and obligatory
            attributes[a] = (default, obligatory, dt)

        # TODO more cases
        return attributes

    def _get_attributes_identifiers(self, iri):
        yield from self._get_attributes_identifiers_from_domain(iri)
        yield from self._get_attributes_identifiers_from_axioms(iri)

    def _get_attributes_identifiers_from_domain(self, iri):
        # Case 1: domain of Datatype
        graph = self._namespace_registry._graph
        blacklist = [OWL.topDataProperty, OWL.bottomDataProperty]
        for a_iri in graph.subjects(CACHE["rdfs:domain"], iri):
            if (
                (a_iri, CACHE["rdf:type"], CACHE["owl:DatatypeProperty"])
                not in graph
                or isinstance(a_iri, BNode)
                or a_iri in blacklist
            ):
                continue
            yield a_iri

    def _get_attributes_identifiers_from_axioms(
        self, iri, return_restriction=False
    ):
        # Case 2: axioms
        graph = self._namespace_registry._graph
        for o in graph.objects(iri, CACHE["rdfs:subClassOf"]):
            if (o, CACHE["rdf:type"], CACHE["owl:Restriction"]) not in graph:
                continue
            a_iri = graph.value(o, CACHE["owl:onProperty"])
            if (
                a_iri,
                CACHE["rdf:type"],
                CACHE["owl:DatatypeProperty"],
            ) not in graph or isinstance(a_iri, BNode):
                continue
            yield a_iri if not return_restriction else (a_iri, o)

    def _get_datatype_for_restriction(self, r):
        obligatory = False
        dt = None
        g = self._namespace_registry._graph

        dt = g.value(r, CACHE["owl:someValuesFrom"])
        obligatory = dt is not None
        dt = dt or g.value(r, CACHE["owl:allValuesFrom"])
        dt = dt or g.value(r, CACHE["owl:hasValue"])
        obligatory = obligatory or (r, CACHE["owl:cardinality"]) != 0
        obligatory = obligatory or (r, CACHE["owl:minCardinality"]) != 0
        return dt, obligatory

    def _get_default(self, attribute_iri, superclass_iri):
        """Get the default of the attribute with the given iri.

        Args:
            attribute_iri (URIRef): IRI of the attribute
            superclass_iri (URIRef): IRI of the superclass that defines
                the default.

        Returns:
            Any: the default
        """
        for bnode in self._namespace_registry._graph.objects(
            superclass_iri, CACHE["cuba:_default"]
        ):
            x = (bnode, CACHE["cuba:_default_attribute"], attribute_iri)
            if x in self._namespace_registry._graph:
                return self._namespace_registry._graph.value(
                    bnode, CACHE["cuba:_default_value"]
                )

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

    def get_attribute_identifier_by_argname(self, name):
        """Get the attribute identifier with the argname of the object.

        Args:
            name (str): The argname of the attribute

        Returns:
            Identifier: The attribute identifier.
        """
        for superclass in self.superclasses:
            for identifier in self._get_attributes_identifiers(superclass.iri):
                attribute_name = self._namespace_registry._get_entity_name(
                    identifier,
                    self._namespace_registry._get_namespace_name_and_iri(
                        identifier
                    )[1],
                )
                if attribute_name == name:
                    return identifier
                elif attribute_name.lower() == name:
                    logger.warning(
                        f"Attribute {attribute_name} is referenced "
                        f"with '{attribute_name.lower()}'. "
                        f"Note that you must match the case of the definition "
                        f"in the ontology in future releases. Additionally, "
                        f"entity names defined in YAML ontology are no longer "
                        f"required to be ALL_CAPS. You can use the "
                        f"yaml2camelcase commandline tool to transform entity "
                        f"names to CamelCase."
                    )
                    return identifier

    def _get_attributes_values(self, kwargs, _force):
        """Get the cuds object's attributes from the given kwargs.

        Combine defaults and given attribute attributes

        Args:
            kwargs (dict[str, Any]): The user specified keyword arguments
            _force (bool): Skip checks.

        Raises:
            TypeError: Unexpected keyword argument.
            TypeError: Missing keyword argument.

        Returns:
            [Dict[OntologyAttribute, Any]]: The resulting attributes.
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
                raise TypeError(
                    "Missing keyword argument: %s" % attribute.argname
                )
            elif default is not None:
                attributes[attribute] = default

        # Check validity of arguments
        if not _force and kwargs:
            raise TypeError("Unexpected keyword arguments: %s" % kwargs.keys())
        return attributes

    def _direct_superclasses(self):
        return self._directly_connected(RDFS.subClassOf, blacklist=BLACKLIST)

    def _direct_subclasses(self):
        return self._directly_connected(
            RDFS.subClassOf, inverse=True, blacklist=BLACKLIST
        )

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(RDFS.subClassOf, blacklist=BLACKLIST)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(
            RDFS.subClassOf, inverse=True, blacklist=BLACKLIST
        )

    def __call__(
        self, session=None, iri=None, uid=None, _force=False, **kwargs
    ):
        """Create a Cuds object from this ontology class.

        Args:
            uid (Union[UUID, int], optional): The identifier of the
                Cuds object. Should be set to None in most cases. Then a new
                identifier is generated, defaults to None. Defaults to None.
            iri (Union[URIRef, str], optional): The same as the uid, but
                exclusively for IRI identifiers.
            session (Session, optional): The session to create the cuds object
                in, defaults to None. Defaults to None.
            _force (bool, optional): Skip validity checks. Defaults to False.

        Raises:
            TypeError: Error occurred during instantiation.

        Returns:
            Cuds: The created cuds object
        """
        # Accept strings as IRI identifiers and integers as UUID identifiers.
        types_map = {
            int: lambda x: uuid.UUID(int=x),
            str: lambda x: rdflib.URIRef(x),
            rdflib.URIRef: lambda x: x,
            uuid.UUID: lambda x: x,
            type(None): lambda x: x,
        }
        iri, uid = (types_map[type(x)](x) for x in (iri, uid))

        from osp.core.cuds import Cuds
        from osp.core.namespaces import cuba

        if self.is_subclass_of(cuba.Wrapper) and session is None:
            raise TypeError("Missing keyword argument 'session' for wrapper.")

        if self.is_subclass_of(cuba.Nothing):
            raise TypeError(
                "Cannot instantiate cuds object for ontology class"
                " cuba.Nothing."
            )

        # build attributes dictionary by combining
        # kwargs and defaults
        return Cuds(
            attributes=self._get_attributes_values(kwargs, _force=_force),
            oclass=self,
            session=session,
            iri=iri,
            uid=uid,
        )
