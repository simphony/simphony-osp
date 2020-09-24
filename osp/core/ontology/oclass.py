"""A class defined in the ontology."""

from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.cuba import rdflib_cuba
import logging
import rdflib

logger = logging.getLogger(__name__)

BLACKLIST = {rdflib.OWL.Nothing, rdflib.OWL.Thing,
             rdflib.OWL.NamedIndividual}


class OntologyClass(OntologyEntity):
    """A class defined in the ontology."""

    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        """Initialize the ontology class.

        Args:
            namespace_registry (OntologyNamespaceRegistry): The namespace
                registry where all namespaces are stored.
            namespace_iri (rdflib.URIRef): The IRI of the namespace.
            name (str): The name of the class.
            iri_suffix (str): namespace_iri +  namespace_registry make up the
                namespace of this entity.
        """
        super().__init__(namespace_registry, namespace_iri, name, iri_suffix)
        logger.debug("Created ontology class %s" % self)

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
                x = (x[0] or v[0], x[1] or v[1], x[2] or v[2])
                attributes[attr] = x
        return attributes

    @property
    def own_attributes(self):
        """Get the non-inherited attributes of this oclass.

        Returns:
            Dict[OntologyAttribute, str]: Mapping from attribute to default
        """
        return self._get_attributes(self.iri)

    def _get_attributes(self, iri):
        """Get the non-inherited attributes of the oclass with the given iri.

        Args:
            iri (URIRef): The iri of the oclass.

        Returns:
            Dict[OntologyAttribute, str]: Mapping from attribute to default
        """
        graph = self._namespace_registry._graph
        attributes = dict()

        blacklist = [rdflib.OWL.topDataProperty, rdflib.OWL.bottomDataProperty]
        # Case 1: domain of Datatype
        triple = (None, rdflib.RDFS.domain, iri)
        for a_iri, _, _ in self.namespace._graph.triples(triple):
            triple = (a_iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
            if triple not in graph or isinstance(a_iri, rdflib.BNode) \
                    or a_iri in blacklist:
                continue
            a = self.namespace._namespace_registry.from_iri(a_iri)
            default = self._get_default(a_iri, iri)
            attributes[a] = (default, False, None)

        # Case 2: restrictions
        triple = (iri, rdflib.RDFS.subClassOf, None)
        for _, _, o in self.namespace._graph.triples(triple):
            if (o, rdflib.RDF.type, rdflib.OWL.Restriction) not in graph:
                continue
            a_iri = graph.value(o, rdflib.OWL.onProperty)
            triple = (a_iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
            if triple not in graph or isinstance(a_iri, rdflib.BNode):
                continue
            a = self.namespace._namespace_registry.from_iri(a_iri)
            default = self._get_default(a_iri, iri)
            dt, obligatory = self._get_datatype_for_restriction(o)
            obligatory = default is None and obligatory
            attributes[a] = (self._get_default(a_iri, iri), obligatory, dt)

        # TODO more cases
        return attributes

    def _get_datatype_for_restriction(self, r):
        obligatory = False
        dt = None
        g = self.namespace._graph

        dt = g.value(r, rdflib.OWL.someValuesFrom)
        obligatory = dt is not None
        dt = dt or g.value(r, rdflib.OWL.allValuesFrom)
        obligatory = obligatory or (r, rdflib.OWL.cardinality) != 0
        obligatory = obligatory or (r, rdflib.OWL.minCardinality) != 0
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
        triple = (superclass_iri, rdflib_cuba._default, None)
        for _, _, bnode in self.namespace._graph.triples(triple):
            x = (bnode, rdflib_cuba._default_attribute, attribute_iri)
            if x in self.namespace._graph:
                return self.namespace._graph.value(bnode,
                                                   rdflib_cuba._default_value)

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

    def _get_attributes_values(self, kwargs, _force):
        """Get the cuds object's attributes from the given kwargs.

        Combine defaults and given attribute attributes

        Args:
            kwargs (dict[str, Any]): The user specified keyword arguments
            _force (bool): Skip checks.

        Raises:
            TypeError:  Unexpected keyword argument.
            TypeError: Missing keword argument.

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
                raise TypeError("Missing keyword argument: %s" %
                                attribute.argname)
            elif default is not None:
                attributes[attribute] = default

        # Check validity of arguments
        if not _force and kwargs:
            raise TypeError("Unexpected keyword arguments: %s"
                            % kwargs.keys())
        return attributes

    def _direct_superclasses(self):
        return self._directly_connected(rdflib.RDFS.subClassOf,
                                        blacklist=BLACKLIST)

    def _direct_subclasses(self):
        return self._directly_connected(rdflib.RDFS.subClassOf,
                                        inverse=True, blacklist=BLACKLIST)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(
            rdflib.RDFS.subClassOf,
            blacklist=BLACKLIST)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(
            rdflib.RDFS.subClassOf, inverse=True,
            blacklist=BLACKLIST)

    def __call__(self, uid=None, session=None, _force=False, **kwargs):
        """Create a Cuds object from this ontology class.

        Args:
            uid (UUID, optional): The uid of the Cuds object.
                Should be set to None in most cases.
                Then a new UUID is generated, defaults to None.
                Defaults to None.
            session (Session, optional): The session to create the cuds object
                in, defaults to None. Defaults to None.
            _force (bool, optional): Skip validity checks. Defaults to False.

        Raises:
            TypeError: Error occurred during instantiation.

        Returns:
            Cuds: The created cuds object
        """
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
