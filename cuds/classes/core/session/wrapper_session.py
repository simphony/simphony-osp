# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
from .session import Session


class WrapperSession(Session):
    """
    Common class for all wrapper sessions.
    Sets the engine and creates the sets with the changed elements
    """
    def __init__(self, engine):
        super().__init__()
        self._engine = engine
        self._reset_buffers()

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def _apply_added(self):
        """Add the added cuds to the engine"""
        pass

    @abstractmethod
    def _apply_updated(self):
        """Update the updated cuds in the engine"""
        pass

    @abstractmethod
    def _apply_deleted(self):
        """Delete the deleted cuds from the engine"""
        pass

    # OVERRIDE
    def store(self, entity):
        """Store the entity in the registry and add it to buffers.

        :param entity: The entity to store.
        :type entity: Cuds
        """
        super().store(entity)
        if entity.uid in self._deleted:
            del self._deleted[entity.uid]

        if entity.uid in self._uid_set:
            self._updated[entity.uid] = entity
        else:
            self._added[entity.uid] = entity

    # OVERRIDE
    def _notify_update(self, entity):
        """Add the updated entity to the buffers.

        :param entity: The entity that has been updated.
        :type entity: Cuds
        :raises RuntimeError: The updated object has been deleted previously.
        """
        if entity.uid in self._deleted:
            raise RuntimeError("Cannot update deleted object")

        if entity.uid in self._uid_set:
            self._updated[entity.uid] = entity
        else:
            self._added[entity.uid] = entity

    # OVERRIDE
    def _notify_delete(self, entity):
        """Add the deleted entity to the buffers.

        :param entity: The entity that has been deleted.
        :type entity: Cuds
        """
        if entity.uid in self._added:
            del self._added[entity.uid]
        elif entity.uid in self._updated:
            del self._updated[entity.uid]
            self._deleted[entity.uid] = entity
        else:
            self._deleted[entity.uid] = entity

    def _reset_buffers(self):
        """Reset the buffers"""
        self._added = dict()
        self._updated = dict()
        self._deleted = dict()
        self._uid_set = set(self._registry.keys())

    def _check_cardinalities(self):
        """Check if the cardinalities specified in the ontology
        are satisfied for the added and updated cuds."""
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        for cuds in set(self._added.values()) | set(self._updated.values()):
            ontology_cardinalities, consider_relationships = \
                self._get_ontology_cardinalities(cuds)

            # Count the observed cardinalities
            observed_cardinalities = {k: 0
                                      for k in ontology_cardinalities.keys()}
            for rel in consider_relationships:
                for _, cuba in cuds[rel].items():
                    for r, o in ontology_cardinalities.keys():
                        if issubclass(rel, r) \
                                and issubclass(CUBA_MAPPING[cuba], o):
                            observed_cardinalities[r, o] += 1

            # Check if observed cardinalities are consistent
            for r, o in ontology_cardinalities.keys():
                if not (ontology_cardinalities[r, o][0]
                        <= observed_cardinalities[r, o]
                        <= ontology_cardinalities[r, o][1]):
                    raise ValueError(
                        ("The number of %s connected to %s via %s"
                         + " should be in range %s, but %s given.")
                        % (o, cuds, r,
                           list(ontology_cardinalities[r, o]),
                           observed_cardinalities[r, o]))

    @staticmethod
    def _parse_cardinality(cardinality):
        """Parse the cardinality string given in the ontology:
        Allowed: many = * = 0+ / + = 1+ / a+ / a-b / a

        :param cardinality: The given cardinality string to parse
        :type cardinality: str
        :return: A tuple defining the min and max number of occurences
        :rtype: Tuple[int, int]
        """
        min_occurences = 0
        max_occurences = float("inf")
        if isinstance(cardinality, int):
            min_occurences = max_occurences = cardinality
        elif cardinality in ["*", "many"]:
            pass
        elif cardinality == "+":
            min_occurences = 1
        elif cardinality == "?":
            min_occurences = 0
            max_occurences = 1
        elif cardinality.endswith("+"):
            min_occurences = int(cardinality[:-1].strip())
        elif "-" in cardinality:
            min_occurences = int(cardinality.split("-")[0].strip())
            max_occurences = int(cardinality.split("-")[1].strip())
        else:
            min_occurences = max_occurences = int(cardinality.strip())
        return min_occurences, max_occurences

    @staticmethod
    def _get_ontology_cardinalities(cuds):
        """Read the cardinalites for the given cuds as specified in the ontology.

        :param cuds: The given Cuds object.
        :type cuds: Cuds
        :return: Dictionary mapping relationship-Cuds_class
            to min and max number of occurences + set of relationships
            to consider when checking if cardinalities are satisfied.
        :rtype: Tuple[Dict[Tuple[Class, Class], Tuple[int, int]], Set]
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        ontology_cardinalities = dict()
        consider_relationships = set()
        for rel, objects in cuds.supported_relationships.items():
            for obj, options in objects.items():
                cardinality = options["cardinality"] \
                    if options and "cardinality" in options else "*"
                cardinality = WrapperSession._parse_cardinality(cardinality)
                rel_cls = CUBA_MAPPING[rel]
                obj_cls = CUBA_MAPPING[obj]
                ontology_cardinalities[rel_cls, obj_cls] = cardinality
                consider_relationships |= cuds._relationship_tree \
                    .get_subrelationships(rel_cls)
        return ontology_cardinalities, consider_relationships
