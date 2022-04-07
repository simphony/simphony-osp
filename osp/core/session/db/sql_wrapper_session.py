"""An abstract session containing method useful for all SQL backends."""

import uuid
from abc import abstractmethod

import rdflib

from osp.core.ontology import OntologyRelationship
from osp.core.ontology.datatypes import convert_from, to_uid
from osp.core.session.buffers import BufferContext
from osp.core.session.db.sql_migrate import check_supported_schema_version
from osp.core.session.db.sql_util import (
    AndCondition,
    EqualsCondition,
    JoinCondition,
    SqlQuery,
    check_characters,
    contract_vector_values,
    determine_datatype,
    expand_vector_cols,
    expand_vector_condition,
    get_data_table_name,
)
from osp.core.session.db.triplestore_wrapper_session import (
    TripleStoreWrapperSession,
)
from osp.core.utils.general import CUDS_IRI_PREFIX, iri_from_uid


class SqlWrapperSession(TripleStoreWrapperSession):
    """Abstract class for an SQL DB Wrapper Session."""

    TRIPLESTORE_COLUMNS = ["s", "p", "o"]
    CUDS_TABLE = "OSP_V1_CUDS"
    ENTITIES_TABLE = "OSP_V1_ENTITIES"
    TYPES_TABLE = "OSP_V1_TYPES"
    NAMESPACES_TABLE = "OSP_V1_NAMESPACES"
    RELATIONSHIP_TABLE = "OSP_V1_RELATIONS"
    DATA_TABLE_PREFIX = "DATA_V1_"
    COLUMNS = {
        CUDS_TABLE: ["cuds_idx", "uid"],
        ENTITIES_TABLE: ["entity_idx", "ns_idx", "name"],
        TYPES_TABLE: ["s", "o"],
        RELATIONSHIP_TABLE: TRIPLESTORE_COLUMNS,
        NAMESPACES_TABLE: ["ns_idx", "namespace"],
        DATA_TABLE_PREFIX: TRIPLESTORE_COLUMNS,
    }
    DATATYPES = {
        CUDS_TABLE: {"cuds_idx": rdflib.XSD.integer, "uid": "UID"},
        ENTITIES_TABLE: {
            "entity_idx": rdflib.XSD.integer,
            "ns_idx": rdflib.XSD.integer,
            "name": rdflib.XSD.string,
        },
        TYPES_TABLE: {
            "s": rdflib.XSD.integer,
            "o": rdflib.XSD.integer,
        },
        RELATIONSHIP_TABLE: {
            "s": rdflib.XSD.integer,
            "p": rdflib.XSD.integer,
            "o": rdflib.XSD.integer,
        },
        DATA_TABLE_PREFIX: {"s": rdflib.XSD.integer, "p": rdflib.XSD.integer},
        NAMESPACES_TABLE: {
            "ns_idx": rdflib.XSD.integer,
            "namespace": rdflib.XSD.string,
        },
    }
    PRIMARY_KEY = {
        CUDS_TABLE: ["cuds_idx"],
        ENTITIES_TABLE: ["entity_idx"],
        TYPES_TABLE: ["s", "o"],
        RELATIONSHIP_TABLE: TRIPLESTORE_COLUMNS,
        DATA_TABLE_PREFIX: [],  # TODO TRIPLESTORE_COLUMNS,
        NAMESPACES_TABLE: ["ns_idx"],
    }
    GENERATE_PK = {CUDS_TABLE, ENTITIES_TABLE, NAMESPACES_TABLE}
    FOREIGN_KEY = {
        CUDS_TABLE: {},
        ENTITIES_TABLE: {"ns_idx": (NAMESPACES_TABLE, "ns_idx")},
        TYPES_TABLE: {
            "s": (CUDS_TABLE, "cuds_idx"),
            "o": (ENTITIES_TABLE, "entity_idx"),
        },
        RELATIONSHIP_TABLE: {
            "s": (CUDS_TABLE, "cuds_idx"),
            "p": (ENTITIES_TABLE, "entity_idx"),
            "o": (CUDS_TABLE, "cuds_idx"),
        },
        DATA_TABLE_PREFIX: {
            "s": (CUDS_TABLE, "cuds_idx"),
            "p": (ENTITIES_TABLE, "entity_idx"),
        },
        NAMESPACES_TABLE: {},
    }
    INDEXES = {
        CUDS_TABLE: [["uid"]],
        ENTITIES_TABLE: [["ns_idx", "name"]],
        TYPES_TABLE: [["s"], ["o"]],
        NAMESPACES_TABLE: [["namespace"]],
        RELATIONSHIP_TABLE: [["s", "p"], ["p", "o"]],
        DATA_TABLE_PREFIX: [["s", "p"]],
    }

    check_schema = check_supported_schema_version

    # GET_TRIPLES

    def _triples(self, pattern):
        for q, t, dt in self._queries(pattern):
            c = self._do_db_select(q)
            yield from self._rows_to_triples(
                cursor=c, table_name=t, object_datatype=dt
            )

    def _triples_for_subject(self, iri, tables=None, exclude=()):
        for q, t, dt in self._queries_for_subject(iri, tables, exclude):
            c = self._do_db_select(q)
            yield from self._rows_to_triples(
                cursor=c, table_name=t, object_datatype=dt
            )

    def _queries(
        self, pattern, table_name=None, object_datatype=None, mode="select"
    ):
        func = {
            "select": self._construct_query,
            "delete": self._construct_remove_condition,
        }
        if table_name is None:
            if pattern[1] is pattern[2] is None:
                yield from self._queries_for_subject(pattern[0], mode=mode)
                return
            table_name, datatypes = self._determine_table(pattern)
            object_datatype = datatypes["o"]

        # Construct query
        yield (
            func[mode](pattern, table_name, object_datatype),
            table_name,
            object_datatype,
        )

    def _queries_for_subject(self, s, tables=None, exclude=(), mode="select"):
        tables = set(
            tables
            or [
                self.RELATIONSHIP_TABLE,
                self.TYPES_TABLE,
                *self._get_table_names(prefix=self.DATA_TABLE_PREFIX),
            ]
        ) - set(exclude)
        for table_name in tables:
            object_datatype = rdflib.XSD.integer
            if table_name.startswith(self.DATA_TABLE_PREFIX):
                object_datatype = determine_datatype(table_name)
            yield from self._queries(
                pattern=(s, None, None),
                table_name=table_name,
                object_datatype=object_datatype,
                mode=mode,
            )

    def _determine_table(self, triple):
        def data_table(datatype):
            return (
                get_data_table_name(datatype),
                dict(**self.DATATYPES[self.DATA_TABLE_PREFIX], o=datatype),
            )

        rel_table = (
            self.RELATIONSHIP_TABLE,
            self.DATATYPES[self.RELATIONSHIP_TABLE],
        )
        types_table = (self.TYPES_TABLE, self.DATATYPES[self.TYPES_TABLE])
        s, p, o = triple

        # object given
        if isinstance(o, rdflib.URIRef) and self._is_cuds_iri(o):
            return rel_table
        if isinstance(o, rdflib.URIRef):
            return types_table
        if isinstance(o, rdflib.Literal) and o.datatype:
            return data_table(o.datatype)
        # predicate given
        if p == rdflib.RDF.type:
            return types_table
        if p is not None:
            from osp.core.namespaces import from_iri

            predicate = from_iri(p)
            if isinstance(predicate, OntologyRelationship):
                return rel_table
            return data_table(predicate.datatype or rdflib.XSD.string)

    def _construct_query(self, pattern, table_name, object_datatype):
        q = SqlQuery(
            self.CUDS_TABLE,
            columns=self.COLUMNS[self.CUDS_TABLE][1:],
            datatypes=self.DATATYPES[self.CUDS_TABLE],
            alias="ts",
        ).where(JoinCondition(table_name, "s", "ts", "cuds_idx"))

        if table_name != self.TYPES_TABLE:
            q = q.join(
                self.ENTITIES_TABLE,
                columns=self.COLUMNS[self.ENTITIES_TABLE][1:],
                datatypes=self.DATATYPES[self.ENTITIES_TABLE],
                alias="tp",
            ).where(JoinCondition(table_name, "p", "tp", "entity_idx"))
        else:
            q = q.join(
                self.ENTITIES_TABLE,
                columns=self.COLUMNS[self.ENTITIES_TABLE][1:],
                datatypes=self.DATATYPES[self.ENTITIES_TABLE],
                alias="to",
            ).where(JoinCondition(table_name, "o", "to", "entity_idx"))

        if table_name == self.RELATIONSHIP_TABLE:
            q = q.join(
                self.CUDS_TABLE,
                columns=self.COLUMNS[self.CUDS_TABLE][1:],
                datatypes=self.DATATYPES[self.CUDS_TABLE],
                alias="to",
            ).where(JoinCondition(table_name, "o", "to", "cuds_idx"))

        cols, dtypes = [], {}
        if table_name.startswith(self.DATA_TABLE_PREFIX):
            cols, dtypes = ["o"], {"o": object_datatype}
        q = q.join(table_name, cols, dtypes)
        q = q.where(self._get_conditions(pattern, table_name, object_datatype))
        return q

    def _get_conditions(self, triple, table_name, object_datatype):
        conditions = []
        s, p, o = triple

        if s is not None:
            uid = to_uid(s)
            conditions += [EqualsCondition("ts", "uid", uid, "UID")]

        if p is not None and table_name != self.TYPES_TABLE:
            ns_idx, name = self._split_namespace(p)
            conditions += [
                EqualsCondition("tp", "ns_idx", ns_idx, rdflib.XSD.integer),
                EqualsCondition("tp", "name", name, rdflib.XSD.string),
            ]

        if o is not None and table_name == self.RELATIONSHIP_TABLE:
            uid = self._split_namespace(o)
            conditions += [EqualsCondition("to", "uid", uid, "UID")]

        elif o is not None and table_name == self.TYPES_TABLE:
            ns_idx, name = self._split_namespace(o)
            conditions += [
                EqualsCondition("to", "ns_idx", ns_idx, rdflib.XSD.integer),
                EqualsCondition("to", "name", name, rdflib.XSD.string),
            ]

        elif o is not None:
            conditions += [
                EqualsCondition(table_name, "o", o.toPython(), object_datatype)
            ]

        return AndCondition(*conditions)

    def _split_namespace(self, iri):
        if iri.startswith(CUDS_IRI_PREFIX):
            return uuid.UUID(hex=iri[len(CUDS_IRI_PREFIX) :])
        elif self._is_cuds_iri(iri):
            return iri
        from osp.core.ontology.namespace_registry import namespace_registry

        ns_iri = namespace_registry._get_namespace_name_and_iri(iri)[1]
        return self._get_ns_idx(ns_iri), str(iri[len(ns_iri) :])

    def _get_ns_idx(self, ns_iri):
        ns_iri = str(ns_iri)
        if ns_iri not in self._ns_to_idx:
            self._do_db_insert(
                table_name=self.NAMESPACES_TABLE,
                columns=["namespace"],
                values=[str(ns_iri)],
                datatypes=self.DATATYPES[self.NAMESPACES_TABLE],
            )
            self._load_namespace_indexes()
        return self._ns_to_idx[ns_iri]

    def _get_ns(self, ns_idx):
        if ns_idx not in self._idx_to_ns:
            self._load_namespace_indexes()
        return self._idx_to_ns[ns_idx]

    def _rows_to_triples(self, cursor, table_name, object_datatype):
        for row in cursor:
            s = rdflib.URIRef(iri_from_uid(row[0]))
            x = rdflib.URIRef(self._get_ns(row[1]) + row[2])
            if table_name == self.TYPES_TABLE:
                yield s, rdflib.RDF.type, x
            elif table_name == self.RELATIONSHIP_TABLE:
                o = rdflib.URIRef(iri_from_uid(row[3]))
                yield s, x, o
            else:
                yield s, x, rdflib.Literal(row[3], datatype=object_datatype)

    # LOAD

    def _load_triples_for_iri(self, iri):
        triples = set(
            self._triples_for_subject(iri, tables=(self.RELATIONSHIP_TABLE,))
        )
        type_triples_of_neighbors = set()
        for s, p, o in triples:
            type_triples_of_neighbors |= set(
                self._triples((o, rdflib.RDF.type, None))
            )

        triples |= set(
            self._triples_for_subject(iri, exclude=(self.RELATIONSHIP_TABLE,))
        )
        return triples, type_triples_of_neighbors

    # ADD

    def _add(self, *triples):
        for triple in triples:
            table_name, datatypes = self._determine_table(triple)
            values = self._get_values(triple, table_name)
            columns = self.TRIPLESTORE_COLUMNS
            if table_name == self.TYPES_TABLE:
                columns = self.COLUMNS[self.TYPES_TABLE]
            self._do_db_insert(
                table_name=table_name,
                columns=columns,
                values=values,
                datatypes=datatypes,
            )

    def _get_values(self, triple, table_name):
        s, p, o = triple
        s = self._get_cuds_idx(self._split_namespace(s))
        if table_name == self.TYPES_TABLE:
            return s, self._get_entity_idx(*self._split_namespace(o))
        p = self._get_entity_idx(*self._split_namespace(p))
        o = o.toPython()
        if table_name == self.RELATIONSHIP_TABLE:
            o = self._get_cuds_idx(self._split_namespace(o))
        return s, p, o

    def _get_cuds_idx(self, uid):
        c = self._default_select(
            self.CUDS_TABLE,
            condition=EqualsCondition(
                self.CUDS_TABLE, "uid", uid, datatype="UID"
            ),
        )
        for cuds_idx, uid in c:
            return cuds_idx
        return self._do_db_insert(
            table_name=self.CUDS_TABLE,
            columns=["uid"],
            values=[uid],
            datatypes=self.DATATYPES[self.CUDS_TABLE],
        )

    def _get_entity_idx(self, ns_idx, name):
        c = self._default_select(
            self.ENTITIES_TABLE,
            condition=AndCondition(
                EqualsCondition(
                    self.ENTITIES_TABLE,
                    "ns_idx",
                    ns_idx,
                    datatype=rdflib.XSD.integer,
                ),
                EqualsCondition(
                    self.ENTITIES_TABLE,
                    "name",
                    name,
                    datatype=rdflib.XSD.string,
                ),
            ),
        )
        for entity_idx, ns_idx, name in c:
            return entity_idx
        return self._do_db_insert(
            table_name=self.ENTITIES_TABLE,
            columns=["ns_idx", "name"],
            values=[ns_idx, name],
            datatypes=self.DATATYPES[self.ENTITIES_TABLE],
        )

    # REMOVE

    def _remove(self, pattern):
        for c, t, _ in self._queries(pattern, mode="delete"):
            self._do_db_delete(t, c)

    def _construct_remove_condition(self, pattern, table, object_datatype):
        conditions = list()
        s, p, o = pattern
        if s is not None:
            s = self._get_cuds_idx(self._split_namespace(s))
            conditions += [
                EqualsCondition(
                    table, column="s", value=s, datatype=rdflib.XSD.integer
                )
            ]
        if table == self.TYPES_TABLE:
            if o is not None:
                o = self._get_entity_idx(*self._split_namespace(o))
                conditions += [
                    EqualsCondition(
                        table, column="o", value=o, datatype=rdflib.XSD.integer
                    )
                ]
            return AndCondition(*conditions)

        if p is not None:
            p = self._get_entity_idx(*self._split_namespace(p))
            conditions += [
                EqualsCondition(
                    table, column="p", value=p, datatype=rdflib.XSD.integer
                )
            ]

        if o is not None:
            o = o.toPython()
            if table == self.RELATIONSHIP_TABLE:
                o = self._get_cuds_idx(self._split_namespace(o))
            conditions += [
                EqualsCondition(
                    table, column="o", value=o, datatype=object_datatype
                )
            ]
        return AndCondition(*conditions)

    def _load_namespace_indexes(self):
        self._idx_to_ns = dict(self._default_select(self.NAMESPACES_TABLE))
        self._ns_to_idx = {v: k for k, v in self._idx_to_ns.items()}

    # INITIALIZE
    # OVERRIDE
    def _initialize(self):
        self.check_schema()
        self._default_create(self.NAMESPACES_TABLE)
        self._default_create(self.CUDS_TABLE)
        self._default_create(self.ENTITIES_TABLE)
        self._default_create(self.TYPES_TABLE)
        self._default_create(self.RELATIONSHIP_TABLE)
        self._load_namespace_indexes()

        from osp.core.utils.general import get_custom_datatypes

        datatypes = get_custom_datatypes() | {
            rdflib.XSD.integer,
            rdflib.XSD.boolean,
            rdflib.XSD.float,
            rdflib.XSD.string,
        }
        for datatype in datatypes:
            self._do_db_create(
                table_name=get_data_table_name(datatype),
                columns=self.TRIPLESTORE_COLUMNS,
                datatypes={
                    "o": datatype,
                    **self.DATATYPES[self.DATA_TABLE_PREFIX],
                },
                primary_key=self.PRIMARY_KEY[self.DATA_TABLE_PREFIX],
                generate_pk=self.DATA_TABLE_PREFIX in self.GENERATE_PK,
                foreign_key=self.FOREIGN_KEY[self.DATA_TABLE_PREFIX],
                indexes=self.INDEXES[self.DATA_TABLE_PREFIX],
            )

    @abstractmethod
    def _db_create(
        self,
        table_name,
        columns,
        datatypes,
        primary_key,
        generate_pk,
        foreign_key,
        indexes,
    ):
        """Create a new table with the given name and columns.

        Args:
            table_name (str): The name of the new table.
            columns (List[str]): The name of the columns.
            datatypes (Dict): Maps columns to datatypes specified in ontology.
            primary_key (List[str]): List of columns that belong to the
                primary key.
            foreign_key (Dict[str, Tuple[str (table), str (column)]]): mapping
                from column to other tables column.
            generate_pk (bool): Whether primary key should be automatically
                generated by the database
                (e.g. be an automatically incrementing integer).
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

        Returns:
            The auto-generated primary key of the inserted row,
            if such exists.
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
    def _db_delete(self, table_name):
        """Drop the entire table.

        Args:
            table_name(str): The name of the table.
        """

    @abstractmethod
    def _db_drop(self, table_name):
        """Drop the table with the given name.

        Args:
            table_name(str): The name of the table.
        """

    @abstractmethod
    def _get_table_names(self, prefix):
        """Get all tables in the database with the given prefix.

        Args:
            prefix(str): Only return tables with the given prefix
        """

    def _do_db_create(
        self,
        table_name,
        columns,
        datatypes,
        primary_key,
        generate_pk,
        foreign_key,
        indexes,
    ):
        """Call db_create but expand the vectors first."""
        columns, datatypes = expand_vector_cols(columns, datatypes)
        check_characters(
            table_name, columns, datatypes, primary_key, foreign_key, indexes
        )
        self._db_create(
            table_name,
            columns,
            datatypes,
            primary_key,
            generate_pk,
            foreign_key,
            indexes,
        )

    def _do_db_drop(self, table_name):
        """Call _db_drop but check the characters first."""
        check_characters(table_name)
        self._db_drop(
            table_name,
        )

    def _do_db_select(self, query):
        """Call db_select but consider vectors."""
        rows = self._db_select(query)
        yield from contract_vector_values(rows, query)

    def _do_db_insert(self, table_name, columns, values, datatypes):
        """Call db_insert but expand vectors."""
        columns, datatypes, values = expand_vector_cols(
            columns, datatypes, values
        )
        values = [
            convert_from(v, datatypes.get(c)) for c, v in zip(columns, values)
        ]
        check_characters(table_name, columns, datatypes)
        return self._db_insert(table_name, columns, values, datatypes)

    def _do_db_update(self, table_name, columns, values, condition, datatypes):
        """Call db_update but expand vectors."""
        columns, datatypes, values = expand_vector_cols(
            columns, datatypes, values
        )
        condition = expand_vector_condition(condition)
        values = [
            convert_from(v, datatypes.get(c)) for c, v in zip(columns, values)
        ]
        check_characters(table_name, columns, condition, datatypes)
        self._db_update(table_name, columns, values, condition, datatypes)

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
            generate_pk=table_name in self.GENERATE_PK,
            foreign_key=self.FOREIGN_KEY[table_name],
            indexes=self.INDEXES[table_name],
        )

    def _default_select(self, table_name, condition=None):
        query = SqlQuery(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            datatypes=self.DATATYPES[table_name],
        ).where(condition)
        return self._do_db_select(query)

    def _default_insert(self, table_name, values):
        self._do_db_insert(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            values=values,
            datatypes=self.DATATYPES[table_name],
        )

    def _clear_database(self):
        """Delete the contents of every table."""
        self._init_transaction()
        try:
            # clear local datastructure
            from osp.core.namespaces import cuba

            self._reset_buffers(BufferContext.USER)
            root = self._registry.get(self.root)

            # Delete relationships of root.
            if root.get(rel=cuba.relationship):
                root.remove(rel=cuba.relationship)

            for uid in list(self._registry.keys()):
                if uid != self.root:
                    self._delete_cuds_triples(self._registry.get(uid))
            self._reset_buffers(BufferContext.USER)

            # delete the data
            for table_name in self._get_table_names(
                SqlWrapperSession.DATA_TABLE_PREFIX
            ):
                self._do_db_delete(table_name, None)
            self._do_db_delete(self.TYPES_TABLE, None)
            self._do_db_delete(self.RELATIONSHIP_TABLE, None)
            self._do_db_delete(self.CUDS_TABLE, None)
            self._do_db_delete(self.ENTITIES_TABLE, None)
            self._do_db_delete(self.NAMESPACES_TABLE, None)

            self._initialize()
            self._commit()
        except Exception as e:
            self._rollback_transaction()
            raise e

    def _sparql(self, query_string):
        """Perform a sparql query on the database."""
        raise NotImplementedError()
