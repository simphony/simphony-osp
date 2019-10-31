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
        self._values = dict()

    @property
    def values(self):
        """Get all (inherited + own) the values of this Cuds object.

        :return: The values of the class
        :rtype: List[OntologyValue]
        """
        result = self.inherited_values
        result.update(self.own_values)
        return result

    @property
    def own_values(self):
        """Get all the own values of this Cuds object.

        :return: The values of the class
        :rtype: List[OntologyValue]
        """
        return self._values

    @property
    def inherited_values(self):
        """Get all the inherited values of this Cuds object.

        :return: The values of the class
        :rtype: List[OntologyValue]
        """
        result = dict()
        superclasses = self.superclasses
        for c in superclasses:
            if c is self:
                continue
            tmp = dict(c.own_values)
            tmp.update(result)
            result = tmp
        return result

    def _add_value(self, value, default):
        """Add an value to the class

        :param value: The value to add
        :type value: OntologyValue
        """
        assert isinstance(value, OntologyValue)
        self._values[value] = default

    def _get_attributes(self, kwargs):
        """Get the cuds object's attributes from the given kwargs.
        Combine defaults and given attribute values

        :param kwargs: The user specified keyword arguments
        :type kwargs: Dict{str, Any}
        :raises TypeError: Unexpected keyword argument
        :raises TypeError: Missing keword argument
        :return: The resulting attributes
        :rtype: Dict[OntologyValue, Any]
        """
        attributes = dict()
        for value, default in self.inherited_values.items():
            if value.argname in kwargs:
                attributes[value] = kwargs[value.argname]
                del kwargs[value.argname]
            else:
                attributes[value] = default

        # Check validity of arguments
        if kwargs:
            raise TypeError("Unexpected keyword arguments: %s" % kwargs.keys())
        missing = [k.argname for k, v in attributes.items() if v is None]
        if missing:
            raise TypeError("Missing keyword arguments: %s" % missing)
        return attributes

    def __call__(self, uid=None, session=None, **kwargs):
        from osp.core.cuds import Cuds

        # build attributes dictionary by combining
        # kwargs and defaults
        return Cuds(attributes=self._get_attributes(kwargs),
                    is_a=self,
                    session=session,
                    uid=uid)
