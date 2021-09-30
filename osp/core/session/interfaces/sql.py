"""An abstract session containing method useful for all SQL backends."""

from abc import abstractmethod
from typing import Any, Dict, List, Iterable, Iterator, Optional, Tuple

from rdflib import RDF, RDFS, OWL, XSD, URIRef, Literal

from osp.core.ontology import OntologyRelationship
from osp.core.ontology.datatypes import CUSTOM_TO_PYTHON,\
    RDFCompatibleType, RDF_TO_PYTHON, SimpleTriple, SimplePattern, UID
from osp.core.session.session import Session
# from osp.core.session.db.sql_migrate import check_supported_schema_version

from osp.core.utils.general import CUDS_IRI_PREFIX

from osp.core.session.interfaces.triplestore import TriplestoreInterface, \
    TriplestoreStore

# TODO: The SQLInterface is dependent on the TBox, should not be the case.


class SqlQuery:
    """An sql query."""

    def __init__(self, table_name: str, columns, datatypes, alias=None):
        """Initialize the query."""
        alias = alias or table_name
        check_characters(table_name, columns, datatypes, alias)

        self.order = [alias]
        self.tables = {alias: table_name}
        self._columns = {alias: columns}
        self.datatypes = {alias: datatypes}
        self.condition = None

    @property
    def columns(self):
        """Return the columns that are selected."""
        for alias in self.order:
            for column in self._columns[alias]:
                yield (alias, column)

    def where(self, condition):
        """Filter the results."""
        check_characters(condition)
        if condition is None:
            return self
        if self.condition is None:
            self.condition = condition
            return self
        if isinstance(self.condition, AndCondition):
            if isinstance(condition, AndCondition):
                self.condition.conditions |= condition.conditions
            else:
                self.condition.conditions.add(condition)
        else:
            if isinstance(condition, AndCondition):
                condition.conditions.add(self.condition)
                self.condition = condition
            else:
                self.condition = AndCondition(self.condition, condition)
        return self

    def join(self, table_name, columns, datatypes, alias=None):
        """Join with another table."""
        alias = alias or table_name
        check_characters(table_name, columns, datatypes, alias)

        if alias in self.tables:
            raise ValueError(f"{alias} already in query: {self.tables}")
        self.order.append(alias)
        self.tables[alias] = table_name
        self._columns[alias] = columns
        self.datatypes[alias] = datatypes
        return self


class Condition:
    """The general condition class."""


class EqualsCondition(Condition):
    """An SQL Equals condition."""

    def __init__(self, table_name, column, value, datatype):
        """Initialize the condition.

        Args:
            table_name (str): The name of the table.
            column (str): The column object.
            value (Any): The value for that column.
            datatype (str): The datatype of the column.
        """
        self.table_name = table_name
        self.column = column
        self.value = Literal(value, datatype=datatype).toPython()
        self.datatype = datatype

    def __eq__(self, other):
        """Check if two conditions are equal.

        Args:
            other (Condition): The other condition.

        Returns:
            bool: Whether the two conditions are equal.
        """
        return (
            isinstance(other, type(self))
            and self.table_name == other.table_name
            and self.column == other.column
            and self.value == other.value
            and self.datatype == other.datatype
        )

    def __hash__(self):
        """Compute hash."""
        return hash(self.table_name + self.column
                    + str(self.value) + str(self.datatype))


class JoinCondition(Condition):
    """Join two tables with this condition."""

    def __init__(self, table_name1, column1, table_name2, column2):
        """Initialize the condition."""
        self.table_name1 = table_name1
        self.table_name2 = table_name2
        self.column1 = column1
        self.column2 = column2

    def __eq__(self, other):
        """Check if two conditions are equal.

        Args:
            other (Condition): The other condition.

        Returns:
            bool: Whether the two conditions are equivalent.
        """
        return (
            isinstance(other, type(self))
            and self.table_name1 == other.table_name1
            and self.table_name2 == other.table_name2
            and self.column1 == other.column1
            and self.column2 == other.column2
        )

    def __hash__(self):
        """Compute hash."""
        return hash(self.table_name1 + self.table_name2
                    + self.column1 + self.column2)


