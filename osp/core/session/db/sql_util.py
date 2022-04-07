"""Object to create backend independent queries, conditions and more."""

from copy import deepcopy
from functools import reduce
from operator import mul

import rdflib

from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.datatypes import (
    _parse_vector_args,
    convert_from,
    convert_to,
)

VEC_PREFIX = str(rdflib_cuba["_datatypes/VECTOR-"])


class SqlQuery:
    """An sql query."""

    def __init__(self, table_name, columns, datatypes, alias=None):
        """Initialize the query."""
        alias = alias or table_name
        columns, datatypes = expand_vector_cols(columns, datatypes)
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
        condition = expand_vector_condition(deepcopy(condition))
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
        columns, datatypes = expand_vector_cols(columns, datatypes)
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
        self.value = convert_from(value, datatype)
        self.datatype = datatype

    def __eq__(self, other):
        """Check if two conditions are equal.

        Args:
            other (Condition): The other condition.

        Returns:
            bool: Wether the two codnitions are equal.
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
        return hash(
            self.table_name
            + self.column
            + str(self.value)
            + str(self.datatype)
        )


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
            bool: Wether the two codnitions are equivalent.
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
        return hash(
            self.table_name1 + self.table_name2 + self.column1 + self.column2
        )


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
            bool: Wether the two codnitions are equivalent.
        """
        return isinstance(other, type(self)) and set(self.conditions) == set(
            other.conditions
        )

    def __hash__(self):
        """Compute hash."""
        return hash("".join([str(hash(c)) for c in self.conditions]))


def determine_datatype(table_name):
    """Determine the datatype of column o for the table with given table name.

    Args:
        table_name (str): The name of the data table.

    Returns:
        rdflib.URIRef: The datatype of the object column.
    """
    from osp.core.session.db.sql_wrapper_session import SqlWrapperSession

    prefix = SqlWrapperSession.DATA_TABLE_PREFIX

    if table_name.startswith(prefix + "OWL_"):
        return rdflib.URIRef(
            f"http://www.w3.org/2002/07/owl#"
            f'{table_name[len(prefix + "OWL_"):]}'
        )
        # Replaced rdflib.OWL with URIRef('...'), as rdflib.OWL.rational seems
        # to have disappeared in rdflib 6.0.0.
        # TODO: return to original form when a fix for rdflib is available.
    elif table_name.startswith(prefix + "RDFS_"):
        return getattr(rdflib.RDFS, table_name[len(prefix + "RDFS_") :])
    elif table_name.startswith(prefix + "RDF_"):
        return getattr(rdflib.RDF, table_name[len(prefix + "RDF_") :])
    elif table_name.startswith(prefix + "XSD_"):
        return getattr(rdflib.XSD, table_name[len(prefix + "XSD_") :])
    else:
        return getattr(rdflib_cuba, "_datatypes/" + table_name[len(prefix) :])


def get_data_table_name(datatype):
    """Get the name of the table for the given datatype.

    Args:
        datatype (rdflib.URIRef): The datatype of the object column.

    Raises:
        NotImplementedError: The given datatype is not supported.

    Returns:
        str: The name of the table.
    """
    from osp.core.session.db.sql_wrapper_session import SqlWrapperSession

    prefix = SqlWrapperSession.DATA_TABLE_PREFIX
    if datatype.startswith(str(rdflib.XSD)):
        return prefix + "XSD_" + datatype[len(str(rdflib.XSD)) :]
    if datatype.startswith(str(rdflib.OWL)):
        return prefix + "OWL_" + datatype[len(str(rdflib.OWL)) :]
    if datatype.startswith(str(rdflib.RDF)):
        return prefix + "RDF_" + datatype[len(str(rdflib.RDF)) :]
    if datatype.startswith(str(rdflib.RDFS)):
        return prefix + "RDFS_" + datatype[len(str(rdflib.RDFS)) :]
    if datatype.startswith(str(rdflib_cuba) + "_datatypes/"):
        return prefix + datatype[len(str(rdflib_cuba) + "_datatypes/") :]
    raise NotImplementedError(f"Unsupported datatype {datatype}")


def check_characters(*to_check):
    """Check if column or table names contain invalid characters.

    Args:
        *to_check: The names to check.

    Raises:
        ValueError: Invalid character detected.

    """
    forbidden_chars = [
        ";",
        "\0",
        "\r",
        "\x08",
        "\x09",
        "\x1a",
        "\n",
        "\r",
        '"',
        "'",
        "`",
        "\\",
        "%",
    ]
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
                to_check += [
                    s.table_name1,
                    s.column1,
                    s.table_name2,
                    s.column2,
                ]
            elif s is None:
                pass
            else:
                raise ValueError("%s - %s" % (s, str_to_check))


