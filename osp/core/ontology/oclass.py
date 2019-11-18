# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.value import OntologyValue
import warnings


CONFLICTING = "2L4N4lGLYBU8mBNx8H6X6dC6Mcf2AcBqIKnFnXUI"


class OntologyClass(OntologyEntity):
    def __init__(self, namespace, name, superclasses, description):
        super().__init__(namespace, name, superclasses, description)
        self._attributes = dict()

    @property
    def attributes(self):
        """Get all (inherited + own) the attributes of this Cuds object.

        :return: Mapping from attributes of the class to the default
        :rtype: Dict[OntologyValue, str]
        """
        result = self._get_attributes_recursively()
        conflicting = [v for v in result.values() if v == CONFLICTING]
        if conflicting:
            result = {k: (v if v != CONFLICTING else None)
                      for k, v in result.items()}
            warnings.warn("Conflicting defaults for %s in %s."
                          % (conflicting, self))
        return {k: v for k, v in result.items() if k not in conflicting}

    @property
    def own_attributes(self):
        """Get all the own attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        return self._attributes

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
        :type attribute: OntologyValue
        """
        assert isinstance(attribute, OntologyValue)
        self._attributes[attribute] = default

    def _get_attributes(self, kwargs):
        """Get the cuds object's attributes from the given kwargs.
        Combine defaults and given attribute attributes

        :param kwargs: The user specified keyword arguments
        :type kwargs: Dict{str, Any}
        :raises TypeError: Unexpected keyword argument
        :raises TypeError: Missing keword argument
        :return: The resulting attributes
        :rtype: Dict[OntologyValue, Any]
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
        if kwargs:
            raise TypeError("Unexpected keyword arguments: %s" % kwargs.keys())
        missing = [k.argname for k, v in attributes.items() if v is None]
        if missing:
            raise TypeError("Missing keyword arguments: %s" % missing)
        return attributes

    def __call__(self, uid=None, session=None, **kwargs):
        from osp.core.cuds import Cuds
        from osp.core import CUBA

        if self.is_subclass_of(CUBA.WRAPPER) and session is None:
            raise TypeError("Missing keyword argument 'session' for wrapper.")

        if self.is_subclass_of(CUBA.NOTHING):
            raise TypeError("Cannot instantiate cuds object for ontology class"
                            " CUBA.NOTHING.")

        # build attributes dictionary by combining
        # kwargs and defaults
        return Cuds(attributes=self._get_attributes(kwargs),
                    oclass=self,
                    session=session,
                    uid=uid)
