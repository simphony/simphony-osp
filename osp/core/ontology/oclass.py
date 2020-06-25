# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


from osp.core.ontology.entity import OntologyEntity
import logging
import rdflib

logger = logging.getLogger(__name__)


class OntologyClass(OntologyEntity):
    def __init__(self, namespace, name):
        super().__init__(namespace, name)
        logger.debug("Created ontology class %s" % self)

    @property
    def attributes(self):
        """Get all (inherited + own) the attributes of this Cuds object.

        :return: Mapping from attributes of the class to the default
        :rtype: Dict[OntologyAttribute, str]
        """
        superclasses = self.superclasses
        attributes = set()
        for superclass in superclasses:
            # TODO more cases
            triple = (None, rdflib.RDFS.domain, superclass.iri)
            for s, _, _ in self.namespace._graph.triples(triple):
                triple = (s, rdflib.RDF.type, rdflib.OWL.DatatypeProperty)
                if triple in self._namespace._graph:
                    attributes.add(
                        self.namespace._namespace_registry.from_iri(s)
                    )  # TODO default values
        return attributes

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
        default = None  # TODO
        for attribute in self.attributes:
            if attribute.argname in kwargs:
                attributes[attribute] = kwargs[attribute.argname]
                del kwargs[attribute.argname]
            else:
                attributes[attribute] = default

        # Check validity of arguments
        if not _force:
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
        from osp.core.namespaces import CUBA

        if self.is_subclass_of(CUBA.WRAPPER) and session is None:
            raise TypeError("Missing keyword argument 'session' for wrapper.")

        if self.is_subclass_of(CUBA.NOTHING):
            raise TypeError("Cannot instantiate cuds object for ontology class"
                            " CUBA.NOTHING.")

        # build attributes dictionary by combining
        # kwargs and defaults
        return Cuds(
            attributes=self._get_attributes_values(kwargs, _force=_force),
            oclass=self,
            session=session,
            uid=uid
        )
