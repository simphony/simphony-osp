# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import ABC, abstractmethod
import rdflib
import logging

logger = logging.getLogger(__name__)


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, namespace, name):
        """Initialise the ontology entity

        :param namespace: The namespace of the entity
        :type namespace: OntologyNamespace
        :param name: The name of the entity
        :type name: str
        """
        self._name = name
        self._namespace = namespace

    def __str__(self):
        return "%s.%s" % (self.namespace.name, self._name)

    def __repr__(self):
        return "<%s %s.%s>" % (
            self.__class__.__name__,
            self.namespace.name,
            self._name
        )

    def __eq__(self, other):
        return self.iri == other.iri and self._namespace is other._namespace

    @property
    def name(self):
        """Get the name of the entity"""
        return self._name

    @property
    def iri(self):
        """Get the IRI of the Entity"""
        return rdflib.URIRef(self._namespace.name + self.name)

    @property
    def tblname(self):
        return "%s___%s" % (self.namespace.name, self._name)

    @property
    def namespace(self):
        """Get the name of the entity"""
        return self._namespace

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity

        :return: The direct superclasses of the entity
        :rtype: List[OntologyEntity]
        """
        pattern = (self.iri, rdflib.RDF.subClassOf, None)
        for s, p, o in self.namespace.graph.triples(pattern):
            if isinstance(o, rdflib.URIRef):
                yield self._create_entity(o)

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity

        :return: The direct subclasses of the entity
        :rtype: Set[OntologyEntity]
        """
        pattern = (rdflib.RDF.subClassOf, None, self.iri)
        for s, p, o in self.namespace.graph.triples(pattern):
            if isinstance(o, rdflib.URIRef):
                yield self._create_entity(o)

    # @property
    # def subclasses(self):  TODO
    #     """Get the subclasses of the entity

    #     :return: The direct subclasses of the entity
    #     :rtype: Set[OntologyEntity]
    #     """
    #     subclasses = [self]
    #     for p in self._subclasses:
    #         subclasses.extend(p.subclasses)
    #     result = list()
    #     for i, p in enumerate(subclasses):
    #         if p not in result:
    #             result.append(p)
    #     return result

    # @property
    # def superclasses(self):  TODO
    #     """Get the superclass of the entity

    #     :return: The direct superclasses of the entity
    #     :rtype: Set[OntologyEntity]
    #     """
    #     superclasses = [self]
    #     for p in self._superclasses:
    #         superclasses.extend(p.superclasses)
    #     result = list()
    #     for i, p in enumerate(superclasses):
    #         if p not in superclasses[i + 1:]:
    #             result.append(p)
    #     return result

    # @property  TODO
    # def description(self):
    #     """Get the description of the entity

    #     :return: The description of the entity
    #     :rtype: str
    #     """
    #     if self._description:
    #         return self._description
    #     return "To Be Determined"

    # def is_subclass_of(self, other):  TODO
    #     """Subclass check.

    #     :param other: Check if self is a subclass of this entity.
    #     :type other: OntologyEntity
    #     :return: Whether self is a subclass of other.
    #     :rtype: bool
    #     """
    #     return self in other.subclasses

    # def is_superclass_of(self, other):  TODO
    #     """Superclass check.

    #     :param other: Check if self is a superclass of this entity.
    #     :type other: OntologyEntity
    #     :return: Whether self is a superclass of other.
    #     :rtype: bool
    #     """
    #     return self in other.superclasses

    def get_triples(self):
        """ Get the triples of the entity """
        return self.namespace.graph.triples((self.iri, None, None))

    # def _add_subclass(self, subclass):  TODO for yaml
    #     """Add a subclass to the entity

    #     :param subclass: The subclass to add
    #     :type subclass: OntologyEntity
    #     """
    #     logger.debug("Add subclass %s to %s" % (subclass, self))
    #     if subclass not in self._subclasses:
    #         self._subclasses.append(subclass)

    # def _add_superclass(self, superclass):  TODO for yaml
    #     """Add a superclass to the entity

    #     :param superclass: The superclass to add
    #     :type superclass: OntologyEntity
    #     """
    #     logger.debug("Add superclass %s to %s" % (superclass, self))
    #     if superclass not in self._superclasses:
    #         self._superclasses.append(superclass)

    # def _add_class_expression(self, keyword, class_expression):  TODO
    #     from osp.core.ontology.class_expression import ClassExpression
    #     if not isinstance(class_expression, ClassExpression):
    #         raise ValueError("Tried to add %s as class expression to %s"
    #                          % (class_expression, self))
    #     logger.debug("Add class expression %s for %s to %s"
    #                  % (class_expression, keyword, self))
    #     if keyword not in self._class_expressions:
    #         self._class_expressions[keyword] = list()
    #     self._class_expressions[keyword].append(class_expression)

    # def _collect_class_expressions(self, keyword):  TODO
    #     result = list()
    #     for superclass in self.superclasses:
    #         if keyword in superclass._class_expressions:
    #             result += superclass._class_expressions[keyword]
    #     return result

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

