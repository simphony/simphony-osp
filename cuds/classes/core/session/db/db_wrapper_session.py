# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from abc import abstractmethod
import uuid
from cuds.classes.core.session.wrapper_session import WrapperSession
from cuds.classes.core.session.db.conditions import EqualsCondition
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA


class DbWrapperSession(WrapperSession):
    master_table = "CUDS_MASTER"
    relationships_table = "CUDS_RELATIONSHIPS"
    datatypes = {
        master_table: {"uid": "UUID",
                       "cuba": "STRING",
                       "first_level": "INT"},
        relationships_table: {"origin": "UUID",
                              "target": "UUID",
                              "name": "STRING",
                              "cuba": "STRING"}}

    def __init__(self, engine):
        super().__init__(engine)
        self._initialize_tables()
        self._load_first_level()
        self._reset_buffers()
        self.root = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def commit(self):
        """Commit the changes in the buffers to the database."""
        self._check_cardinalities()
        self._apply_added()
        self._apply_updated()
        self._apply_deleted()
        self._commit()
        self._reset_buffers()

    # OVERRIDE
    def store(self, entity):
        super().store(entity)

        # if new root added (new wrapper), create relationships
        # to first level childrens.
        if self._first_level_connections_to_root:
            for uid, rel in self._first_level_connections_to_root:
                first_level_entity = self._registry.get(uid)
                first_level_entity._add_direct(entity, rel)
                entity._add_inverse(first_level_entity, rel)
            self._first_level_connections_to_root = None
            self._reset_buffers()

    # OVERRIDE
    def load(self, *uids):
        missing_uids = [uid for uid in uids if uid not in self._registry]

        # Load elements not in the registry from the database
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
        """Close the connection to the database"""
        pass

    @abstractmethod
    def _commit(self):
        """Call the commit command of the database
        e.g. self._engine.commit()"""
        pass

    @abstractmethod
    def _db_select(self, table_name, columns, condition, datatypes):
        """Get data from the table of the given names.

        :param table_name: The name of the table.
        :type table_name: str
        :param columns: The names of the columns.
        :type columns: List[str]
        :param condition: A condition for filtering.
        :type condition: str
        """
        pass

    @abstractmethod
    def _db_create(self, table_name, columns, datatypes):
        """Create a new table with the given name and columns

        :param table_name: The name of the new table.
        :type table_name: str
        :param columns: The name of the columns.
        :type columns: List[str]
        :param datatypes: Maps columns to datatypes specified in ontology.
        :type columns: Dict[String, String]
        """
        pass

    @abstractmethod
    def _db_insert(self, table_name, columns, values, datatypes):
        """Insert data into the table with the given name.

        :param table_name: The table name.
        :type table_name: str
        :param columns: The names of the columns.
        :type columns: List[str]
        :param values: The data to insert.
        :type values: List[TODO]
        """
        pass

    @abstractmethod
    def _db_update(self, table_name, columns, values, condition, datatypes):
        """Update the data in the given table.

        :param table_name: The name of the table.
        :type table_name: str
        :param columns: The names of the columns.
        :type columns: List[str]
        :param values: The new updated values.
        :type values: List[TODO]
        :param condition: Only update rows that satisfy the condition.
        :type condition: str
        """
        pass

    @abstractmethod
    def _db_delete(self, table_name, condition):
        """Delete data from the given table.

        :param table_name: The name of the table.
        :type table_name: str
        :param condition: Delete rows that satisfy the condition.
        :type condition: str
        """
        pass

    @abstractmethod
    def _get_table_names(self):
        """Get a list of all tables in the database."""
        pass

    def _initialize_tables(self):
        """Create master tables if they don't exit"""
        self._db_create(self.master_table,
                        ["uid", "cuba", "first_level"],
                        self.datatypes[self.master_table])
        self._db_create(self.relationships_table,
                        ["origin", "target", "name", "cuba"],
                        self.datatypes[self.relationships_table])

    def _load_first_level(self):
        """Load the first level of entities"""
        self._first_level_connections_to_root = None
        connections_to_root = set()

        c = self._db_select(self.master_table,
                            ["uid", "cuba"],
                            EqualsCondition("first_level", 1, "INT"),
                            self.datatypes[self.master_table])
        list(self._load_many_cuds(
            map(lambda x: (x[0], CUBA(x[1])), c),
            connections_to_root))
        self._first_level_connections_to_root = connections_to_root

    # OVERRIDE
    def _apply_added(self):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.

        tables = self._get_table_names()
        for added in self._added.values():
            if added.uid == self.root:
                continue

            # Create tables
            if added.cuba_key.value not in tables \
                    and added.get_attributes(skip="session"):
                tables.add(added.cuba_key.value)
                self._db_create(added.cuba_key.value,
                                ["uid"] + added.get_attributes(skip="session"),
                                added.get_datatypes())

            # Insert the items
            if added.get_attributes(skip="session"):
                values = [getattr(added, attr)
                          for attr in added.get_attributes(skip="session")]
                self._db_insert(added.cuba_key.value,
                                ["uid"] + added.get_attributes(skip="session"),
                                [added.uid] + values,
                                added.get_datatypes())

            # Add to master
            is_first_level = False
            root = self._registry.get(self.root)
            for rel, uids in root.items():
                if added.uid in uids:
                    is_first_level = True
                    break
            self._db_insert(
                self.master_table,
                ["uid", "cuba", "first_level"],
                [added.uid, added.cuba_key.value, is_first_level],
                self.datatypes[self.master_table]
            )

            # Insert the relationships
            for rel, uid_cuba in added.items():
                for uid, cuba in uid_cuba.items():
                    target_uuid = uid if uid != self.root else uuid.UUID(int=0)
                    self._db_insert(self.relationships_table,
                                    ["origin", "target", "name", "cuba"],
                                    [added.uid,
                                     target_uuid,
                                     rel.cuba_key.value,
                                     cuba.value],
                                    self.datatypes[self.relationships_table])

    # OVERRIDE
    def _apply_updated(self):
        # Perform the SQL-Statements to update the elements
        # in the buffers in the DB.
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
                    EqualsCondition("uid", updated.uid, "UUID"),
                    updated.get_datatypes())

            # Update the relationships
            self._db_delete(self.relationships_table,
                            EqualsCondition("origin", updated.uid, "UUID"))
            for rel, uid_cuba in updated.items():
                for uid, cuba in uid_cuba.items():
                    target_uuid = uid if uid != self.root else uuid.UUID(int=0)
                    self._db_insert(self.relationships_table,
                                    ["origin", "target", "name", "cuba"],
                                    [updated.uid,
                                     target_uuid,
                                     rel.cuba_key.value,
                                     cuba.value],
                                    self.datatypes[self.relationships_table])

    # OVERRIDE
    def _apply_deleted(self):
        # Perform the SQL-Statements to delete the elements
        # in the buffers in the DB.
        for deleted in self._deleted.values():
            if deleted.uid == self.root:
                continue

            # Update the values
            if deleted.get_attributes(skip="session"):
                self._db_delete(deleted.cuba_key.value,
                                EqualsCondition("uid", deleted.uid, "UUID"))

            self._db_delete(self.master_table,
                            EqualsCondition("uid", deleted.uid, "UUID"))
            self._db_delete(self.relationships_table,
                            EqualsCondition("origin", deleted.uid, "UUID"))

    def _load_missing(self, *uids):
        """Load the missing entities from the database.

        : param uids: The uids od the entities to load.
        : type uids: UUID
        : return: The loaded entities.
        : rtype: Iterator[Cuds]
        """
        yield from self._load_many_cuds(uids)

    def _load_many_cuds(self, uid_cuba_iterator, connections_to_root=None):
        """Load the Cuds entities with given uids/uid+cuba.

        :param uid_cuba_iterator: Iterator of uids / uid-cuba_key tuples
            of the entities to load.
        :type uid_cuba_iterator: Iterator[Union[UUID, Tuple[UUID, CUBA]]]
        :param connections_to_root: [description], defaults to None
        :type connections_to_root: [type], optional
        """
        for uid_cuba in uid_cuba_iterator:
            if isinstance(uid_cuba, uuid.UUID):
                uid = uid_cuba
                cuba = None
            else:
                uid, cuba = uid_cuba
            cuds = self._load_single_cuds(uid, cuba, connections_to_root)
            yield cuds

    def _load_single_cuds(self, uid, cuba=None, connections_to_root=None):
        """Load the Cuds entity with the given uid/uid+cuba.

        :param uid: The uid of the Cuds to load.
        :type uid: UUID
        :param cuba: The Cuba-Key of the cuds object, defaults to None
        :type cuba: CUBA, optional
        :param connections_to_root: A set to collect all the relationships to
            the root, defaults to None
        :type connections_to_root: Set[Tuple[UUID, Relationship]], optional
        :return: The loaded Cuds entity.
        :rtype: Cuds
        """
        try:
            cuba = cuba or self._get_cuba(uid)
        except KeyError:
            return None
        cuds_class = CUBA_MAPPING[cuba]
        attributes = cuds_class.get_attributes()
        datatypes = cuds_class.get_datatypes()

        c = self._db_select(cuba.value,
                            attributes,
                            EqualsCondition("uid", uid, "UUID"),
                            datatypes)
        try:
            cuds = cuds_class(**dict(zip(attributes, next(c))))
        except StopIteration:
            return None
        cuds.session = self
        cuds.uid = uid
        self.store(cuds)
        self._load_relationships(cuds, connections_to_root)
        return cuds

    def _get_cuba(self, uid):
        """Get the cuba-key of the given uid from the database.

        :param uid: Load the cuba-key of this uis.
        :type uid: UUID
        :return: The cuba-key.
        :rtype: CUBA
        """
        c = self._db_select(self.master_table,
                            ["cuba"],
                            EqualsCondition("uid", uid, "UUID"),
                            self.datatypes[self.master_table])
        try:
            cuba = CUBA(next(c)[0])
        except StopIteration as e:
            raise KeyError("No entry with uid %s in db." % uid) from e
        return cuba

    def _load_relationships(self, cuds, connections_to_root):
        """Adds the relationships in the db to the given cuds objects.

        :param cuds: Adds the relationships to this cuds object.s
        :type cuds: Cuds
        :param connections_to_root: Collect the relationships to
            the root in this set.
        :type connections_to_root: Set[Tuple[UUID, Relationship]]
        """
        c = self._db_select(self.relationships_table,
                            ["target", "name", "cuba"],
                            EqualsCondition("origin", cuds.uid, "UUID"),
                            self.datatypes[self.relationships_table])
        for target, name, target_cuba in c:
            target_cuba = CUBA(target_cuba)
            rel = CUBA_MAPPING[CUBA(name)]

            if rel not in cuds:
                cuds[rel] = dict()
            if target == uuid.UUID(int=0) and connections_to_root is not None:
                connections_to_root.add((cuds.uid, rel))
            elif target != uuid.UUID(int=0):
                cuds[rel][target] = target_cuba

    def _convert_uuid_values(self, values, uuid_columns, from_datatype):
        result = list(values)
        for i in uuid_columns:
            result[i] = uuid.UUID(**{from_datatype: values[i]})
        return result
