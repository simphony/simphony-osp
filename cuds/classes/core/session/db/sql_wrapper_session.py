# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
from abc import abstractmethod
from cuds.utils import create_for_session
from cuds.metatools.ontology_datatypes import convert_to
from cuds.classes.core.session.db.db_wrapper_session import DbWrapperSession
from cuds.classes.core.session.db.conditions import EqualsCondition
from cuds.classes.generated.cuba import CUBA
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING


class SqlWrapperSession(DbWrapperSession):
    CUDS_PREFIX = "CUDS_"
    RELATIONSHIP_TABLE = "OSP_RELATIONSHIPS"
    MASTER_TABLE = "OSP_MASTER"
    COLUMNS = {
        MASTER_TABLE: ["uid", "cuba", "first_level"],
        RELATIONSHIP_TABLE: ["origin", "target", "name", "target_cuba"]
    }
    DATATYPES = {
        MASTER_TABLE: {"uid": "UUID",
                       "cuba": "STRING",
                       "first_level": "BOOL"},
        RELATIONSHIP_TABLE: {"origin": "UUID",
                             "target": "UUID",
                             "name": "STRING",
                             "target_cuba": "STRING"}
    }
    PRIMARY_KEY = {
        MASTER_TABLE: ["uid"],
        RELATIONSHIP_TABLE: ["origin", "target", "name"]
    }
    FOREIGN_KEY = {
        MASTER_TABLE: {},
        RELATIONSHIP_TABLE: {
            "origin": (MASTER_TABLE, "uid"),
            # "target": (MASTER_TABLE, "uid")
        }
    }
    INDEX = {
        MASTER_TABLE: ["cuba", "first_level"],
        RELATIONSHIP_TABLE: ["origin"]
    }

    @abstractmethod
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, foreign_key, index):
        """Create a new table with the given name and columns

        :param table_name: The name of the new table.
        :type table_name: str
        :param columns: The name of the columns.
        :type columns: List[str]
        :param datatypes: Maps columns to datatypes specified in ontology.
        :type columns: Dict[String, String]
        :param primary_key: List of columns that belong to the primary key.
        :type primary_key: List[str]
        :param foreign_key: mapping from column to other tables column.
        :type foreign_key: Dict[str, Tuple[str (table), str (column)]]
        :param index: List of column for which an index should be built.
        :type index: List(str)
        """
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
    def _db_insert(self, table_name, columns, values, datatypes):
        """Insert data into the table with the given name.

        :param table_name: The table name.
        :type table_name: str
        :param columns: The names of the columns.
        :type columns: List[str]
        :param values: The data to insert.
        :type values: List[Any]
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
        :type values: List[Any]
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

    # OVERRIDE
    def _apply_added(self):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.

        for added in self._added.values():
            if added.uid == self.root:
                continue

            # Create tables
            if added.get_attributes(skip=["session"]):
                self._db_create(table_name=self.CUDS_PREFIX
                                + added.cuba_key.value,
                                columns=added.get_attributes(skip=["session"]),
                                datatypes=added.get_datatypes(),
                                primary_key=["uid"],
                                foreign_key={"uid":
                                             (self.MASTER_TABLE, "uid")},
                                index=[])

            # Add to master
            is_first_level = any(self.root in uids for uids in added.values())
            self._db_insert(
                self.MASTER_TABLE,
                ["uid", "cuba", "first_level"],
                [added.uid, added.cuba_key.value, is_first_level],
                self.DATATYPES[self.MASTER_TABLE]
            )

            # Insert the items
            if added.get_attributes(skip=["session"]):
                values = [getattr(added, attr)
                          for attr in added.get_attributes(skip=["session"])]
                self._db_insert(self.CUDS_PREFIX + added.cuba_key.value,
                                added.get_attributes(skip=["session"]),
                                values,
                                added.get_datatypes())

            # Insert the relationships
            for rel, uid_cuba in added.items():
                for uid, cuba in uid_cuba.items():
                    target_uid = uid if uid != self.root else uuid.UUID(int=0)
                    self._db_insert(self.RELATIONSHIP_TABLE,
                                    ["origin", "target",
                                     "name", "target_cuba"],
                                    [added.uid,
                                     target_uid,
                                     rel.cuba_key.value,
                                     cuba.value],
                                    self.DATATYPES[self.RELATIONSHIP_TABLE])

    # OVERRIDE
    def _apply_updated(self):
        # Perform the SQL-Statements to update the elements
        # in the buffers in the DB.
        for updated in self._updated.values():
            if updated.uid == self.root:
                continue

            # Update the values
            if updated.get_attributes(skip=["session"]):
                values = [getattr(updated, attr)
                          for attr in updated.get_attributes(skip=["session"])]
                self._db_update(
                    self.CUDS_PREFIX + updated.cuba_key.value,
                    updated.get_attributes(skip=["session"]),
                    values,
                    EqualsCondition(self.CUDS_PREFIX + updated.cuba_key.value,
                                    "uid",
                                    updated.uid,
                                    "UUID"),
                    updated.get_datatypes())

            # Update the relationships
            self._db_delete(self.RELATIONSHIP_TABLE,
                            EqualsCondition(self.RELATIONSHIP_TABLE,
                                            "origin",
                                            updated.uid,
                                            "UUID"))
            for rel, uid_cuba in updated.items():
                for uid, cuba in uid_cuba.items():
                    target_uuid = uid if uid != self.root else uuid.UUID(int=0)
                    self._db_insert(self.RELATIONSHIP_TABLE,
                                    ["origin", "target",
                                     "name", "target_cuba"],
                                    [updated.uid,
                                     target_uuid,
                                     rel.cuba_key.value,
                                     cuba.value],
                                    self.DATATYPES[self.RELATIONSHIP_TABLE])

    # OVERRIDE
    def _apply_deleted(self):
        # Perform the SQL-Statements to delete the elements
        # in the buffers in the DB.
        for deleted in self._deleted.values():
            if deleted.uid == self.root:
                continue

            # Update the values
            if deleted.get_attributes(skip=["session"]):
                self._db_delete(self.CUDS_PREFIX + deleted.cuba_key.value,
                                EqualsCondition(self.CUDS_PREFIX
                                                + deleted.cuba_key.value,
                                                "uid",
                                                deleted.uid,
                                                "UUID"))

            self._db_delete(self.MASTER_TABLE,
                            EqualsCondition(self.MASTER_TABLE,
                                            "uid",
                                            deleted.uid,
                                            "UUID"))
            self._db_delete(self.RELATIONSHIP_TABLE,
                            EqualsCondition(self.RELATIONSHIP_TABLE,
                                            "origin",
                                            deleted.uid,
                                            "UUID"))

    # OVERRIDE
    def _load_cuds(self, uids, expired=None):
        for uid in uids:
            if isinstance(uid, uuid.UUID):
                cuba = self._get_cuba(uid)
            elif isinstance(uid, tuple) and len(uid) == 2:
                uid, cuba = uid
            else:
                raise ValueError("Invalid uid given %s" % uid)
            loaded = list(self._load_by_cuba(cuba=cuba,
                                             update_registry=True,
                                             uid=uid))
            yield loaded[0] if loaded else None

    # OVERRIDE
    def _initialize(self):
        self._db_create(table_name=self.MASTER_TABLE,
                        columns=self.COLUMNS[self.MASTER_TABLE],
                        datatypes=self.DATATYPES[self.MASTER_TABLE],
                        primary_key=self.PRIMARY_KEY[self.MASTER_TABLE],
                        foreign_key=self.FOREIGN_KEY[self.MASTER_TABLE],
                        index=self.INDEX[self.MASTER_TABLE])
        self._db_create(table_name=self.RELATIONSHIP_TABLE,
                        columns=self.COLUMNS[self.RELATIONSHIP_TABLE],
                        datatypes=self.DATATYPES[self.RELATIONSHIP_TABLE],
                        primary_key=self.PRIMARY_KEY[self.RELATIONSHIP_TABLE],
                        foreign_key=self.FOREIGN_KEY[self.RELATIONSHIP_TABLE],
                        index=self.INDEX[self.RELATIONSHIP_TABLE])

    # OVERRIDE
    def _load_first_level(self):
        c = self._db_select(self.MASTER_TABLE,
                            ["uid", "cuba"],
                            EqualsCondition(self.MASTER_TABLE,
                                            "first_level",
                                            True,
                                            "BOOL"),
                            self.DATATYPES[self.MASTER_TABLE])
        list(self._load_cuds(map(lambda x: (x[0], CUBA(x[1])), c)))

    def _load_by_cuba(self, cuba, update_registry=False, uid=None):
        """Load the Cuds entity with the given cuba (+ uid).
        If uid is None return all entities with given cuba_key.

        :param cuba: The Cuba-Key of the cuds object
        :type cuba: CUBA
        :param uid: The uid of the Cuds to load.
        :type uid: UUID
        :param update_registry: Whether to update cuds objects already
            present in the registry.
        :type update_registry: bool
        :return: The loaded Cuds entity.
        :rtype: Cuds
        """
        if cuba is None and uid is not None:
            yield None
        if cuba is None:
            return
        if not update_registry and uid is not None and uid in self._registry:
            yield self._registry.get(uid)
            return
        cuds_class = CUBA_MAPPING[cuba]
        attributes = cuds_class.get_attributes()
        datatypes = cuds_class.get_datatypes()
        condition = EqualsCondition(self.CUDS_PREFIX + cuba.value,
                                    "uid", uid, "UUID") \
            if uid else None

        c = self._db_select(self.CUDS_PREFIX + cuba.value,
                            attributes,
                            condition,
                            datatypes)

        for row in c:
            kwargs = dict(zip(attributes, row))
            uid = convert_to(kwargs["uid"], "UUID")
            if not update_registry and uid in self._registry:
                yield self._registry.get(uid)
                continue
            cuds = create_for_session(cuds_class, kwargs, self)
            self._load_relationships(cuds)
            yield cuds

    def _load_relationships(self, cuds):
        """Adds the relationships in the db to the given cuds objects.

        :param cuds: Adds the relationships to this cuds object.s
        :type cuds: Cuds
        """
        c = self._db_select(self.RELATIONSHIP_TABLE,
                            ["target", "name", "target_cuba"],
                            EqualsCondition(self.RELATIONSHIP_TABLE,
                                            "origin",
                                            cuds.uid,
                                            "UUID"),
                            self.DATATYPES[self.RELATIONSHIP_TABLE])
        for target, name, target_cuba in c:
            target_cuba = CUBA(target_cuba)
            rel = CUBA_MAPPING[CUBA(name)]

            if rel not in cuds:
                cuds[rel] = dict()
            if target == uuid.UUID(int=0):
                root_obj = self._registry.get(self.root)
                cuds[rel][self.root] = root_obj.cuba_key
                if CUBA_MAPPING[rel.inverse] not in root_obj:
                    root_obj[CUBA_MAPPING[rel.inverse]] = dict()
                root_obj[CUBA_MAPPING[rel.inverse]][cuds.uid] = cuds.cuba_key
            elif target != uuid.UUID(int=0):
                cuds[rel][target] = target_cuba

    def _get_cuba(self, uid):
        """Get the cuba-key of the given uid from the database.

        :param uid: Load the cuba-key of this uis.
        :type uid: UUID
        :return: The cuba-key.
        :rtype: CUBA
        """
        c = self._db_select(self.MASTER_TABLE,
                            ["cuba"],
                            EqualsCondition(self.MASTER_TABLE,
                                            "uid",
                                            uid,
                                            "UUID"),
                            self.DATATYPES[self.MASTER_TABLE])
        try:
            return CUBA(next(c)[0])
        except StopIteration:
            return None

    def _convert_values(self, rows, columns, datatypes):
        """Convert the values in the database to the correct datatype.

        :param rows: The rows of the database
        :type rows: Iterator[Iterator[Any]]
        :param columns: The corresponding columns
        :type columns: List[str]
        :param datatypes: Mapping from column to datatype
        :type datatypes: Dict[str, str]
        """
        for row in rows:
            output = []
            for value, column in zip(row, columns):
                output.append(
                    convert_to(value, datatypes[column])
                )
            yield output
