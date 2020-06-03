
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.class_expression import ClassExpression
import logging
import rdflib

logger = logging.getLogger(__name__)


CONFLICTING = "2L4N4lGLYBU8mBNx8H6X6dC6Mcf2AcBqIKnFnXUI"


class OntologyClass(OntologyEntity, ClassExpression):
    def __init__(self, namespace, name, superclasses, description):
        super().__init__(namespace, name, superclasses, description)
        self._attributes = dict()
        logger.debug("Created ontology class %s" % self)

    @property
    def attributes(self):
        """Get all (inherited + own) the attributes of this Cuds object.

        :return: Mapping from attributes of the class to the default
        :rtype: Dict[OntologyAttribute, str]
        """
        result = self._get_attributes_recursively()
        conflicting = [k for k, v in result.items() if v == CONFLICTING]
        if conflicting:
            result = {k: (v if v != CONFLICTING else None)
                      for k, v in result.items()}
            logger.warning("Conflicting defaults for %s in %s.",
                           conflicting, self)
        return result

    @property
    def own_attributes(self):
        """Get all the own attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyAttribute]
        """
        return self._attributes

    @property
    def subclass_of_expressions(self):
        """Get the subclass_of class expressions"""
        from osp.core.ontology.parser import SUPERCLASSES_KEY
        return self._collect_class_expressions(SUPERCLASSES_KEY)

    @property
    def equivalent_to_expressions(self):
        """Get the subclass_of class expressions"""
        from osp.core.ontology.parser import EQUIVALENT_TO_KEY
        if EQUIVALENT_TO_KEY in self._class_expressions:
            return self._class_expressions[EQUIVALENT_TO_KEY]
        return list()

    @property
    def disjoint_with_expressions(self):
        """Get the subclass_of class expressions"""
        from osp.core.ontology.parser import DISJOINTS_KEY
        return self._collect_class_expressions(DISJOINTS_KEY)

    # OVERRIDE
    def get_triples(self):
        return super().get_triples() + [
            (self.iri, rdflib.RDFS.subClassOf, x.iri)
            for x in self.superclasses
        ] + [
            (self.iri, rdflib.RDF.type, rdflib.OWL.Class),
        ]

    def _get_attributes_recursively(self):
        """Get the attributes and defaults recursively

        """
        result = dict()

        for p in self.direct_superclasses:
            superclass_attributes = p._get_attributes_recursively()
            conflicting = [a for a in superclass_attributes.keys()
                           if a in result   # different defaults
                           and result[a] != superclass_attributes[a]]
            superclass_attributes.update({a: CONFLICTING for a in conflicting})
            result.update(superclass_attributes)

        result.update(self.own_attributes)
        return result

    def _add_attribute(self, attribute, default):
        """Add an attribute to the class

        :param attribute: The attribute to add
        :type attribute: OntologyAttribute
        """
        if not isinstance(attribute, OntologyAttribute):
            raise TypeError("Tried to add non-attribute %s as "
                            "attribute to %s"
                            % (attribute, self))
        logger.debug("Add attribute %s to %s" % (attribute, self))
        self._attributes[attribute] = default

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
        from osp.core import CUBA

        if self.is_subclass_of(CUBA.WRAPPER) and session is None:
            raise TypeError("Missing keyword argument 'session' for wrapper.")

        if self.is_subclass_of(CUBA.NOTHING):
            raise TypeError("Cannot instantiate cuds object for ontology class"
                            " CUBA.NOTHING.")

        # build attributes dictionary by combining
        # kwargs and defaults
        return Cuds(attributes=self._get_attributes_values(kwargs,
                                                           _force=_force),
                    oclass=self,
                    session=session,
                    uid=uid)