class AndCondition(Condition):
    """An SQL AND condition."""

    def __init__(self, *conditions):
        """Initialize the condition with several subconditions."""
        conditions = set(c for c in conditions if c is not None)
        if not all(isinstance(c, Condition) for c in conditions):
            raise ValueError(f"Invalid conditions: {conditions}")
        self.conditions = conditions

    def __eq__(self, other):
        """Check if two conditions are equal.

        Args:
            other (Condition): The other condition.

        Returns:
            bool: Whether the two conditions are equivalent.
        """
        return isinstance(other, type(self)) \
            and set(self.conditions) == set(other.conditions)

    def __hash__(self):
        """Compute hash."""
        return hash("".join([str(hash(c)) for c in self.conditions]))


def determine_datatype(table_name: str) -> URIRef:
    """Determine the datatype of column o for the table with given table name.

    Args:
        table_name (str): The name of the data table.

    Returns:
        URIRef: The datatype of the object column.
    """
    prefix = SQLInterface.DATA_TABLE_PREFIX

    if table_name.startswith(prefix + "OWL_"):
        return URIRef(f'http://www.w3.org/2002/07/owl#'
                      f'{table_name[len(prefix + "OWL_"):]}')
        # Replaced OWL with URIRef('...'), as OWL.rational seems
        # to have disappeared in rdflib 6.0.0.
        # TODO: return to original form when a fix for rdflib is available.
    elif table_name.startswith(prefix + "RDFS_"):
        return getattr(RDFS, table_name[len(prefix + "RDFS_"):])
    elif table_name.startswith(prefix + "RDF_"):
        return getattr(RDF, table_name[len(prefix + "RDF_"):])
    elif table_name.startswith(prefix + "XSD_"):
        return getattr(XSD, table_name[len(prefix + "XSD_"):])
    elif table_name.startswith(prefix + "CUSTOM_"):
        return URIRef('http://www.osp-core.com/types#') \
            + table_name[len(prefix + "CUSTOM_"):]
    else:
        raise NotImplementedError(f"Table name {table_name} does not match "
                                  f"any known datatype.")


def get_data_table_name(datatype: URIRef) -> str:
    """Get the name of the table for the given datatype.

    Args:
        datatype: The datatype of the object column.

    Raises:
        NotImplementedError: The given datatype is not supported.

    Returns:
        The name of the table.
    """
    prefix = SQLInterface.DATA_TABLE_PREFIX
    if datatype.startswith(str(XSD)):
        return prefix + "XSD_" + datatype[len(str(XSD)):]
    if datatype.startswith(str(OWL)):
        return prefix + "OWL_" + datatype[len(str(OWL)):]
    if datatype.startswith(str(RDF)):
        return prefix + "RDF_" + datatype[len(str(RDF)):]
    if datatype.startswith(str(RDFS)):
        return prefix + "RDFS_" + datatype[len(str(RDFS)):]
    if datatype.startswith(str(URIRef('http://www.osp-core.com/types#'))):
        return prefix + "CUSTOM_" + \
            datatype[len(str(URIRef('http://www.osp-core.com/types#'))):]
    raise NotImplementedError(f"Unsupported datatype {datatype}")


def check_characters(*to_check):
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
            elif isinstance(s, JoinCondition):
                to_check += [s.table_name1, s.column1,
                             s.table_name2, s.column2]
            elif s is None:
                pass
            else:
                raise ValueError("%s - %s" % (s, str_to_check))


def convert_values(rows, query):
    """Convert the values in the database to the correct datatype.

    Args:
        rows(Iterator[Iterator[Any]]): The rows of the database.
        query(SqlQuery): The corresponding query.

    Yields:
        The rows with converted values.
    """
    for row in rows:
        output = []
        for value, (t_alias, column) in zip(row, query.columns):
            output.append(
                Literal(value,
                        datatype=query.datatypes[t_alias][column])
                .toPython()
            )
        yield output


class SQLStore(TriplestoreStore):
    """The abstraction of the TriplestoreStore is sufficient."""

    _interface: "SQLInterface"

    pass


