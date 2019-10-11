# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.classes.cuds import Cuds
from abc import abstractmethod
from .session import Session


def consumes_buffers(func):
    func.does_consume_buffers = True
    return func


def check_consumes_buffers(func):
    return hasattr(func, "does_consume_buffers") \
        and func.does_consume_buffers


class WrapperSession(Session):
    """
    Common class for all wrapper sessions.
    Sets the engine and creates the sets with the changed elements
    """
    def __init__(self, engine, forbid_buffer_reset_by=None):
        super().__init__()
        self._engine = engine
        self._forbid_buffer_reset_by = None
        self._reset_buffers(changed_by="engine")
        self._forbid_buffer_reset_by = forbid_buffer_reset_by

    @abstractmethod
    def __str__(self):
        pass

    # OVERRIDE
    def store(self, cuds_object):
        """Store the cuds_objects in the registry and add it to buffers.

        :param cuds_object: The cuds_object to store.
        :type cuds_object: Cuds
        """
        super().store(cuds_object)
        if cuds_object.uid in self._deleted:
            del self._deleted[cuds_object.uid]

        if cuds_object.uid in self._uids_in_registry_after_last_buffer_reset:
            self._updated[cuds_object.uid] = cuds_object
        else:
            self._added[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_update(self, cuds_object):
        """Add the updated cuds_object to the buffers.

        :param cuds_object: The cuds_object that has been updated.
        :type cuds_object: Cuds
        :raises RuntimeError: The updated object has been deleted previously.
        """
        if cuds_object.uid in self._deleted:
            raise RuntimeError("Cannot update deleted object")

        if cuds_object.uid in self._uids_in_registry_after_last_buffer_reset:
            self._updated[cuds_object.uid] = cuds_object
        else:
            self._added[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_delete(self, cuds_object):
        """Add the deleted cuds_object to the buffers.

        :param cuds_object: The cuds_object that has been deleted.
        :type cuds_object: Cuds
        """
        if cuds_object.uid in self._added:
            del self._added[cuds_object.uid]
        elif cuds_object.uid in self._updated:
            del self._updated[cuds_object.uid]
            self._deleted[cuds_object.uid] = cuds_object
        else:
            self._deleted[cuds_object.uid] = cuds_object

    # OVERRIDE
    def _notify_read(self, cuds_object):
        pass

    def _reset_buffers(self, changed_by):
        """Reset the buffers. When you run an engine,
        call this with changed_by="user" right before you execute the
        engine. After you execute the engine call it with
        changed_by="engine".

        :param changed_by: Were the buffers modified by the engine or the user?
        :type changed_by: str
        :return: Whether the buffers have been resetted.
        :rtype: bool
        """
        assert changed_by in ["user", "engine"]
        if changed_by == self._forbid_buffer_reset_by:
            return False
        self._added = dict()
        self._updated = dict()
        self._deleted = dict()
        # Save set of uids in registry to determine
        # if cuds_objects are added or updated
        self._uids_in_registry_after_last_buffer_reset = \
            set(self._registry.keys())
        return True

    def _remove_uids_from_buffers(self, uids):
        """Remove the given uids from the buffers.

        :param uids: A set/list of uids to remove from the buffers.
        :type uids: Iterable[UUID]
        """
        for uid in uids:
            self._uids_in_registry_after_last_buffer_reset.add(uid)
            if uid in self._added:
                del self._added[uid]
            if uid in self._updated:
                del self._updated[uid]
            if uid in self._deleted:
                del self._deleted[uid]

    def _check_cardinalities(self):
        """Check if the cardinalities specified in the ontology
        are satisfied for the added and updated cuds_object."""
        if not Cuds.CUDS_SETTINGS["check_cardinalities"]:
            return

        to_check = set(self._added.values()) | set(self._updated.values())
        for cuds_object in to_check:
            self._check_cuds_object_cardinalities(cuds_object)

    @staticmethod
    def _check_cuds_object_cardinalities(cuds_object):
        """Check the cardinality of a single cuds_object.

        :param cuds_object: The cuds_object to check-
        :type cuds_object: Cuds
        :raises ValueError: The cuds_object did not satisfy the cardinalities
            given by the ontology
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        ontology_cardinalities, consider_relationships = \
            WrapperSession._get_ontology_cardinalities(cuds_object)

        # Count the observed cardinalities
        observed_cardinalities = {k: 0
                                  for k in ontology_cardinalities.keys()}
        for rel in consider_relationships:
            for _, cuba in cuds_object[rel].items():
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
                    % (o, cuds_object, r,
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
        min_occurrences = 0
        max_occurrences = float("inf")
        if isinstance(cardinality, int):
            min_occurrences = max_occurrences = cardinality
        elif cardinality in ["*", "many"]:
            pass
        elif cardinality == "+":
            min_occurrences = 1
        elif cardinality == "?":
            min_occurrences = 0
            max_occurrences = 1
        elif cardinality.endswith("+"):
            min_occurrences = int(cardinality[:-1].strip())
        elif "-" in cardinality:
            min_occurrences = int(cardinality.split("-")[0].strip())
            max_occurrences = int(cardinality.split("-")[1].strip())
        else:
            min_occurrences = max_occurrences = int(cardinality.strip())
        return min_occurrences, max_occurrences

    @staticmethod
    def _get_ontology_cardinalities(cuds_object):
        """Read the cardinalites for the given cuds_object
            as specified in the ontology.

        :param cuds_object: The given Cuds object.
        :type cuds_object: Cuds
        :return: Dictionary mapping relationship-Cuds_class
            to min and max number of occurences + set of relationships
            to consider when checking if cardinalities are satisfied.
        :rtype: Tuple[Dict[Tuple[Class, Class], Tuple[int, int]], Set]
        """
        from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
        ontology_cardinalities = dict()
        consider_relationships = set()
        for rel, objects in cuds_object.supported_relationships.items():
            for obj, options in objects.items():
                cardinality = Cuds.CUDS_SETTINGS["default_cardinality"]
                if options and "cardinality" in options:
                    cardinality = options["cardinality"]
                cardinality = WrapperSession._parse_cardinality(cardinality)
                rel_cls = CUBA_MAPPING[rel]
                obj_cls = CUBA_MAPPING[obj]
                ontology_cardinalities[rel_cls, obj_cls] = cardinality
                consider_relationships |= cuds_object._relationship_tree \
                    .get_subrelationships(rel_cls)
        return ontology_cardinalities, consider_relationships
