# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.value import OntologyValue


class OntologyClass(OntologyEntity):
    def __init__(self, namespace, name, superclasses, definition):
        super().__init__(namespace, name, superclasses, definition)
        self._attributes = dict()

    @property
    def attributes(self):
        """Get all (inherited + own) the attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        result = self.inherited_attributes
        result.update(self.own_attributes)
        return result

    @property
    def own_attributes(self):
        """Get all the own attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        return self._attributes

    @property
    def inherited_attributes(self):
        """Get all the inherited attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        result = dict()
        superclasses = self.superclasses
        for c in superclasses:
            if c is self:
                continue
            tmp = dict(c.own_attributes)
            tmp.update(result)
            result = tmp
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

        # build attributes dictionary by combining
        # kwargs and defaults
        if self in CUBA.WRAPPER.subclasses and session is None:
            raise TypeError("Missing keyword argument 'session' for wrapper.")
        return Cuds(attributes=self._get_attributes(kwargs),
                    is_a=self,
                    session=session,
                    uid=uid)
