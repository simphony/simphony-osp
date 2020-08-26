from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.cuba import rdflib_cuba
import logging
import rdflib

logger = logging.getLogger(__name__)


class OntologyClass(OntologyEntity):
    def __init__(self, namespace_registry, namespace_iri, name, iri_suffix):
        super().__init__(namespace_registry, namespace_iri, name, iri_suffix)
        logger.debug("Created ontology class %s" % self)

    @property
    def attributes(self):
        """Get all the attributes of this oclass

        Returns:
            Dict[OntologyAttribute, str]: Mapping from attribute to default
        """
        attributes = dict()
        for superclass in self.superclasses:
            attributes.update(self._get_attributes(superclass.iri))
        return attributes

    @property
    def own_attributes(self):
        """Get the non-inherited attributes of this oclass

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
        # Case 1: domain of Datatype
        triple = (None, rdflib.RDFS.domain, iri)
        for a_iri, _, _ in self.namespace._graph.triples(triple):
            triple = (a_iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
            if triple in graph \
                    and not isinstance(a_iri, rdflib.BNode):
                a = self._namespace_registry.from_iri(a_iri)
                attributes[a] = self._get_default(a_iri, iri)

        # Case 2: restrictions
        triple = (iri, rdflib.RDFS.subClassOf, None)
        for _, _, o in self.namespace._graph.triples(triple):
            if (o, rdflib.RDF.type, rdflib.OWL.Restriction) in graph:
                a_iri = graph.value(o, rdflib.OWL.onProperty)
                triple = (a_iri, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
                if triple in graph \
                        and not isinstance(a_iri, rdflib.BNode):
                    a = self._namespace_registry.from_iri(a_iri)
                    attributes[a] = self._get_default(a_iri, iri)
        # TODO more cases
        return attributes

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

        :param kwargs: The user specified keyword arguments
        :type kwargs: Dict{str, Any}
        :raises TypeError: Unexpected keyword argument
        :raises TypeError: Missing keword argument
        :return: The resulting attributes
        :rtype: Dict[OntologyAttribute, Any]
        """
        kwargs = dict(kwargs)
        attributes = dict()
        for attribute, default in self.attributes.items():
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
            else:
                attributes[attribute] = default

        # Check validity of arguments
        if _force:
            return {k: v for k, v in attributes.items() if v is not None}
        if kwargs:
            raise TypeError("Unexpected keyword arguments: %s"
                            % kwargs.keys())
        missing = [k.argname for k, v in attributes.items() if v is None]
        if missing:
            raise TypeError("Missing keyword arguments: %s" % missing)
        return attributes

    def _direct_superclasses(self):
        return self._directly_connected(rdflib.RDFS.subClassOf)

    def _direct_subclasses(self):
        return self._directly_connected(rdflib.RDFS.subClassOf, inverse=True)

    def _superclasses(self):
        yield self
        yield from self._transitive_hull(rdflib.RDFS.subClassOf)

    def _subclasses(self):
        yield self
        yield from self._transitive_hull(rdflib.RDFS.subClassOf, inverse=True)

    def __call__(self, uid=None, session=None, _force=False, **kwargs):
        """Create a Cuds object from this ontology class.

        :param uid: The uid of the Cuds object. Should be set to None in most
            cases. Then a new UUID is generated, defaults to None
        :type uid: uuid.UUID, optional
        :param session: The session to create the cuds object in,
            defaults to None
        :type session: Session, optional
        :raises TypeError: Error occurred during instantiation.
        :return: The created cuds object
        :rtype: Cuds
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