class SQLInterface(TriplestoreInterface):
    """Abstract class for an SQL DB Wrapper Session."""

    store_class = SQLStore

    NAMESPACES_TABLE = "OSP_V2_NAMESPACES"
    ENTITIES_TABLE = "OSP_V2_ENTITIES"
    CUDS_TABLE = "OSP_V2_CUDS"
    TYPES_TABLE = "OSP_V2_TYPES"
    RELATIONSHIP_TABLE = "OSP_V2_RELATIONS"
    DATA_TABLE_PREFIX = "OSP_DATA_V2_"
    """There is one data table for each data type."""
    TRIPLESTORE_COLUMNS = ["s", "p", "o"]
    COLUMNS = {
        NAMESPACES_TABLE: ["ns_idx", "namespace"],
        ENTITIES_TABLE: ["entity_idx", "ns_idx", "name"],
        CUDS_TABLE: ["cuds_idx", "uid"],
        TYPES_TABLE: ["s", "o"],
        RELATIONSHIP_TABLE: TRIPLESTORE_COLUMNS,
        DATA_TABLE_PREFIX: TRIPLESTORE_COLUMNS
    }
    DATATYPES = {
        NAMESPACES_TABLE: {
            "ns_idx": XSD.integer,
            "namespace": XSD.string,
        },
        ENTITIES_TABLE: {
            "entity_idx": XSD.integer,
            "ns_idx": XSD.integer,
            "name": XSD.string,
        },
        CUDS_TABLE: {
            "cuds_idx": XSD.integer,
            "uid": UID.iri
        },
        TYPES_TABLE: {
            "s": XSD.integer,
            "o": XSD.integer,
        },
        RELATIONSHIP_TABLE: {
            "s": XSD.integer,
            "p": XSD.integer,
            "o": XSD.integer},
        DATA_TABLE_PREFIX: {
            "s": XSD.integer,
            "p": XSD.integer
        },
    }
    PRIMARY_KEY = {
        NAMESPACES_TABLE: ["ns_idx"],
        ENTITIES_TABLE: ["entity_idx"],
        CUDS_TABLE: ["cuds_idx"],
        TYPES_TABLE: ["s", "o"],
        RELATIONSHIP_TABLE: TRIPLESTORE_COLUMNS,
        DATA_TABLE_PREFIX: TRIPLESTORE_COLUMNS,
    }
    GENERATE_PK = {CUDS_TABLE, ENTITIES_TABLE, NAMESPACES_TABLE}
    FOREIGN_KEY = {
        NAMESPACES_TABLE: {},
        ENTITIES_TABLE: {"ns_idx": (NAMESPACES_TABLE, "ns_idx")},
        CUDS_TABLE: {},
        TYPES_TABLE: {
            "s": (CUDS_TABLE, "cuds_idx"),
            "o": (ENTITIES_TABLE, "entity_idx")
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
    }
    INDEXES = {
        CUDS_TABLE: [["uid"]],
        ENTITIES_TABLE: [["ns_idx", "name"]],
        TYPES_TABLE: [["s"], ["o"]],
        NAMESPACES_TABLE: [["namespace"]],
        RELATIONSHIP_TABLE: [["s", "p"], ["p", "o"]],
        DATA_TABLE_PREFIX: [["s", "p"]]
    }

    # check_schema = check_supported_schema_version

    def __init__(self, *args, **kwargs):
        """Initialize the interface.

        The only added functionality with regard to the superclass is
        calling `_initialize` to set up the database tables.
        """
        super().__init__(*args, **kwargs)
        self._initialize()

    # GET TRIPLES

    def triples(self, pattern: SimplePattern) -> Iterator[SimpleTriple]:
        """Generator that yields database triples matching a pattern.

        Args:
            pattern: Triple pattern (without blank nodes).

        Yields:
            Triples (see SimpleTriple description) without blank nodes.
        """
        for q, t, dt in self._queries(pattern):
            c = self._do_db_select(q)
            yield from self._rows_to_triples(cursor=c,
                                             table_name=t,
                                             object_datatype=dt)

    def _triples_for_subject(self,
                             iri: URIRef,
                             tables: Optional[Iterable[str]] = None,
                             exclude: Iterable[str] = tuple()) \
            -> Iterator[SimpleTriple]:
        """Generator that yields database triples for a given subject.

        Args:
            iri: IRI of the subject.
            tables: table names to query.
            exclude: table names to exclude from the queries.

        Yields:
            Triples (see SimpleTriple description) without blank nodes.
        """
        for q, t, dt in self._queries_for_subject(iri, tables, exclude):
            c = self._do_db_select(q)
            yield from self._rows_to_triples(cursor=c,
                                             table_name=t,
                                             object_datatype=dt)

    def _queries(self,
                 pattern: SimplePattern,
                 table_name: Optional[str] = None,
                 object_datatype: Optional[URIRef] = None,
                 mode: str = "select") \
            -> Iterator[Tuple[SqlQuery, str, URIRef]]:
        """Generator that yields SQL query details for a pattern.

        Args:
            pattern: triple pattern to query for.
            table_name: name of the table to query.
            object_datatype: the RDF datatype of the object to be extracted.
            mode: type of query to perform. The supported queries are,
                - "select" a SELECT query,
                - "delete" a DELETE query.

        Yields:
            Tuple of SQL query objects, the table on which such query is to be
            performed and the RDF datatype that the extracted piece of
            information should have.
        """
        func = {"select": self._construct_query,
                "delete": self._construct_remove_condition}
        if table_name is None:
            if pattern[1] is pattern[2] is None:
                yield from self._queries_for_subject(pattern[0], mode=mode)
                return
            table_name, datatypes = self._determine_table(pattern)
            object_datatype = datatypes["o"]
        # Construct query
        yield (func[mode](pattern, table_name, object_datatype),
               table_name,
               object_datatype)

    def _queries_for_subject(self,
                             s: URIRef,
                             tables: Optional[Iterable[str]] = None,
                             exclude: Iterable[str] = tuple(),
                             mode: str = "select") \
            -> Iterator[Tuple[SqlQuery, str, URIRef]]:
        """Get all queries needed to all the information about a subject.

        To fetch all the information about a subject, it is necessary to
        query multiple tables. This functions calls `_queries` to yield all
        such queries.

        Args:
            s: The IRI of the subject to query for.
            tables: Iterable with the table names to query. When not specified,
                all tables are queried.
            exclude: Iterable with table names to exclude from the query.
            mode: type of query to get. The supported queries are,
                - "select" a SELECT query,
                - "delete" a DELETE query.

        Yields:
            Tuple of SQL query objects, the table on which such query is to be
            performed and the RDF datatype that the extracted piece of
            information should have.
        """
        tables = set(tables or [
            self.RELATIONSHIP_TABLE, self.TYPES_TABLE,
            *self._get_table_names(prefix=self.DATA_TABLE_PREFIX)]
        ) - set(exclude)
        for table_name in tables:
            object_datatype = XSD.integer
            if table_name.startswith(self.DATA_TABLE_PREFIX):
                object_datatype = determine_datatype(table_name)
            yield from self._queries(
                pattern=(s, None, None),
                table_name=table_name,
                object_datatype=object_datatype,
                mode=mode
            )

    def _determine_table(self, pattern: SimplePattern) \
            -> Tuple[str, Dict[str, RDFCompatibleType]]:
        """Determine the table to be queried given a triple pattern.

        Args:
            pattern: The triple pattern to be queried.

        Returns:
            Tuple in which the first element is the name of the table to store
            the triple and the second a dict with the RDF datatype for each
            column of the table.
        """
        def data_table(datatype):
            return (get_data_table_name(datatype),
                    dict(**self.DATATYPES[self.DATA_TABLE_PREFIX],
                         o=datatype))
        rel_table = (self.RELATIONSHIP_TABLE,
                     self.DATATYPES[self.RELATIONSHIP_TABLE])
        types_table = (self.TYPES_TABLE, self.DATATYPES[self.TYPES_TABLE])
        s, p, o = pattern

        # object given
        if isinstance(o, URIRef) and self._is_cuds_iri(o):
            return rel_table
        if isinstance(o, URIRef):
            return types_table
        if isinstance(o, Literal) and o.datatype:
            return data_table(o.datatype)
        # predicate given
        if p == RDF.type:
            return types_table
        if p is not None:
            from osp.core.namespaces import from_iri
            predicate = from_iri(p)
            if isinstance(predicate, OntologyRelationship):
                return rel_table
            return data_table(predicate.datatype or XSD.string)

    def _construct_query(self,
                         pattern: SimplePattern,
                         table_name: str,
                         object_datatype: RDFCompatibleType):
        """Construct a query from a triple pattern."""
        q = SqlQuery(
            self.CUDS_TABLE, columns=self.COLUMNS[self.CUDS_TABLE][1:],
            datatypes=self.DATATYPES[self.CUDS_TABLE], alias="ts"
        ).where(JoinCondition(table_name, "s", "ts", "cuds_idx"))

        if table_name != self.TYPES_TABLE:
            q = q.join(
                self.ENTITIES_TABLE,
                columns=self.COLUMNS[self.ENTITIES_TABLE][1:],
                datatypes=self.DATATYPES[self.ENTITIES_TABLE], alias="tp"
            ).where(JoinCondition(table_name, "p", "tp", "entity_idx"))
        else:
            q = q.join(
                self.ENTITIES_TABLE,
                columns=self.COLUMNS[self.ENTITIES_TABLE][1:],
                datatypes=self.DATATYPES[self.ENTITIES_TABLE], alias="to"
            ).where(JoinCondition(table_name, "o", "to", "entity_idx"))

        if table_name == self.RELATIONSHIP_TABLE:
            q = q.join(
                self.CUDS_TABLE, columns=self.COLUMNS[self.CUDS_TABLE][1:],
                datatypes=self.DATATYPES[self.CUDS_TABLE], alias="to"
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
            uid = UID(s)
            conditions += [EqualsCondition("ts", "uid", uid,
                                           UID.iri)]

        if p is not None and table_name != self.TYPES_TABLE:
            ns_idx, name = self._split_namespace(p)
            conditions += [
                EqualsCondition("tp", "ns_idx", ns_idx, XSD.integer),
                EqualsCondition("tp", "name", name, XSD.string)
            ]

        if o is not None and table_name == self.RELATIONSHIP_TABLE:
            uid = self._split_namespace(o)
            conditions += [EqualsCondition("to", "uid", uid, UID.iri)]

        elif o is not None and table_name == self.TYPES_TABLE:
            ns_idx, name = self._split_namespace(o)
            conditions += [
                EqualsCondition("to", "ns_idx", ns_idx, XSD.integer),
                EqualsCondition("to", "name", name, XSD.string)
            ]

        elif o is not None:
            conditions += [
                EqualsCondition(table_name, "o",
                                o.toPython(), object_datatype)]

        return AndCondition(*conditions)

    def _split_namespace(self, iri):
        # TODO: This can be improved.
        if iri.startswith(CUDS_IRI_PREFIX):
            return UID(iri)
        elif self._is_cuds_iri(iri):
            return UID(iri)
        ns_iri = next((x.iri for x in Session.ontology.namespaces if iri in x),
                      None)
        return self._get_ns_idx(ns_iri), str(iri[len(ns_iri):])

    def _is_cuds_iri(self, iri):
        return UID(iri) == UID(0) or iri.startswith(CUDS_IRI_PREFIX) or \
            self._is_cuds_iri_ontology(iri)

    @staticmethod
    def _is_cuds_iri_ontology(iri):
        def blacklisted(_iri):
            return _iri in frozenset(
                {OWL.DatatypeProperty, OWL.ObjectProperty, OWL.Class,
                 OWL.Restriction,
                 URIRef("http://www.osp-core.com/cuba#attribute"),
                 URIRef("http://www.osp-core.com/cuba#relationship"),
                 }) \
                or str(OWL) in _iri or str(RDF) in _iri or str(RDFS) in _iri

        for s, p, o in Session.ontology.ontology_graph\
                .triples((URIRef(iri), RDF.type, None)):
            if blacklisted(o):
                return False
        return not blacklisted(iri)

    def _get_ns_idx(self, ns_iri):
        ns_iri = str(ns_iri)
        if ns_iri not in self._ns_to_idx:
            self._do_db_insert(
                table_name=self.NAMESPACES_TABLE,
                columns=["namespace"],
                values=[str(ns_iri)],
                datatypes=self.DATATYPES[self.NAMESPACES_TABLE]
            )
            self._load_namespace_indexes()
        return self._ns_to_idx[ns_iri]

    def _get_ns(self, ns_idx):
        if ns_idx not in self._idx_to_ns:
            self._load_namespace_indexes()
        return self._idx_to_ns[ns_idx]

    def _rows_to_triples(self, cursor, table_name, object_datatype):
        for row in cursor:
            s = URIRef(UID(row[0]).to_iri())
            x = URIRef(self._get_ns(row[1]) + row[2])
            if table_name == self.TYPES_TABLE:
                yield s, RDF.type, x
            elif table_name == self.RELATIONSHIP_TABLE:
                o = URIRef(UID(row[3]).to_iri())
                yield s, x, o
            else:
                yield s, x, Literal(row[3], datatype=object_datatype)

    # LOAD

    def _load_triples_for_iri(self, iri):
        triples = set(
            self._triples_for_subject(iri, tables=(self.RELATIONSHIP_TABLE,))
        )
        type_triples_of_neighbors = set()
        for s, p, o in triples:
            type_triples_of_neighbors |= set(
                self.triples((o, RDF.type, None))
            )

        triples |= set(
            self._triples_for_subject(iri, exclude=(self.RELATIONSHIP_TABLE,))
        )
        return triples, type_triples_of_neighbors

    # ADD

    def add(self, *triples):
        """Add the provided triples to the store."""
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
                datatypes=datatypes
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
            self.CUDS_TABLE, condition=EqualsCondition(
                self.CUDS_TABLE, "uid", uid, datatype=UID.iri
            )
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
            self.ENTITIES_TABLE, condition=AndCondition(
                EqualsCondition(self.ENTITIES_TABLE, "ns_idx", ns_idx,
                                datatype=XSD.integer),
                EqualsCondition(self.ENTITIES_TABLE, "name", name,
                                datatype=XSD.string)
            )
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

    def remove(self, pattern):
        """Remove triples matching the provided pattern from the store."""
        for c, t, _ in self._queries(pattern, mode="delete"):
            self._do_db_delete(t, c)

    def _construct_remove_condition(self, pattern, table, object_datatype):
        conditions = list()
        s, p, o = pattern
        if s is not None:
            s = self._get_cuds_idx(self._split_namespace(s))
            conditions += [EqualsCondition(table, column="s", value=s,
                                           datatype=XSD.integer)]
        if table == self.TYPES_TABLE:
            if o is not None:
                o = self._get_entity_idx(*self._split_namespace(o))
                conditions += [EqualsCondition(table, column="o", value=o,
                                               datatype=XSD.integer)]
            return AndCondition(*conditions)

        if p is not None:
            p = self._get_entity_idx(*self._split_namespace(p))
            conditions += [EqualsCondition(table, column="p", value=p,
                                           datatype=XSD.integer)]

        if o is not None:
            o = o.toPython()
            if table == self.RELATIONSHIP_TABLE:
                o = self._get_cuds_idx(self._split_namespace(o))
            conditions += [EqualsCondition(table, column="o", value=o,
                                           datatype=object_datatype)]
        return AndCondition(*conditions)

    def _load_namespace_indexes(self):
        self._idx_to_ns = dict(self._default_select(self.NAMESPACES_TABLE))
        self._ns_to_idx = {v: k for k, v in self._idx_to_ns.items()}

    # OTHER

    def _do_db_create(self, table_name, columns, datatypes,
                      primary_key, generate_pk, foreign_key, indexes):
        """Call db_create but expand the vectors first."""
        check_characters(table_name, columns, datatypes,
                         primary_key, foreign_key, indexes)
        self._db_create(table_name, columns, datatypes,
                        primary_key, generate_pk, foreign_key, indexes)

    def _do_db_drop(self, table_name):
        """Call _db_drop but check the characters first."""
        check_characters(table_name)
        self._db_drop(table_name,)

    def _do_db_select(self, query):
        """Call db_select vectors."""
        yield from self._db_select(query)

    def _do_db_insert(self, table_name, columns, values, datatypes):
        """Call db_insert."""
        values = [self._convert_to_datatype(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        check_characters(table_name, columns, datatypes)
        return self._db_insert(table_name, columns, values, datatypes)

    @staticmethod
    def _convert_to_datatype(value: Any, datatype: URIRef) -> Any:
        # TODO: Very similar to
        #  `osp.core.ontology.attribute.OntologyAttribute.convert_to_datatype`.
        #  Unify somehow.
        if isinstance(value, Literal):
            result = Literal(value.toPython(), datatype=datatype,
                             lang=value.language).toPython()
            if isinstance(result, Literal):
                result = RDF_TO_PYTHON[datatype or XSD.string](value.value)
        else:
            result = RDF_TO_PYTHON[datatype or XSD.string](value)
        return result

    def _do_db_update(self, table_name, columns,
                      values, condition, datatypes):
        """Call db_update but expand vectors."""
        values = [self._convert_to_datatype(v, datatypes.get(c))
                  for c, v in zip(columns, values)]
        check_characters(table_name, columns,
                         condition, datatypes)
        self._db_update(table_name, columns,
                        values, condition, datatypes)

    def _do_db_delete(self, table_name, condition):
        """Call _db_delete but expand vectors."""
        check_characters(table_name, condition)
        self._db_delete(table_name, condition)

    def _default_create(self, table_name):
        self._do_db_create(
            table_name=table_name,
            columns=self.COLUMNS[table_name],
            datatypes=self.DATATYPES[table_name],
            primary_key=self.PRIMARY_KEY[table_name],
            generate_pk=table_name in self.GENERATE_PK,
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

    def _clear_database(self):
        """Delete the contents of every table."""
        self.init_transaction()
        try:

            # delete the data
            for table_name in self._get_table_names(
                    SQLInterface.DATA_TABLE_PREFIX):
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

    # INITIALIZE
    def _initialize(self):
        # self.check_schema()
        self._default_create(self.NAMESPACES_TABLE)
        self._default_create(self.CUDS_TABLE)
        self._default_create(self.ENTITIES_TABLE)
        self._default_create(self.TYPES_TABLE)
        self._default_create(self.RELATIONSHIP_TABLE)
        self._load_namespace_indexes()

        datatypes = set(CUSTOM_TO_PYTHON.keys()) | {
            XSD.integer, XSD.boolean, XSD.float,
            XSD.string
        }
        for datatype in datatypes:
            self._do_db_create(
                table_name=get_data_table_name(
                    datatype),
                columns=self.TRIPLESTORE_COLUMNS,
                datatypes={"o": datatype,
                           **self.DATATYPES[self.DATA_TABLE_PREFIX]},
                primary_key=self.PRIMARY_KEY[self.DATA_TABLE_PREFIX],
                generate_pk=self.DATA_TABLE_PREFIX in self.GENERATE_PK,
                foreign_key=self.FOREIGN_KEY[self.DATA_TABLE_PREFIX],
                indexes=self.INDEXES[self.DATA_TABLE_PREFIX]
            )

    # ABSTRACT METHODS

    @abstractmethod
    def _db_create(self,
                   table_name: str,
                   columns: List[str],
                   datatypes: dict,
                   primary_key: List[str],
                   generate_pk: bool,
                   foreign_key: Dict[str, Tuple[str, str]],
                   indexes: List[str]):
        """Create a new table with the given name and columns.

        Args:
            table_name: The name of the new table.
            columns: The name of the columns.
            datatypes: Maps columns to datatypes specified in ontology.
            primary_key: List of columns that belong to the
                primary key.
            foreign_key: mapping from column (dict key) to other tables
                (dict value[0]) column (dict value[1]).
            generate_pk: Whether primary key should be automatically
                generated by the database
                (e.g. be an automatically incrementing integer).
            indexes: List of indexes. Each index is a list of
                column names for which an index should be built.
        """

    @abstractmethod
    def _db_select(self, query: SqlQuery):
        """Get data from the table of the given names.

        Args:
            query: A object describing the SQL query.
        """

    @abstractmethod
    def _db_insert(self,
                   table_name: str,
                   columns: List[str],
                   values: List[Any],
                   datatypes: dict):
        """Insert data into the table with the given name.

        Args:
            table_name: The table name.
            columns: The names of the columns.
            values: The data to insert.
            datatypes: Maps column names to datatypes.

        Returns:
            The auto-generated primary key of the inserted row, if such exists.
        """

    @abstractmethod
    def _db_update(self,
                   table_name: str,
                   columns: List[str],
                   values: List[Any],
                   condition: str,
                   datatypes: dict):
        """Update the data in the given table.

        Args:
            table_name: The name of the table.
            columns: The names of the columns.
            values: The new updated values.
            condition: Only update rows that satisfy the condition.
            datatypes: Maps column names to datatypes.
        """

    @abstractmethod
    def _db_delete(self, table_name: str, condition: Condition):
        """Drop the entire table.

        Args:
            table_name: The name of the table.
            condition: The condition specifying the values to delete.
        """
        pass

    @abstractmethod
    def _db_drop(self, table_name: str):
        """Drop the table with the given name.

        Args:
            table_name: The name of the table.
        """
        pass

    @abstractmethod
    def _get_table_names(self, prefix: str):
        """Get all tables in the database with the given prefix.

        Args:
            prefix: Only return tables with the given prefix
        """
        pass

    @abstractmethod
    def commit(self):
        """Commit buffered changes."""
        pass

    @abstractmethod
    def init_transaction(self):
        """Initialize the transaction (SQL Specific)."""
        pass

    @abstractmethod
    def rollback_transaction(self):
        """Cancel the transaction (SQL Specific)."""
        pass
