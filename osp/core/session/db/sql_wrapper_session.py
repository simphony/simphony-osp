"""An abstract session containing method useful for all SQL backends."""

import uuid
import rdflib
from operator import mul
from functools import reduce
from abc import abstractmethod
from osp.core.utils import create_recycle
from osp.core.ontology.datatypes import convert_to, convert_from, \
    _parse_vector_args
from osp.core.session.db.triplestore_wrapper_session import \
    TripleStoreWrapperSession
from osp.core.session.db.conditions import EqualsCondition, AndCondition
from osp.core.namespaces import get_entity
from osp.core.session.buffers import BufferContext
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology import OntologyRelationship
from osp.core.utils import CUDS_IRI_PREFIX


class SqlWrapperSession(TripleStoreWrapperSession):
    """Abstract class for an SQL DB Wrapper Session."""

    ENTITIES_TABLE = "OSP_ENTITIES"
    TYPES_TABLE = "OSP_TYPES"
    NAMESPACES_TABLE = "OSP_NAMESPACES"
    RELATIONSHIP_TABLE = "OSP_RELATIONS"
    DATA_TABLE_PREFIX = "DATA_"
    COLUMNS = {
        ENTITIES_TABLE: ["entity_idx", "ns_idx", "name"],
        TYPES_TABLE: ["cuds_idx", "type_idx"],
        RELATIONSHIP_TABLE: ["s", "p", "o"],
        NAMESPACES_TABLE: ["ns_idx", "namespace"],
        DATA_TABLE_PREFIX: ["s", "p"]
    }
    DATATYPES = {
        ENTITIES_TABLE: {
            "entity_idx": rdflib.XSD.integer,
            "ns_idx": rdflib.XSD.integer,
            "name": rdflib.XSD.string
        },
        TYPES_TABLE: {
            "cuds_idx": rdflib.XSD.integer,
            "type_idx": rdflib.XSD.integer,
        },
        RELATIONSHIP_TABLE: {"s": rdflib.XSD.integer,
                             "p": rdflib.XSD.integer,
                             "o": rdflib.XSD.integer},
        DATA_TABLE_PREFIX: {"s": rdflib.XSD.integer,
                            "p": rdflib.XSD.integer},
        NAMESPACES_TABLE: {"ns_idx": rdflib.XSD.integer,
                           "namespace": rdflib.XSD.string}
    }
    PRIMARY_KEY = {
        ENTITIES_TABLE: ["entity_idx"],
        TYPES_TABLE: ["cuds_idx", "type_idx"],
        RELATIONSHIP_TABLE: ["s", "p", "o"],
        DATA_TABLE_PREFIX: ["s", "p"],
        NAMESPACES_TABLE: ["ns_idx"]
    }
    FOREIGN_KEY = {
        ENTITIES_TABLE: {"ns_idx": (NAMESPACES_TABLE, "ns_idx")},
        TYPES_TABLE: {
            "cuds_idx": (ENTITIES_TABLE, "entity_idx"),
            "type_idx": (ENTITIES_TABLE, "entity_idx")
        },
        RELATIONSHIP_TABLE: {
            "s": (ENTITIES_TABLE, "entity_idx"),
            "p": (ENTITIES_TABLE, "entity_idx"),
            "o": (ENTITIES_TABLE, "entity_idx"),
        },
        DATA_TABLE_PREFIX: {
            "s": (ENTITIES_TABLE, "entity_idx"),
            "p": (ENTITIES_TABLE, "entity_idx")
        },
        NAMESPACES_TABLE: {}
    }
    INDEXES = {
        ENTITIES_TABLE: [["ns_idx", "name"]],
        TYPES_TABLE: [["cuds_idx"], ["type_idx"]],
        NAMESPACES_TABLE: [
            ["namespace"]
        ],
        RELATIONSHIP_TABLE: [["s", "p"],
                             ["p", "o"],
                             ["o"]],
        DATA_TABLE_PREFIX: [["s", "p"]]
    }

    def _triples(self, pattern, table_name=None, columns=None, datatypes=None):
        if table_name is columns is datatypes is None:
            if pattern[1] is pattern[2] is None:
                yield from self._triples_all_tables(pattern[0])
                return
            table_name, columns, datatypes = self._determine_table(pattern)
        condition = self._get_conditions(pattern, table_name, datatypes)
        c = self._do_db_select(
            table_name=table_name,
            columns=columns,
            condition=condition,
            datatypes=datatypes
        )
        yield from self._rows_to_triples(c, table_name, columns, datatypes)

    def _triples_all_tables(self, s):
        tables = [self.RELATIONSHIP_TABLE,
                  *self._get_table_names(prefix=self.DATA_TABLE_PREFIX)]
        for table_name in tables:
            columns, datatypes = self._determine_columns(table_name)
            yield from self._triples((s, None, None), table_name=table_name,
                                     columns=columns, datatypes=datatypes)

    def _add(self, *triples):
        for triple in triples:
            table_name, columns, datatypes = self._determine_table(triple)
            values = self._get_values(triple, table_name,
                                      columns, datatypes)
            self._do_db_insert(
                table_name=table_name,
                columns=columns,
                values=values,
                datatypes=datatypes
            )

    def _determine_table(self, triple):
        def data_table(datatype):
            return (self._get_data_table_name(o.datatype),
                    self.COLUMNS[self.DATA_TABLE_PREFIX] + ["o"],
                    dict(**self.DATATYPES[self.DATA_TABLE_PREFIX],
                         o=o.datatype))
        rel_table = (self.RELATIONSHIP_TABLE,
                     self.COLUMNS[self.RELATIONSHIP_TABLE],
                     self.DATATYPES[self.RELATIONSHIP_TABLE])
        s, p, o = triple

        # object given
        if isinstance(o, rdflib.URIRef):
            return rel_table
        if isinstance(o, rdflib.Literal) and o.datatype:
            return data_table(o.datatype)
        # predicate given
        if p is not None:
            from osp.core.namespaces import _from_iri
            predicate = _from_iri(p)
            if isinstance(predicate, OntologyRelationship):
                return rel_table
            return data_table(p.datatype)

    def _get_conditions(self, triple, table_name, datatypes):
        s, p, o = triple
        conditions = []

        if s is not None:
            s_ns, s = self._split_namespace(s)
            conditions.append(EqualsCondition(table_name, "s",
                                              s, datatypes["s"]))

        if p is not None:
            p_ns, p = self._split_namespace(p)
            conditions.append(EqualsCondition(table_name, "p",
                                              p, datatypes["p"]))

        if o is not None:
            conditions.append(EqualsCondition(table_name, "o", o,
                                              datatypes["o"]))
        return AndCondition(*conditions)

    def _split_namespace(self, iri):
        from osp.core.namespaces import _namespace_registry
        ns_iri = _namespace_registry._get_namespace_name_and_iri(iri)[1]
        return self._ns_to_idx[ns_iri], rdflib.URIRef(iri[len(ns_iri):])

    def _rows_to_triples(self, cursor, table_name, columns, datatypes):
        for row in cursor:
            s = rdflib.URIRef(self._idx_to_ns[row[0]] + row[1])
            p = rdflib.URIRef(self._idx_to_ns[row[2]] + row[3])
            if table_name == self.RELATIONSHIP_TABLE:
                o = rdflib.URIRef(self._idx_to_ns[row[4]] + row[5])
                yield s, p, o
            yield s, p, rdflib.Literal(o, datatype=datatypes[columns[4]])

    def _load_by_iri(self, iri):
        raise NotImplementedError

    def _remove(self, pattern):
        raise NotImplementedError

    @abstractmethod
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, foreign_key, indexes):
        """Create a new table with the given name and columns.

        Args:
            table_name (str): The name of the new table.
            columns (List[str]): The name of the columns.
            datatypes (Dict): Maps columns to datatypes specified in ontology.
            primary_key (List[str]): List of columns that belong to the
                primary key.
            foreign_key (Dict[str, Tuple[str (table), str (column)]]): mapping
                from column to other tables column.
            indexes (List(str)): List of indexes. Each index is a list of
                column names for which an index should be built.
        """

    @abstractmethod
    def _db_select(self, table_name, columns, condition, datatypes):
        """Get data from the table of the given names.

        Args:
            table_name(str): The name of the table.
            columns(List[str]): The names of the columns.
            condition(Condition): A condition for filtering.
            datatypes(Dict): Maps column names to datatypes.
        """

    @abstractmethod
    def _db_insert(self, table_name, columns, values, datatypes):
        """Insert data into the table with the given name.

        Args:
           table_name(str): The table name.
            columns(List[str]): The names of the columns.
            values(List[Any]): The data to insert.
            datatypes(Dict): Maps column names to datatypes.
        """

    @abstractmethod
    def _db_update(self, table_name, columns, values, condition, datatypes):
        """Update the data in the given table.

        Args:
            table_name(str): The name of the table.
            columns(List[str]): The names of the columns.
            values(List[Any]): The new updated values.
            condition(str): Only update rows that satisfy the condition.
            datatypes(Dict): Maps column names to datatypes.
        """

    @abstractmethod
    def _db_delete(self, table_name, condition):
        """Delete data from the given table.

        Args:
            table_name(str): The name of the table.
            condition(str): Delete rows that satisfy the condition.
        """

    @abstractmethod
    def _get_table_names(self, prefix):
        """Get all tables in the database with the given prefix.

        Args:
            prefix(str): Only return tables with the given prefix
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

        Args:
            columns(List[str]): The columns to expand.
            datatypes(Dict[str, str]): The datatypes for each column.
                VECTORs will be expanded.
            values(List[Any], optional, optional): The values to expand,
                defaults to None

        Returns:
            Tuple[List[str], Dict[str, str], (List[Any])]: The expanded
                columns, datatypes (and values, if given)
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

        Args:
            columns(List[str]): The expanded columns of the database
            datatypes(dict): The datatype for each column
            rows(Iterator[List[Any]]): The rows fetched from the database

        Returns:
            Iterator[List[Any]]: The rows with vectors being a single item
                in each row.
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

        Args:
            column(str): The currect column to consider in the contraction
            value(Any): The value of the column
            datatypes(Dict): Maps a datatype to each column
            temp_vec(List[float]): The elements of the current vector.
            old_vector_datatype(str): The vector datatype of the old iteration.

        Returns:
            Tuple[str, bool]: The new vector datatype and whether the current
                column corresponds to a vector.
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

    # def _clear_database(self):
    #     """Delete the contents of every table."""
    #     self._init_transaction()
    #     try:
    #         # clear local datastructure
    #         from osp.core.namespaces import cuba
    #         self._reset_buffers(BufferContext.USER)
    #         root = self._registry.get(self.root)

    #         # if there is something to remove
    #         if root.get(rel=cuba.relationship):
    #             root.remove(rel=cuba.relationship)
    #             for uid in list(self._registry.keys()):
    #                 if uid != self.root:
    #                     self._delete_cuds_triples(self._registry.get(uid))
    #             self._reset_buffers(BufferContext.USER)

    #             # delete the data
    #             for table_name in self._get_table_names(
    #                     SqlWrapperSession.CUDS_PREFIX):
    #                 self._do_db_delete(table_name, None)
    #             self._do_db_delete(self.RELATIONSHIP_TABLE, None)
    #             self._do_db_delete(self.MASTER_TABLE, None)
    #             self._initialize()
    #             self._commit()
    #     except Exception as e:
    #         self._rollback_transaction()
    #         raise e

    def _default_create(self, table_name):
        self._do_db_create(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            datatypes=self.DATATYPES[table_name],
            primary_key=self.PRIMARY_KEY[table_name],
            foreign_key=self.FOREIGN_KEY[table_name],
            indexes=self.INDEXES[table_name]
        )

    def _default_select(self, table_name, condition=None):
        return self._do_db_select(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            condition=condition,
            datatypes=self.DATATYPES[table_name]
        )

    def _default_insert(self, table_name, values):
        self._do_db_insert(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            values=values,
            datatypes=self.DATATYPES[table_name]
        )

    # OVERRIDE
    def _initialize(self):
        self._default_create(self.ENTITIES_TABLE)
        self._default_create(self.TYPES_TABLE)
        self._default_create(self.NAMESPACES_TABLE)
        self._default_create(self.RELATIONSHIP_TABLE)
        self._idx_to_ns = dict(self._default_select(self.NAMESPACES_TABLE))
        if not self._idx_to_ns:  # initialize table contents
            self._default_insert(self.ENTITIES_TABLE,
                                 [0, 0, uuid.UUID(int=0).hex])
            self._default_insert(self.NAMESPACES_TABLE, [0, CUDS_IRI_PREFIX])
            self._idx_to_ns = {0: rdflib.URIRef(CUDS_IRI_PREFIX)}
        self._ns_to_idx = {v: k for k, v in self._idx_to_ns.items()}

    def _convert_values(self, rows, columns, datatypes):
        """Convert the values in the database to the correct datatype.

        Args:
            rows(Iterator[Iterator[Any]]): The rows of the database
            columns(List[str]): The corresponding columns
            datatypes(Dict[str, str]): Mapping from column to datatype

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

        Args:
            *to_check: The names to check.

        Raises:
            ValueError: Invalid character detected.

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
