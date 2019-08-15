# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
import uuid
from .wrapper_session import WrapperSession
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA


class DbWrapperSession(WrapperSession):
    def __init__(self, engine):
        super().__init__(engine)
        self._initialize_tables()
        self._load_first_level()
        self._reset_buffers()
        self.root = None

    def commit(self):
        self._apply_added()
        self._apply_updated()
        self._apply_deleted()
        self._commit()
        self._reset_buffers()

    # OVERRIDE
    def store(self, entity):
        super().store(entity)
        if self._first_level_connections_to_root:
            for uid, rel in self._first_level_connections_to_root:
                first_level_entity = self._registry.get(uid)
                first_level_entity._add_direct(entity, rel)
                entity._add_inverse(first_level_entity, rel)
        self._first_level_connections_to_root = None

    # OVERRIDE
    def load(self, *uids):
        """Look in the DB if element not in the registry.

        :param uids: The uids of the cuds objects to load.
        :type uids: UUID
        :return: The fetched Cuds objects.
        :rtype: Iterator[Cuds]
        """
        missing_uids = [uid for uid in uids if uid not in self._registry]
        missing = self._load_missing(*missing_uids)
        for uid in uids:
            if uid in self._registry:
                yield self._registry.get(uid)
            else:
                entity = next(missing)
                if entity is not None:
                    self._uid_set.add(entity.uid)
                yield entity

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def _commit(self):
        pass

    @abstractmethod
    def _db_select(self, table_name, columns, condition):
        pass

    @abstractmethod
    def _db_create(self, table_name, columns):
        pass

    @abstractmethod
    def _db_insert(self, table_name, columns, values):
        pass

    @abstractmethod
    def _db_update(self, table_name, columns, values, condition):
        pass

    @abstractmethod
    def _db_delete(self, table_name, condition):
        pass

    @abstractmethod
    def _get_table_names(self):
        pass

    def _initialize_tables(self):
        """Create master tables if they don't exit"""
        self._db_create("CUDS_MASTER", ["uid", "cuba", "first_level"])
        self._db_create("CUDS_RELATIONSHIPS",
                        ["origin", "target", "name", "cuba"])

    def _load_first_level(self):
        """Load the first level of entities"""
        self._first_level_connections_to_root = None
        connections_to_root = set()

        c = self._db_select("CUDS_MASTER",
                            ["uid", "cuba"],
                            "first_level='True'")
        list(self._load_many_cuds(
            map(lambda x: (uuid.UUID(hex=x[0]), CUBA(x[1])), c),
            connections_to_root))
        self._first_level_connections_to_root = connections_to_root

    def _apply_added(self):
        """Perform the SQL-Statements to add the elements
        in the buffers to the DB."""

        tables = self._get_table_names()
        for added in self._added.values():
            if added.uid == self.root:
                continue

            # Create tables
            if added.cuba_key.value not in tables \
                    and added.get_attributes(skip="session"):
                tables.add(added.cuba_key.value)
                self._db_create(added.cuba_key.value,
                                ["uid"] + added.get_attributes(skip="session"))

            # Insert the items
            if added.get_attributes(skip="session"):
                values = [getattr(added, attr)
                          for attr in added.get_attributes(skip="session")]
                self._db_insert(added.cuba_key.value,
                                ["uid"] + added.get_attributes(skip="session"),
                                [added.uid] + values)

            # Add to master
            is_first_level = False
            root = self._registry.get(self.root)
            for rel, uids in root.items():
                if added.uid in uids:
                    is_first_level = True
                    break
            self._db_insert(
                "CUDS_MASTER",
                ["uid", "cuba", "first_level"],
                [added.uid, added.cuba_key.value, is_first_level]
            )

            # Insert the relationships
            for rel, uid_cuba in added.items():
                for uid, cuba in uid_cuba.items():
                    self._db_insert("CUDS_RELATIONSHIPS",
                                    ["origin", "target", "name", "cuba"],
                                    [added.uid,
                                     (uid if uid != self.root else "ROOT"),
                                     rel.cuba_key.value,
                                     cuba.value])

    def _apply_updated(self):
        """Perform the SQL-Statements to update the elements
        in the buffers in the DB."""
        for updated in self._updated.values():
            if updated.uid == self.root:
                continue

            # Update the values
            if updated.get_attributes(skip="session"):
                values = [getattr(updated, attr)
                          for attr in updated.get_attributes(skip="session")]
                self._db_update(
                    updated.cuba_key.value,
                    updated.get_attributes(skip="session"),
                    values,
                    "'uid'=%s" % updated.uid)

            # Update the relationships
            self._db_delete("CUDS_RELATIONSHIPS", "origin='%s'" % updated.uid)
            for rel, uid_cuba in updated.items():
                for uid, cuba in uid_cuba.items():
                    self._db_insert("CUDS_RELATIONSHIPS",
                                    ["origin", "target", "name", "cuba"],
                                    [updated.uid,
                                     (uid if uid != self.root else "ROOT"),
                                     rel.cuba_key.value,
                                     cuba.value])

    def _apply_deleted(self):
        """Perform the SQL-Statements to delete the elements
        in the buffers in the DB."""
        for deleted in self._updated.values():
            if deleted.uid == self.root:
                continue

            # Update the values
            if deleted.get_attributes(skip="session"):
                self._db_delete(deleted.cuba_key.value,
                                "'uid'=%s" % deleted.uid)

            self._db_delete("CUDS_MASTER", "uid='%s'" % deleted.uid)
            self._db_delete("CUDS_RELATIONSHIPS", "origin='%s'" % deleted.uid)

    def _load_missing(self, *uids):
        """Load the missing entities from the database.

        : param uids: The uids od the entities to load.
        : type uids: UUID
        : return: The loaded entities.
        : rtype: Iterator[Cuds]
        """
        yield from self._load_many_cuds(uids)

    def _load_many_cuds(self, uid_cuba_iterator, connections_to_root=None):
        for uid_cuba in uid_cuba_iterator:
            if isinstance(uid_cuba, uuid.UUID):
                uid = uid_cuba
                cuba = None
            else:
                uid, cuba = uid_cuba
            cuds = self._load_single_cuds(uid, cuba, connections_to_root)
            yield cuds

    def _load_single_cuds(self, uid, cuba=None, connections_to_root=None):
        cuba = cuba or self._get_cuba(uid)
        cuds_class = CUBA_MAPPING[cuba]
        attributes = cuds_class.get_attributes()

        c = self._db_select(cuba.value, attributes, "uid='%s'" % uid)
        cuds = cuds_class(**dict(zip(attributes, next(c))))
        cuds.session = self
        cuds.uid = uid
        self.store(cuds)
        self._load_relationships(cuds, connections_to_root)
        return cuds

    def _get_cuba(self, uid):
        c = self._db_select("CUDS_MASTER", ["cuba"], "uid='%s'" % uid)
        cuba = CUBA(next(c)[0])
        return cuba

    def _load_relationships(self, cuds, connections_to_root):
        c = self._db_select("CUDS_RELATIONSHIPS",
                            ["target", "name", "cuba"],
                            "origin='%s'" % cuds.uid)
        for target, name, target_cuba in c:
            target_cuba = CUBA(target_cuba)
            rel = CUBA_MAPPING[CUBA(name)]

            if rel not in cuds:
                cuds[rel] = dict()
            if target == "ROOT" and connections_to_root is not None:
                connections_to_root.add((cuds.uid, rel))
            elif target != "ROOT":
                target = uuid.UUID(hex=target)
                cuds[rel][target] = target_cuba
