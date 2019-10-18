# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


from cuds.parser.ontology_entity import OntologyEntity


class OntologyClass(OntologyEntity):
    def __init__(self, name, superclasses, definition):
        super().__init__(name, superclasses, definition)
        self._attributes = dict()

    def get_attributes(self):
        """Get all (inherited + own) the attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        result = self.get_inherited_attributes()
        result.update(self.get_own_attributes())
        return result

    def get_own_attributes(self):
        """Get all the own attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        return self._attributes

    def get_inherited_attributes(self):
        """Get all the inherited attributes of this Cuds object.

        :return: The attributes of the class
        :rtype: List[OntologyValue]
        """
        result = dict()
        superclasses = self.get_superclasses()
        for c in superclasses:
            if c is self:
                continue
            result.update(c.get_own_attributes())
        return result

    def _add_attribute(self, attribute, default):
        """Add an attribute to the class

        :param attribute: The attribute to add
        :type attribute: OntologyValue
        """
        self._attributes[attribute] = default
