"""Object to create backend independent queries, conditions and more."""

from rdflib import OWL, RDF, RDFS, XSD, URIRef, Literal


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
    from osp.core.session.db.sql_wrapper_session import SqlWrapperSession
    prefix = SqlWrapperSession.DATA_TABLE_PREFIX

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
    from osp.core.session.db.sql_wrapper_session import SqlWrapperSession
    prefix = SqlWrapperSession.DATA_TABLE_PREFIX
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
