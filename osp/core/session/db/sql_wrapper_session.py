"""An abstract session containing method useful for all SQL backends."""

import uuid
import rdflib
from operator import mul
from functools import reduce
from abc import abstractmethod
from osp.core.utils import create_recycle
from osp.core.ontology.datatypes import convert_to, convert_from, \
    _parse_vector_args
from osp.core.session.db.db_wrapper_session import DbWrapperSession
from osp.core.session.db.conditions import EqualsCondition, AndCondition
from osp.core.namespaces import get_entity
from osp.core.session.buffers import BufferContext
from osp.core.ontology.cuba import rdflib_cuba


class SqlWrapperSession(DbWrapperSession):
    """Abstract class for an SQL DB Wrapper Session."""

    CUDS_PREFIX = "CUDS_"
    RELATIONSHIP_TABLE = "OSP_RELATIONSHIPS"
    MASTER_TABLE = "OSP_MASTER"
    COLUMNS = {
        MASTER_TABLE: ["uid", "oclass", "first_level"],
        RELATIONSHIP_TABLE: ["origin", "target", "name", "target_oclass"]
    }
    DATATYPES = {
        MASTER_TABLE: {"uid": "UUID",
                       "oclass": rdflib.XSD.string,
                       "first_level": rdflib.XSD.boolean},
        RELATIONSHIP_TABLE: {"origin": "UUID",
                             "target": "UUID",
                             "name": rdflib.XSD.string,
                             "target_oclass": rdflib.XSD.string}
    }
    PRIMARY_KEY = {
        MASTER_TABLE: ["uid"],
        RELATIONSHIP_TABLE: ["origin", "target", "name"]
    }
    FOREIGN_KEY = {
        MASTER_TABLE: {},
        RELATIONSHIP_TABLE: {
            "origin": (MASTER_TABLE, "uid"),
            "target": (MASTER_TABLE, "uid")
        }
    }
    INDEXES = {
        MASTER_TABLE: [
            ["oclass"], ["first_level"]
        ],
        RELATIONSHIP_TABLE: [["origin"]]
    }

    @abstractmethod
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, foreign_key, indexes):
        """Create a new table with the given name and columns.

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
        :param indexes: List of indexes. Each index is a list of column names
            for which an index should be built.
        :type indexes: List(str)
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
        """Get all tables in the database with the given prefix.

        :param prefix: Only return tables with the given prefix
        :type prefix: str
        """

    @staticmethod
    def _expand_vector_cols(columns, datatypes, values=None):
        """Expand columns of vectors.

        SQL databases are not able to store vectors in general.
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
            vec_prefix = str(rdflib_cuba["_datatypes/VECTOR-"])
            if datatypes[column] is None or \
                    not datatypes[column].startswith(vec_prefix):
                columns_expanded.append(column)
                datatypes_expanded[column] = datatypes[column]
                if values:
                    values_expanded.append(values[i])
                continue

            # create a column for each element in the vector
            vector_args = datatypes[column][len(vec_prefix):].split("-")
            datatype, shape = _parse_vector_args(vector_args)
            size = reduce(mul, map(int, shape))
            expanded_cols = ["%s___%s" % (column, x) for x in range(size)]
            columns_expanded.extend(expanded_cols)
            datatypes_expanded.update({c: datatype for c in expanded_cols})
            datatypes_expanded[column] = datatypes[column]
            if values:
                values_expanded.extend(convert_from(values[i],
                                                    datatypes[column]))
        if values:
            return columns_expanded, datatypes_expanded, values_expanded
        return columns_expanded, datatypes_expanded

    @staticmethod
    def _contract_vector_values(columns, datatypes, rows):
        """Contract vector values in a row of a database into one vector.

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
                      primary_key, foreign_key, indexes):
        """Call db_create but expand the vectors first."""
        columns, datatypes = self._expand_vector_cols(columns, datatypes)
        self._check_characters(table_name, columns, datatypes,
                               primary_key, foreign_key, indexes)
        self._db_create(table_name, columns, datatypes,
                        primary_key, foreign_key, indexes)

    def _do_db_select(self, table_name, columns, condition, datatypes):
        """Call db_select but consider vectors."""
        columns, datatypes = self._expand_vector_cols(columns, datatypes)
        self._check_characters(table_name, columns, condition, datatypes)
        rows = self._db_select(table_name, columns, condition, datatypes)
        rows = self._convert_values(rows, columns, datatypes)
        yield from self._contract_vector_values(columns, datatypes, rows)

    def _do_db_insert(self, table_name, columns, values, datatypes):
        """Call db_insert but expand vectors."""
        columns, datatypes, values = self._expand_vector_cols(columns,
                                                              datatypes,
                                                              values)
        values = [convert_from(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        self._check_characters(table_name, columns, datatypes)
        self._db_insert(table_name, columns, values, datatypes)

    def _do_db_update(self, table_name, columns,
                      values, condition, datatypes):
        """Call db_update but expand vectors."""
        columns, datatypes, values = self._expand_vector_cols(columns,
                                                              datatypes,
                                                              values)
        values = [convert_from(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        self._check_characters(table_name, columns,
                               condition, datatypes)
        self._db_update(table_name, columns,
                        values, condition, datatypes)

    def _do_db_delete(self, table_name, condition):
        """Call _db_delete but expand vectors."""
        self._check_characters(table_name, condition)
        self._db_delete(table_name, condition)

    def _clear_database(self):
        """Delete the contents of every table."""
        self._init_transaction()
        try:
            # clear local datastructure
            from osp.core.namespaces import cuba
            self._reset_buffers(BufferContext.USER)
            root = self._registry.get(self.root)

            # if there is something to remove
            if root.get(rel=cuba.relationship):
                root.remove(rel=cuba.relationship)
                for uid in list(self._registry.keys()):
                    if uid != self.root:
                        self._delete_cuds_triples(self._registry.get(uid))
                self._reset_buffers(BufferContext.USER)

                # delete the data
                for table_name in self._get_table_names(
                        SqlWrapperSession.CUDS_PREFIX):
                    self._do_db_delete(table_name, None)
                self._do_db_delete(self.RELATIONSHIP_TABLE, None)
                self._do_db_delete(self.MASTER_TABLE, None)
                self._initialize()
                self._commit()
        except Exception as e:
            self._rollback_transaction()
            raise e

    # OVERRIDE
    def _expire_neighour_diff(self, old_cuds_object, new_cuds_object, uids):
        # do not expire if root is loaded
        x = old_cuds_object or new_cuds_object
        if x and x.uid != self.root:
            super()._expire_neighour_diff(old_cuds_object, new_cuds_object,
                                          uids)

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        # Perform the SQL-Statements to add the elements
        # in the buffers to the DB.

        for added in buffer.values():
            if added.uid == self.root:
                continue

            # Create tables
            oclass = added.oclass
            columns, datatypes = self._get_col_spec(oclass)
            if columns:
                self._do_db_create(
                    table_name=self.CUDS_PREFIX + oclass.tblname,
                    columns=columns,
                    datatypes=datatypes,
                    primary_key=["uid"],
                    foreign_key={"uid": (self.MASTER_TABLE, "uid")},
                    indexes=[]
                )

            # Add to master
            is_first_level = any(self.root in uids
                                 for uids in added._neighbors.values())
            self._do_db_insert(
                table_name=self.MASTER_TABLE,
                columns=["uid", "oclass", "first_level"],
                values=[added.uid, oclass, is_first_level],
                datatypes=self.DATATYPES[self.MASTER_TABLE]
            )

            # Insert the items
            if columns:
                values = [getattr(added, attr) for attr in columns]
                self._do_db_insert(
                    table_name=self.CUDS_PREFIX + oclass.tblname,
                    columns=columns,
                    values=values,
                    datatypes=datatypes
                )

        for added in buffer.values():
            if added.uid == self.root:
                continue

            # Insert the relationships
            for rel, neighbor_dict in added._neighbors.items():
                for uid, target_oclass in neighbor_dict.items():
                    target_uid = uid if uid != self.root else uuid.UUID(int=0)
                    self._do_db_insert(
                        self.RELATIONSHIP_TABLE,
                        ["origin", "target", "name", "target_oclass"],
                        [added.uid, target_uid,
                         rel, target_oclass],
                        self.DATATYPES[self.RELATIONSHIP_TABLE]
                    )

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        # Perform the SQL-Statements to update the elements
        # in the buffers in the DB.
        for updated in buffer.values():
            if updated.uid == self.root:
                continue

            # Update the values
            oclass = updated.oclass
            columns, datatypes = self._get_col_spec(oclass)
            if columns:
                values = [getattr(updated, attr) for attr in columns]
                self._do_db_update(
                    table_name=self.CUDS_PREFIX + oclass.tblname,
                    columns=columns,
                    values=values,
                    condition=EqualsCondition(
                        table_name=self.CUDS_PREFIX + oclass.tblname,
                        column="uid",
                        value=updated.uid,
                        datatype="UUID"
                    ),
                    datatypes=datatypes)

            # Update the relationships
            first_level = False
            self._do_db_delete(
                table_name=self.RELATIONSHIP_TABLE,
                condition=EqualsCondition(
                    table_name=self.RELATIONSHIP_TABLE,
                    column="origin",
                    value=updated.uid,
                    datatype="UUID"
                )
            )
            for rel, neighbor_dict in updated._neighbors.items():
                for uid, target_oclass in neighbor_dict.items():
                    first_level = first_level or uid == self.root
                    target_uuid = uid if uid != self.root else uuid.UUID(int=0)
                    self._do_db_insert(
                        table_name=self.RELATIONSHIP_TABLE,
                        columns=self.COLUMNS[self.RELATIONSHIP_TABLE],
                        values=[updated.uid, target_uuid,
                                rel, target_oclass],
                        datatypes=self.DATATYPES[self.RELATIONSHIP_TABLE]
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
    def _apply_deleted(self, root_obj, buffer):
        # Perform the SQL-Statements to delete the elements
        # in the buffers in the DB.
        for deleted in buffer.values():
            if deleted.uid == self.root:
                continue

            # Update the values
            oclass = deleted.oclass
            columns, datatypes = self._get_col_spec(oclass)
            if columns:
                self._do_db_delete(
                    table_name=self.CUDS_PREFIX + oclass.tblname,
                    condition=EqualsCondition(
                        table_name=self.CUDS_PREFIX + oclass.tblname,
                        column="uid",
                        value=deleted.uid,
                        datatype="UUID"
                    )
                )
            self._do_db_delete(
                table_name=self.RELATIONSHIP_TABLE,
                condition=EqualsCondition(
                    table_name=self.RELATIONSHIP_TABLE,
                    column="origin",
                    value=deleted.uid,
                    datatype="UUID"
                )
            )

            self._do_db_delete(
                table_name=self.RELATIONSHIP_TABLE,
                condition=EqualsCondition(
                    table_name=self.RELATIONSHIP_TABLE,
                    column="target",
                    value=deleted.uid,
                    datatype="UUID"
                )
            )

        for deleted in buffer.values():
            self._do_db_delete(
                table_name=self.MASTER_TABLE,
                condition=EqualsCondition(
                    table_name=self.MASTER_TABLE,
                    column="uid",
                    value=deleted.uid,
                    datatype="UUID"
                )
            )

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        for uid in uids:
            if isinstance(uid, uuid.UUID):
                oclass = self._get_oclass(uid)
            elif isinstance(uid, tuple) and len(uid) == 2:
                uid, oclass = uid
            else:
                raise ValueError("Invalid uid given %s" % uid)
            if uid == self.root:  # root not stored explicitly in database
                self._load_first_level()
                yield self._registry.get(uid)
                continue
            loaded = list(self._load_by_oclass(oclass=oclass,
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
            indexes=self.INDEXES[self.MASTER_TABLE]
        )
        self._do_db_create(
            table_name=self.RELATIONSHIP_TABLE,
            columns=self.COLUMNS[self.RELATIONSHIP_TABLE],
            datatypes=self.DATATYPES[self.RELATIONSHIP_TABLE],
            primary_key=self.PRIMARY_KEY[self.RELATIONSHIP_TABLE],
            foreign_key=self.FOREIGN_KEY[self.RELATIONSHIP_TABLE],
            indexes=self.INDEXES[self.RELATIONSHIP_TABLE]
        )
        # Add the dummy root element if it doesn't exist.
        # We do not want to store the actual root element since it will be
        # created by the user for every connect (root is the wrapper).
        # Adding it the dummy root here is necessary because other cuds
        # objects can have relations with the root.
        c = self._db_select(
            table_name=self.MASTER_TABLE,
            columns=["uid"],
            condition=EqualsCondition(self.MASTER_TABLE,
                                      "uid", str(uuid.UUID(int=0)),
                                      rdflib.XSD.string),
            datatypes=self.DATATYPES[self.MASTER_TABLE]
        )
        if len(list(c)) == 0:
            self._db_insert(
                table_name=self.MASTER_TABLE,
                columns=self.COLUMNS[self.MASTER_TABLE],
                values=[str(uuid.UUID(int=0)), "", False],
                datatypes=self.DATATYPES[self.MASTER_TABLE]
            )

    # OVERRIDE
    def _load_first_level(self):
        c = self._do_db_select(
            self.MASTER_TABLE,
            ["uid", "oclass"],
            EqualsCondition(self.MASTER_TABLE,
                            "first_level", True, rdflib.XSD.boolean),
            self.DATATYPES[self.MASTER_TABLE]
        )
        list(self._load_from_backend(
            map(lambda x: (x[0], get_entity(x[1])), c)
        ))

    def _load_by_oclass(self, oclass, update_registry=False, uid=None):
        """Load the cuds_object with the given oclass (+ uid).

        If uid is None return all cuds_objects with given ontology class.

        :param oclass: The oclass of the cuds_object
        :type oclass: OntologyClass
        :param uid: The uid of the Cuds to load.
        :type uid: UUID
        :param update_registry: Whether to update cuds_objects already
            present in the registry.
        :type update_registry: bool
        :return: The loaded cuds_object.
        :rtype: Cuds
        """
        # Check if oclass is given
        if (oclass is None and uid is not None) or (uid == uuid.UUID(int=0)):
            yield None  # uid given --> return iterator containing None
        if oclass is None:
            return  # uid not given --> return None

        # Check if object in registry can be used
        if not update_registry and uid is not None and uid in self._registry:
            yield self._registry.get(uid)
            return

        # gather the data needed to fetch object from the database
        tables = self._get_table_names(
            prefix=(self.CUDS_PREFIX + oclass.tblname)
        )
        if not (self.CUDS_PREFIX + oclass.tblname) in tables:
            return
        condition = EqualsCondition(self.CUDS_PREFIX + oclass.tblname,
                                    "uid", uid, "UUID") \
            if uid else None

        columns, datatypes = self._get_col_spec(oclass)

        # fetch the data
        c = self._do_db_select(
            table_name=self.CUDS_PREFIX + oclass.tblname,
            columns=columns,
            condition=condition,
            datatypes=datatypes
        )

        # transform into cuds object
        for row in c:
            kwargs = dict(zip(columns, row))
            uid = convert_to(kwargs["uid"], "UUID")
            del kwargs["uid"]
            if not update_registry and uid in self._registry:
                yield self._registry.get(uid)
                continue
            cuds_object = create_recycle(oclass=oclass,
                                         kwargs=kwargs,
                                         session=self,
                                         uid=uid,
                                         fix_neighbors=False)
            self._load_relationships(cuds_object)
            yield cuds_object

    def _load_relationships(self, cuds_object):
        """Adds the relationships in the db to the given cuds_objects.

        :param cuds_object: Adds the relationships to this cuds_object.s
        :type cuds_object: Cuds
        """
        # Fetch the data
        c = self._do_db_select(
            table_name=self.RELATIONSHIP_TABLE,
            columns=["target", "name", "target_oclass"],
            condition=EqualsCondition(
                table_name=self.RELATIONSHIP_TABLE,
                column="origin",
                value=cuds_object.uid,
                datatype="UUID"
            ),
            datatypes=self.DATATYPES[self.RELATIONSHIP_TABLE]
        )

        # update the cuds object
        for target, name, target_oclass in c:
            target_oclass = get_entity(target_oclass)
            rel = get_entity(name)

            if rel not in cuds_object._neighbors:
                cuds_object._neighbors[rel] = {}

            # Special case: target is root --> Add inverse to root
            if target == uuid.UUID(int=0):
                root_obj = self._registry.get(self.root)
                cuds_object._neighbors[rel][self.root] = root_obj.oclass
                if rel.inverse not in root_obj._neighbors:
                    root_obj._neighbors[rel.inverse] = {}
                root_obj._neighbors[rel.inverse][cuds_object.uid] = \
                    cuds_object.oclass

            # Target is not root. Simply add the relationship
            elif target != uuid.UUID(int=0):
                cuds_object._neighbors[rel][target] = target_oclass

    def _get_oclass(self, uid):
        """Get the ontology class of the given uid from the database.

        :param uid: Load the OntologyClass of this uis.
        :type uid: UUID
        :return: The ontology class.
        :rtype: OntologyClass
        """
        c = self._do_db_select(
            self.MASTER_TABLE,
            ["oclass"],
            EqualsCondition(self.MASTER_TABLE,
                            "uid", uid,
                            "UUID"),
            self.DATATYPES[self.MASTER_TABLE])
        try:
            return get_entity(next(c)[0])
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

    def _get_col_spec(self, oclass):
        attributes = oclass.attributes
        columns = [x.argname for x in attributes if x != "session"] + ["uid"]
        datatypes = dict(uid="UUID", **{x.argname: x.datatype
                                        for x in attributes if x != "session"})
        return columns, datatypes

    def _check_characters(self, *to_check):
        """Check if column or table names contain invalid characters.

        Raises:
            ValueError: Invalid character detected
        """
        forbidden_chars = [";", "\0", "\r", "\x08", "\x09", "\x1a", "\n",
                           "\r", "\"", "'", "`", "\\", "%"]
        to_check = list(to_check)
        str_to_check = str(to_check)
        for c in forbidden_chars:
            while to_check:
                s = to_check.pop()
                if isinstance(s, str):
                    s = s.encode("utf-8", "strict").decode("utf-8")
                    if c in s:
                        raise ValueError(
                            "Forbidden character %s [chr(%s)] in %s"
                            % (c, ord(c), s)
                        )
                elif isinstance(s, (list, tuple)):
                    to_check += list(s)
                elif isinstance(s, dict):
                    to_check += list(s.keys())
                    to_check += list(s.values())
                elif isinstance(s, AndCondition):
                    to_check += list(s.conditions)
                elif isinstance(s, EqualsCondition):
                    to_check += [s.table_name, s.column, s.datatype]
                elif s is None:
                    pass
                else:
                    raise ValueError("%s - %s" % (s, str_to_check))
