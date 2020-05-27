from abc import ABC, abstractmethod
import rdflib
import logging

logger = logging.getLogger(__name__)


class OntologyEntity(ABC):
    @abstractmethod
    def __init__(self, namespace, name, superclasses, description):
        """Initialize the ontology entity.

        Args:
            namespace (OntologyNamespace): The namespace of the entity
            name (str): The name of the entity
            superclasses (List[OntologyEntity]): The superclasses of the entity
            description (str): The defintion of the entity
        """
        self._name = name
        self._namespace = namespace
        self._subclasses = list()
        self._superclasses = list(superclasses)
        self._description = description
        self._class_expressions = dict()

        from osp.core import ONTOLOGY_INSTALLER
        assert (
            namespace.name not in ONTOLOGY_INSTALLER.namespace_registry
            or name not in
            ONTOLOGY_INSTALLER.namespace_registry[namespace.name]
        )

    def __str__(self):
        return "%s.%s" % (self.namespace.name, self._name)

    def __repr__(self):
        return "<%s %s.%s>" % (
            self.__class__.__name__,
            self.namespace.name,
            self._name
        )

    @property
    def name(self):
        """Get the name of the entity"""
        return self._name

    @property
    def iri(self):
        """Get the IRI of the Entity"""
        from osp.core import IRI_DOMAIN
        return rdflib.URIRef(IRI_DOMAIN + "/%s#%s" % (self._namespace.name,
                                                      self.name))

    @property
    def tblname(self):
        return "%s___%s" % (self.namespace.name, self._name)

    @property
    def namespace(self):
        """Get the name of the entity"""
        return self._namespace

    @property
    def direct_superclasses(self):
        """Get the direct superclass of the entity.

        Returns:
            List[OntologyEntity]: The direct superclasses of the entity
        """
        return self._superclasses

    @property
    def direct_subclasses(self):
        """Get the direct subclasses of the entity

        Returns:
            Set[OntologyEntity]: The direct subclasses of the entity
        """
        return self._subclasses

    @property
    def subclasses(self):
        """Get the subclasses of the entity

        Returns:
            Set[OntologyEntity]: The direct subclasses of the entity
        """
        subclasses = [self]
        for p in self._subclasses:
            subclasses.extend(p.subclasses)
        result = list()
        for i, p in enumerate(subclasses):
            if p not in result:
                result.append(p)
        return result

    @property
    def superclasses(self):
        """Get the superclass of the entity

        Returns:
            Set[OntologyEntity]: The direct superclasses of the entity
        """

        superclasses = [self]
        for p in self._superclasses:
            superclasses.extend(p.superclasses)
        result = list()
        for i, p in enumerate(superclasses):
            if p not in superclasses[i + 1:]:
                result.append(p)
        return result

    @property
    def description(self):
        """Get the description of the entity

        Returns:
            str: The description of the entity
        """
        if self._description:
            return self._description
        return "To Be Determined"

    def is_subclass_of(self, other):
        """Subclass check.

        Args:
            other (OntologyEntity): Check if self is a subclass of this entity.

        Returns:
            bool: Whether self is a subclass of other.
        """
        return self in other.subclasses

    def is_superclass_of(self, other):
        """Superclass check.

        Args:
            other (OntologyEntity): Check if self is a superclass of this
                entity.

        Returns:
            bool: Whether self is a superclass of other.
        """
        return self in other.superclasses

    def get_triples(self):
        """ Get the triples of the entity """
        return [
            (self.iri, rdflib.RDFS.label, rdflib.Literal(self.name)),
            (self.iri, rdflib.RDFS.comment, rdflib.Literal(self.description))
        ]

    def _add_subclass(self, subclass):
        """Add a subclass to the entity

        Args:
            subclass (OntologyEntity): The subclass to add
        """
        logger.debug("Add subclass %s to %s" % (subclass, self))
        if subclass not in self._subclasses:
            self._subclasses.append(subclass)

    def _add_superclass(self, superclass):
        """Add a superclass to the entity

        Args:
            superclass (OntologyEntity): The superclass to add
        """
        logger.debug("Add superclass %s to %s" % (superclass, self))
        if superclass not in self._superclasses:
            self._superclasses.append(superclass)

    def _add_class_expression(self, keyword, class_expression):
        """Add a class expression to the entity.

        Args:
            keyword (str): The keyword for the class expression
                (e.g. subclass_of).
            class_expression (ClassExpression): The class expression to add.

        Raises:
            ValueError: Invalid class expression.
        """
        from osp.core.ontology.class_expression import ClassExpression
        if not isinstance(class_expression, ClassExpression):
            raise ValueError("Tried to add %s as class expression to %s"
                             % (class_expression, self))
        logger.debug("Add class expression %s for %s to %s"
                     % (class_expression, keyword, self))
        if keyword not in self._class_expressions:
            self._class_expressions[keyword] = list()
        self._class_expressions[keyword].append(class_expression)

    def _collect_class_expressions(self, keyword):
        """Get all the class expressions for a given keyword for this entity
        and its superclasses.

        Args:
            keyword (str): The keyword for the class expressions.
                (e.g. subclass_of)

        Returns:
            List[ClassExpression]: All class expressions for the keyword.
        """
        result = list()
        for superclass in self.superclasses:
            if keyword in superclass._class_expressions:
                result += superclass._class_expressions[keyword]
        return result

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state
