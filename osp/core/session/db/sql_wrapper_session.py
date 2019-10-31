# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
from operator import mul
from functools import reduce
from abc import abstractmethod
from cuds.utils import create_recycle
from cuds.generator.ontology_datatypes import convert_to, convert_from
from cuds.session.db.db_wrapper_session import DbWrapperSession
from cuds.session.db.conditions import EqualsCondition
from cuds.classes.generated.cuba import CUBA
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING


class SqlWrapperSession(DbWrapperSession):
    """Abstract class for an SQL DB Wrapper Session"""

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

    @abstractmethod
    def _db_select(self, table_name, columns, condition, datatypes):
        """Get data from the table of the given names.

        :param table_name: The name of the table.
        :type table_name: str
        :param columns: The names of the columns.
        :type columns: List[str]
        :param condition: A condition for filtering.
        :type condition: str
        :param rows: The rows fetched from the database
        :rtype: Iterator[List[Any]]
        """

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

    @abstractmethod
    def _db_delete(self, table_name, condition):
        """Delete data from the given table.

        :param table_name: The name of the table.
        :type table_name: str
        :param condition: Delete rows that satisfy the condition.
        :type condition: str
        """

    @abstractmethod
    def _get_table_names(self, prefix):
        """ Get all tables in the database with the given prefix.

        :param prefix: Only return tables with the given prefix
        :type prefix: str
        """

    @staticmethod
    def _expand_vector_cols(columns, datatypes, values=None):
        """SQL databases are not able to store vectors in general.
        So we instead create a column for each element in the vector.
        Therefore we need generate the column descriptions for each of those
        columns.
        During insertion, we need to transform the vectors
        into their individual values.

        This method expands the column description and the values, if given.

        :param columns: The columns to expand.
        :type columns: List[str]
        :param datatypes: The datatypes for each column.
            VECTORs will be expanded.
        :type datatypes: Dict[str, str]
        :param values: The values to expand, defaults to None
        :type values: List[Any], optional
        :return: The expanded columns, datatypes (and values, if given)
        :rtype: Tuple[List[str], Dict[str, str], (List[Any])]
        """
        columns_expanded = list()
        datatypes_expanded = dict()
        values_expanded = list()

        # iterate over the columns and look for vectors
        for i, column in enumerate(columns):

            # non vectors are simply added to the result
            if not datatypes[column].startswith("VECTOR:"):
                columns_expanded.append(column)
                datatypes_expanded[column] = datatypes[column]
                if values:
                    values_expanded.append(values[i])
                continue

            # create a column for each element in the vector
            size = reduce(mul, map(int, datatypes[column].split(":")[1:]))
            expanded_cols = ["%s___%s" % (column, x) for x in range(size)]
            columns_expanded.extend(expanded_cols)
            datatypes_expanded.update({c: "FLOAT" for c in expanded_cols})
            datatypes_expanded[column] = datatypes[column]
            if values:
                values_expanded.extend(convert_from(values[i],
                                                    datatypes[column]))
        if values:
            return columns_expanded, datatypes_expanded, values_expanded
        return columns_expanded, datatypes_expanded

    @staticmethod
    def _contract_vector_values(columns, datatypes, rows):
        """Contract the different values in a row of a database
        corresponding vectors into one vector object.

        :param columns: The expanded columns of the database
        :type columns: List[str]
        :param datatypes: The datatype for each column
        :type datatypes: dict
        :param rows: The rows fetched from the database
        :type rows: Iterator[List[Any]]
        :returns: The rows with vectors being a single item in each row.
        :rtype: Iterator[List[Any]]
        """
        for row in rows:
            contracted_row = list()
            temp_vec = list()  # collect the elements of the vectors here
            vector_datatype = None

            # iterate over the columns and look for vector columns
            for column, value in zip(columns, row):
                vector_datatype, is_vec_elem = SqlWrapperSession. \
                    handle_vector_item(column, value, datatypes,
                                       temp_vec, vector_datatype)
                if is_vec_elem:
                    continue

                if temp_vec:  # add the vector to the result
                    contracted_row.append(convert_to(temp_vec,
                                                     vector_datatype))
                    temp_vec = list()

                vector_datatype, is_vec_elem = SqlWrapperSession. \
                    handle_vector_item(column, value, datatypes,
                                       temp_vec, vector_datatype)
                if is_vec_elem:
                    continue

                # non vectors are simply added to the result
                contracted_row.append(value)

            if temp_vec:  # add the vector to the result
                contracted_row.append(convert_to(temp_vec,
                                                 vector_datatype))
                temp_vec = list()
            yield contracted_row

    @staticmethod
    def handle_vector_item(column, value, datatypes, temp_vec,
                           old_vector_datatype):
        """Check if a column corresponds to a vector.
        If it does, add it to the temp_vec list.
        Used during contract_vector_values

        :param column: The currect column to consider in the contraction
        :type column: str
        :param value: The value of the column
        :type value: Any
        :param datatypes: Maps a datatype to each column
        :type datatypes: List
        :param temp_vec: The elements of the current vector.
        :type temp_vec: List[float]
        :param old_vector_datatype: The vector datatype of the old iteration.
        :type old_vector_datatype: str
        :return: The new vector datatype and whether the current
            column corresponds to a vector
        :rtype: Tuple[str, bool]
        """
        vec_suffix = "___%s" % len(temp_vec)  # suffix of vector column
        if column.endswith(vec_suffix):
            temp_vec.append(value)  # store the vector element
            orig_col = column[:-len(vec_suffix)]
            return datatypes[orig_col], True
        return old_vector_datatype, False

    def _do_db_create(self, table_name, columns, datatypes,
                      primary_key, foreign_key, index):
        """Call db_create but expand the vectors first."""
        columns, datatypes = self._expand_vector_cols(columns, datatypes)
        self._db_create(table_name, columns, datatypes,
                        primary_key, foreign_key, index)

    def _do_db_select(self, table_name, columns, condition, datatypes):
        """Call db_select but consider vectors"""
        columns, datatypes = self._expand_vector_cols(columns, datatypes)
        rows = self._db_select(table_name, columns, condition, datatypes)
        rows = self._convert_values(rows, columns, datatypes)
        yield from self._contract_vector_values(columns, datatypes, rows)

    def _do_db_insert(self, table_name, columns, values, datatypes):
        """Call db_insert but expand vectors"""
        columns, datatypes, values = self._expand_vector_cols(columns,
                                                              datatypes,
                                                              values)
        values = [convert_from(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        self._db_insert(table_name, columns, values, datatypes)

    def _do_db_update(self, table_name, columns,
                      values, condition, datatypes):
        """Call db_update but expand vectors"""
        columns, datatypes, values = self._expand_vector_cols(columns,
                                                              datatypes,
                                                              values)
        values = [convert_from(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        self._db_update(table_name, columns,
                        values, condition, datatypes)

    def _do_db_delete(self, table_name, condition):
        """Call _db_delete but expand vectors"""
        self._db_delete(table_name, condition)

    def _clear_database(self):
        """Delete the contents of every table."""
        self._init_transaction()
        try:
            for table_name in self._get_table_names(
                    SqlWrapperSession.CUDS_PREFIX):
                self._do_db_delete(table_name, None)
            self._do_db_delete(self.RELATIONSHIP_TABLE, None)
            self._do_db_delete(self.MASTER_TABLE, None)
            self._commit()
        except Exception as e:
            self._rollback_transaction()
            raise e

    # OVERRIDE
    def _apply_added(self):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.

        for added in self._added.values():
            if added.uid == self.root:
                continue

            # Create tables
            if added.get_attributes(skip=["session"]):
                self._do_db_create(
                    table_name=self.CUDS_PREFIX + added.cuba_key.value,
                    columns=added.get_attributes(skip=["session"]),
                    datatypes=added.get_datatypes(),
                    primary_key=["uid"],
                    foreign_key={"uid": (self.MASTER_TABLE, "uid")},
                    index=[]
                )

            # Add to master
            is_first_level = any(self.root in uids for uids in added.values())
            self._do_db_insert(
                self.MASTER_TABLE,
                ["uid", "cuba", "first_level"],
                [added.uid, added.cuba_key.value, is_first_level],
                self.DATATYPES[self.MASTER_TABLE]
            )

            # Insert the items
            if added.get_attributes(skip=["session"]):
                values = [getattr(added, attr)
                          for attr in added.get_attributes(skip=["session"])]
                self._do_db_insert(
                    self.CUDS_PREFIX + added.cuba_key.value,
                    added.get_attributes(skip=["session"]),
                    values,
                    added.get_datatypes()
                )

            # Insert the relationships
            for rel, uid_cuba in added.items():
                for uid, cuba in uid_cuba.items():
                    target_uid = uid if uid != self.root else uuid.UUID(int=0)
                    self._do_db_insert(
                        self.RELATIONSHIP_TABLE,
                        ["origin", "target", "name", "target_cuba"],
                        [added.uid, target_uid,
                         rel.cuba_key.value, cuba.value],
                        self.DATATYPES[self.RELATIONSHIP_TABLE]
                    )

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
                self._do_db_update(
                    self.CUDS_PREFIX + updated.cuba_key.value,
                    updated.get_attributes(skip=["session"]),
                    values,
                    EqualsCondition(self.CUDS_PREFIX + updated.cuba_key.value,
                                    "uid",
                                    updated.uid,
                                    "UUID"),
                    updated.get_datatypes())

            # Update the relationships
            first_level = False
            self._do_db_delete(
                self.RELATIONSHIP_TABLE,
                EqualsCondition(self.RELATIONSHIP_TABLE,
                                "origin", updated.uid, "UUID")
            )
            for rel, uid_cuba in updated.items():
                for uid, cuba in uid_cuba.items():
                    first_level = first_level or uid == self.root
                    target_uuid = uid if uid != self.root else uuid.UUID(int=0)
                    self._do_db_insert(
                        self.RELATIONSHIP_TABLE,
                        ["origin", "target", "name", "target_cuba"],
                        [updated.uid, target_uuid,
                         rel.cuba_key.value, cuba.value],
                        self.DATATYPES[self.RELATIONSHIP_TABLE]
                    )

            # update first_level flag
            self._do_db_update(
                table_name=self.MASTER_TABLE,
                columns=["first_level"],
                values=[first_level],
                condition=EqualsCondition(self.MASTER_TABLE,
                                          "uid", updated.uid, "UUID"),
                datatypes=self.DATATYPES[self.MASTER_TABLE]
            )

    # OVERRIDE
    def _apply_deleted(self):
        # Perform the SQL-Statements to delete the elements
        # in the buffers in the DB.
        for deleted in self._deleted.values():
            if deleted.uid == self.root:
                continue

            # Update the values
            if deleted.get_attributes(skip=["session"]):
                self._do_db_delete(
                    self.CUDS_PREFIX + deleted.cuba_key.value,
                    EqualsCondition(self.CUDS_PREFIX + deleted.cuba_key.value,
                                    "uid", deleted.uid, "UUID")
                )

            self._do_db_delete(
                self.MASTER_TABLE,
                EqualsCondition(self.MASTER_TABLE,
                                "uid", deleted.uid, "UUID")
            )
            self._do_db_delete(
                self.RELATIONSHIP_TABLE,
                EqualsCondition(self.RELATIONSHIP_TABLE,
                                "origin", deleted.uid, "UUID")
            )

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
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
        self._do_db_create(
            table_name=self.MASTER_TABLE,
            columns=self.COLUMNS[self.MASTER_TABLE],
            datatypes=self.DATATYPES[self.MASTER_TABLE],
            primary_key=self.PRIMARY_KEY[self.MASTER_TABLE],
            foreign_key=self.FOREIGN_KEY[self.MASTER_TABLE],
            index=self.INDEX[self.MASTER_TABLE]
        )
        self._do_db_create(
            table_name=self.RELATIONSHIP_TABLE,
            columns=self.COLUMNS[self.RELATIONSHIP_TABLE],
            datatypes=self.DATATYPES[self.RELATIONSHIP_TABLE],
            primary_key=self.PRIMARY_KEY[self.RELATIONSHIP_TABLE],
            foreign_key=self.FOREIGN_KEY[self.RELATIONSHIP_TABLE],
            index=self.INDEX[self.RELATIONSHIP_TABLE]
        )

    # OVERRIDE
    def _load_first_level(self):
        c = self._do_db_select(
            self.MASTER_TABLE,
            ["uid", "cuba"],
            EqualsCondition(self.MASTER_TABLE,
                            "first_level", True, "BOOL"),
            self.DATATYPES[self.MASTER_TABLE]
        )
        list(self._load_from_backend(map(lambda x: (x[0], CUBA(x[1])), c)))

    def _load_by_cuba(self, cuba, update_registry=False, uid=None):
        """Load the cuds_object with the given cuba (+ uid).
        If uid is None return all cuds_objects with given cuba_key.

        :param cuba: The Cuba-Key of the cuds_object
        :type cuba: CUBA
        :param uid: The uid of the Cuds to load.
        :type uid: UUID
        :param update_registry: Whether to update cuds_objects already
            present in the registry.
        :type update_registry: bool
        :return: The loaded cuds_object.
        :rtype: Cuds
        """
        if cuba is None and uid is not None:
            yield None
        if cuba is None:
            return
        if not update_registry and uid is not None and uid in self._registry:
            yield self._registry.get(uid)
            return
        tables = self._get_table_names(prefix=(self.CUDS_PREFIX + cuba.value))
        if not (self.CUDS_PREFIX + cuba.value) in tables:
            return
        cuds_class = CUBA_MAPPING[cuba]
        attributes = cuds_class.get_attributes()
        datatypes = cuds_class.get_datatypes()
        condition = EqualsCondition(self.CUDS_PREFIX + cuba.value,
                                    "uid", uid, "UUID") \
            if uid else None

        c = self._do_db_select(
            self.CUDS_PREFIX + cuba.value,
            attributes,
            condition,
            datatypes
        )

        for row in c:
            kwargs = dict(zip(attributes, row))
            uid = convert_to(kwargs["uid"], "UUID")
            if not update_registry and uid in self._registry:
                yield self._registry.get(uid)
                continue
            cuds_object = create_recycle(entity_cls=cuds_class,
                                             kwargs=kwargs,
                                             session=self,
                                             add_to_buffers=False)
            self._load_relationships(cuds_object)
            yield cuds_object

    def _load_relationships(self, cuds_object):
        """Adds the relationships in the db to the given cuds_objects.

        :param cuds_object: Adds the relationships to this cuds_object.s
        :type cuds_object: Cuds
        """
        c = self._do_db_select(
            self.RELATIONSHIP_TABLE,
            ["target", "name", "target_cuba"],
            EqualsCondition(self.RELATIONSHIP_TABLE,
                            "origin", cuds_object.uid,
                            "UUID"),
            self.DATATYPES[self.RELATIONSHIP_TABLE]
        )
        for target, name, target_cuba in c:
            target_cuba = CUBA(target_cuba)
            rel = CUBA_MAPPING[CUBA(name)]

            if rel not in cuds_object:
                cuds_object[rel] = dict()
            if target == uuid.UUID(int=0):
                root_obj = self._registry.get(self.root)
                cuds_object[rel][self.root] = root_obj.cuba_key
                if CUBA_MAPPING[rel.inverse] not in root_obj:
                    root_obj[CUBA_MAPPING[rel.inverse]] = dict()
                root_obj[CUBA_MAPPING[rel.inverse]][cuds_object.uid] = \
                    cuds_object.cuba_key
            elif target != uuid.UUID(int=0):
                cuds_object[rel][target] = target_cuba

    def _get_cuba(self, uid):
        """Get the cuba-key of the given uid from the database.

        :param uid: Load the cuba-key of this uis.
        :type uid: UUID
        :return: The cuba-key.
        :rtype: CUBA
        """
        c = self._do_db_select(
            self.MASTER_TABLE,
            ["cuba"],
            EqualsCondition(self.MASTER_TABLE,
                            "uid", uid,
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
