"""An abstract session containing method useful for all SQL backends."""

import uuid
import rdflib
from abc import abstractmethod
from osp.core.utils import create_recycle
from osp.core.ontology.datatypes import convert_from
from osp.core.session.db.triplestore_wrapper_session import \
    TripleStoreWrapperSession
from osp.core.namespaces import get_entity
from osp.core.session.buffers import BufferContext
from osp.core.ontology import OntologyRelationship
from osp.core.utils import CUDS_IRI_PREFIX
from osp.core.session.db.sql_util import SqlQuery, EqualsCondition, \
    AndCondition, JoinCondition, expand_vector_cols, \
    contract_vector_values, expand_vector_condition, check_characters


class SqlWrapperSession(TripleStoreWrapperSession):
    """Abstract class for an SQL DB Wrapper Session."""

    TRIPLESTORE_COLUMNS = ["s", "p", "o"]
    CUDS_TABLE = "OSP_CUDS"
    ENTITIES_TABLE = "OSP_ENTITIES"
    TYPES_TABLE = "OSP_TYPES"
    NAMESPACES_TABLE = "OSP_NAMESPACES"
    RELATIONSHIP_TABLE = "OSP_RELATIONS"
    DATA_TABLE_PREFIX = "DATA_"
    COLUMNS = {
        CUDS_TABLE: ["cuds_idx", "uid"],
        ENTITIES_TABLE: ["entity_idx", "ns_idx", "name"],
        TYPES_TABLE: ["cuds_idx", "type_idx"],
        RELATIONSHIP_TABLE: TRIPLESTORE_COLUMNS,
        NAMESPACES_TABLE: ["ns_idx", "namespace"],
        DATA_TABLE_PREFIX: TRIPLESTORE_COLUMNS
    }
    DATATYPES = {
        CUDS_TABLE: {
            "cuds_idx": rdflib.XSD.integer,
            "uid": "UUID"
        },
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
        CUDS_TABLE: ["cuds_idx"],
        ENTITIES_TABLE: ["entity_idx"],
        TYPES_TABLE: ["cuds_idx", "type_idx"],
        RELATIONSHIP_TABLE: ["s", "p", "o"],
        DATA_TABLE_PREFIX: ["s", "p"],
        NAMESPACES_TABLE: ["ns_idx"]
    }
    FOREIGN_KEY = {
        CUDS_TABLE: {},
        ENTITIES_TABLE: {"ns_idx": (NAMESPACES_TABLE, "ns_idx")},
        TYPES_TABLE: {
            "cuds_idx": (CUDS_TABLE, "cuds_idx"),
            "type_idx": (ENTITIES_TABLE, "entity_idx")
        },
        RELATIONSHIP_TABLE: {
            "s": (CUDS_TABLE, "cuds_idx"),
            "p": (ENTITIES_TABLE, "entity_idx"),
            "o": (CUDS_TABLE, "cuds_idx"),
        },
        DATA_TABLE_PREFIX: {
            "s": (CUDS_TABLE, "cuds_idx"),
            "p": (ENTITIES_TABLE, "entity_idx")
        },
        NAMESPACES_TABLE: {}
    }
    INDEXES = {
        CUDS_TABLE: [["uid"]],
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

    def _triples(self, pattern, table_name=None, datatypes=None):
        if table_name is datatypes is None:
            if pattern[1] is pattern[2] is None:
                yield from self._triples_all_tables(pattern[0])
                return
            table_name, datatypes = self._determine_table(pattern)
        q = self._construct_query(pattern, table_name, datatypes)
        c = self._do_db_select(q)
        yield from self._rows_to_triples(c, table_name, datatypes)

    def _triples_all_tables(self, s):
        tables = [self.RELATIONSHIP_TABLE,
                  *self._get_table_names(prefix=self.DATA_TABLE_PREFIX)]
        for table_name in tables:
            datatypes = self._determine_datatypes(table_name)
            yield from self._triples((s, None, None), table_name=table_name,
                                     datatypes=datatypes)

    def _determine_table(self, triple):
        def data_table(datatype):
            return (self._get_data_table_name(o.datatype),
                    dict(**self.DATATYPES[self.DATA_TABLE_PREFIX],
                         o=o.datatype))
        rel_table = (self.RELATIONSHIP_TABLE,
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

    def _determine_datatypes(self, table_name):
        pass

    def _construct_query(self, pattern, table_name, datatypes):
        q = SqlQuery(table_name, [], {}).join(
            self.CUDS_TABLE, columns=self.COLUMNS[self.CUDS_TABLE][1:],
            datatypes=self.DATATYPES[self.CUDS_TABLE], alias="ts"
        ).join(
            self.ENTITIES_TABLE, columns=self.COLUMNS[self.ENTITIES_TABLE][1:],
            datatypes=self.DATATYPES[self.ENTITIES_TABLE], alias="tp"
        ).where(AndCondition(
            JoinCondition(table_name, "s", "ts", "cuds_idx"),
            JoinCondition(table_name, "p", "tp", "entity_idx")
        ))

        if table_name == self.RELATIONSHIP_TABLE:
            q = q.join(
                self.CUDS_TABLE, columns=self.COLUMNS[self.CUDS_TABLE][1:],
                datatypes=self.DATATYPES[self.CUDS_TABLE], alias="to"
            ).where(JoinCondition(table_name, "o", "to", "cuds_idx"))

        q = q.where(self._get_conditions(pattern, table_name, datatypes["o"]))
        return q

    def _get_conditions(self, triple, table_name, object_datatype):
        conditions = []
        s, p, o = triple

        if s is not None:
            uid = self._split_namespace(s)
            conditions += [EqualsCondition("ts", "uid", uid, "UUID")]

        if p is not None:
            ns_idx, name = self._split_namespace(p)
            conditions += [
                EqualsCondition("tp", "ns_idx", ns_idx, rdflib.XSD.integer),
                EqualsCondition("tp", "name", name, rdflib.XSD.string)
            ]

        if o is not None and table_name == self.RELATIONSHIP_TABLE:
            uid = self._split_namespace(o)
            conditions += [EqualsCondition("to", "uid", uid, "UUID")]

        elif o is not None:
            conditions += [
                EqualsCondition(table_name, "o", o, object_datatype)]

        return AndCondition(*conditions)

    def _split_namespace(self, iri):
        if iri.startswith(CUDS_IRI_PREFIX):
            return uuid.UUID(hex=iri[len(CUDS_IRI_PREFIX):])
        from osp.core.namespaces import _namespace_registry
        ns_iri = _namespace_registry._get_namespace_name_and_iri(iri)[1]
        return self._ns_to_idx[ns_iri], str(iri[len(ns_iri):])

    def _rows_to_triples(self, cursor, table_name, datatypes):
        for row in cursor:
            s = rdflib.URIRef(self._idx_to_ns[row[0]] + row[1])
            p = rdflib.URIRef(self._idx_to_ns[row[2]] + row[3])
            if table_name == self.RELATIONSHIP_TABLE:
                o = rdflib.URIRef(self._idx_to_ns[row[4]] + row[5])
                yield s, p, o
            yield s, p, rdflib.Literal(o, datatype=datatypes["o"])

    def _load_by_iri(self, iri):
        raise NotImplementedError

    def _add(self, *triples):
        for triple in triples:
            table_name, datatypes = self._determine_table(triple)
            values = self._get_values(triple, table_name, datatypes)
            self._do_db_insert(
                table_name=table_name,
                columns=self.TRIPLESTORE_COLUMNS,
                values=values,
                datatypes=datatypes
            )

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
    def _db_select(self, query):
        """Get data from the table of the given names.

        Args:
            query (SqlQuery): A object describing the SQL query.
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

    def _do_db_create(self, table_name, columns, datatypes,
                      primary_key, foreign_key, indexes):
        """Call db_create but expand the vectors first."""
        columns, datatypes = expand_vector_cols(columns, datatypes)
        check_characters(table_name, columns, datatypes,
                         primary_key, foreign_key, indexes)
        self._db_create(table_name, columns, datatypes,
                        primary_key, foreign_key, indexes)

    def _do_db_select(self, query):
        """Call db_select but consider vectors."""
        rows = self._db_select(query)
        yield from contract_vector_values(rows, query)

    def _do_db_insert(self, table_name, columns, values, datatypes):
        """Call db_insert but expand vectors."""
        columns, datatypes, values = expand_vector_cols(columns,
                                                        datatypes,
                                                        values)
        values = [convert_from(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        check_characters(table_name, columns, datatypes)
        self._db_insert(table_name, columns, values, datatypes)

    def _do_db_update(self, table_name, columns,
                      values, condition, datatypes):
        """Call db_update but expand vectors."""
        columns, datatypes, values = expand_vector_cols(columns,
                                                        datatypes,
                                                        values)
        condition = expand_vector_condition(condition)
        values = [convert_from(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        check_characters(table_name, columns,
                               condition, datatypes)
        self._db_update(table_name, columns,
                        values, condition, datatypes)

    def _do_db_delete(self, table_name, condition):
        """Call _db_delete but expand vectors."""
        check_characters(table_name, condition)
        condition = expand_vector_condition(condition)
        self._db_delete(table_name, condition)

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
        query = SqlQuery(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            datatypes=self.DATATYPES[table_name]
        ).where(condition)
        return self._do_db_select(query)

    def _default_insert(self, table_name, values):
        self._do_db_insert(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            values=values,
            datatypes=self.DATATYPES[table_name]
        )

    # OVERRIDE
    def _initialize(self):
        self._default_create(self.CUDS_TABLE)
        self._default_create(self.ENTITIES_TABLE)
        self._default_create(self.TYPES_TABLE)
        self._default_create(self.NAMESPACES_TABLE)
        self._default_create(self.RELATIONSHIP_TABLE)
        self._idx_to_ns = dict(self._default_select(self.NAMESPACES_TABLE))
        if not self._idx_to_ns:  # initialize table contents
            self._default_insert(self.ENTITIES_TABLE,
                                 [0, 0, uuid.UUID(int=0).hex])
            self._idx_to_ns = {0: rdflib.URIRef(CUDS_IRI_PREFIX)}
        self._ns_to_idx = {v: k for k, v in self._idx_to_ns.items()}

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