def expand_vector_cols(columns, datatypes, values=None):
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
    datatypes_expanded = dict(datatypes)
    values_expanded = list()

    # iterate over the columns and look for vectors
    for i, column in enumerate(columns):
        # non vectors are simply added to the result
        if datatypes[column] is None or not datatypes[column].startswith(
            VEC_PREFIX
        ):
            columns_expanded.append(column)
            datatypes_expanded[column] = datatypes[column]
            if values:
                values_expanded.append(values[i])
            continue

        # create a column for each element in the vector
        expanded_cols, datatype = get_expanded_cols(column, datatypes[column])
        columns_expanded.extend(expanded_cols)
        datatypes_expanded.update({c: datatype for c in expanded_cols})
        datatypes_expanded[column] = datatypes[column]
        if values:
            values_expanded.extend(convert_from(values[i], datatypes[column]))
    if values:
        return columns_expanded, datatypes_expanded, values_expanded
    return columns_expanded, datatypes_expanded


def contract_vector_values(rows, query):
    """Contract vector values in a row of a database into one vector.

    Args:
        rows(Iterator[List[Any]]): The rows fetched from the database
        query(SqlQuery): The corresponding query-

    Returns:
        Iterator[List[Any]]: The rows with vectors being a single item
            in each row.
    """
    rows = convert_values(rows, query)
    for row in rows:
        contracted_row = list()
        temp_vec = list()  # collect the elements of the vectors here
        vector_datatype = None

        # iterate over the columns and look for vector columns
        for (t_alias, column), value in zip(query.columns, row):

            vector_datatype, is_vec_elem = handle_vector_item(
                column,
                value,
                query.datatypes[t_alias],
                temp_vec,
                vector_datatype,
            )
            if is_vec_elem:
                continue

            if temp_vec:  # add the vector to the result
                contracted_row.append(convert_to(temp_vec, vector_datatype))
                temp_vec = list()

            vector_datatype, is_vec_elem = handle_vector_item(
                column,
                value,
                query.datatypes[t_alias],
                temp_vec,
                vector_datatype,
            )
            if is_vec_elem:
                continue

            # non vectors are simply added to the result
            contracted_row.append(value)

        if temp_vec:  # add the vector to the result
            contracted_row.append(convert_to(temp_vec, vector_datatype))
            temp_vec = list()
        yield contracted_row


def expand_vector_condition(condition):
    """Expand a condition on a vector to condition on multiple columns.

    Args:
        condition (Condition): A osp-core condition.

    Returns:
        Condition: The expanded OSP-core condition.
    """
    if isinstance(
        condition, EqualsCondition
    ) and condition.datatype.startswith(VEC_PREFIX):

        expanded_cols, datatype = get_expanded_cols(
            condition.column, condition.datatype
        )
        return AndCondition(
            *[
                EqualsCondition(
                    table_name=condition.table_name,
                    column=c,
                    value=v,
                    datatype=datatype,
                )
                for c, v in zip(expanded_cols, condition.value)
            ]
        )

    elif isinstance(condition, AndCondition):
        return AndCondition(
            *[expand_vector_condition(c) for c in condition.conditions]
        )
    return condition


def get_expanded_cols(column, datatype):
    """Get the expanded columns for the given column.

    Args:
        column (str): The column name to expand.
        datatype (rdflib.URIRef): The datatype of the column.
            Expand if it is a vector.

    Returns:
        Tuple[List[str], rdflib.URIRef]: ist of resulting columns and their
            datatype,
    """
    if not datatype.startswith(VEC_PREFIX):
        return [column], datatype
    vector_args = datatype[len(VEC_PREFIX) :].split("-")
    datatype, shape = _parse_vector_args(vector_args)
    size = reduce(mul, map(int, shape))
    expanded_cols = ["%s___%s" % (column, x) for x in range(size)]
    return expanded_cols, datatype


def handle_vector_item(
    column, value, datatypes, temp_vec, old_vector_datatype
):
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
        orig_col = column[: -len(vec_suffix)]
        return datatypes[orig_col], True
    return old_vector_datatype, False


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
            output.append(convert_to(value, query.datatypes[t_alias][column]))
        yield output
