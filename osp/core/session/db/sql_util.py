"""Object to create backend independent filters for SQL queries."""

from operator import mul
from osp.core.ontology.datatypes import convert_to, convert_from, \
    _parse_vector_args
from osp.core.ontology.cuba import rdflib_cuba
from functools import reduce


class SqlQuery():
    """An sql query."""

    def __init__(self, table_name, columns, datatypes, alias=None):
        """Initialize the query."""
        alias = (alias or table_name).lower()
        columns, datatypes = expand_vector_cols(columns, datatypes)
        check_characters(table_name, columns, datatypes, alias)

        self.order = [alias]
        self.tables = {alias: table_name}
        self._columns = {alias: columns}
        self.datatypes = {alias: datatypes}
        self.condition = None

    @property
    def columns(self):
        for alias in self.order:
            for column in self._columns[alias]:
                yield (alias, column)

    def where(self, condition):
        """Filter the results."""
        condition = expand_vector_condition(condition)
        check_characters(condition)
        if condition is None:
            return self
        if self.condition is None:
            self.condition = condition
            return self
        if isinstance(self.condition, AndCondition):
            if isinstance(condition, AndCondition):
                self.condition.conditions += condition.conditions
            else:
                self.condition.conditions.append(condition)
        else:
            if isinstance(condition, AndCondition):
                condition.conditions.append(self.condition)
                self.condition.conditions = condition
            else:
                self.condition = AndCondition(self.condition, condition)
        return self

    def join(self, table_name, columns, datatypes, alias=None):
        """Join with another table."""
        alias = (alias or table_name).lower()
        columns, datatypes = expand_vector_cols(columns, datatypes)
        check_characters(table_name, columns, datatypes, alias)

        if alias in self.tables:
            raise ValueError(f"{alias} already in query: {self.tables}")
        self.order.append(alias)
        self.tables[alias] = table_name
        self._columns[alias] = columns
        self.datatypes[alias] = datatypes
        return self


class Condition():
    pass


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
        self.table_name = None
        self.column = column
        self.value = convert_from(value, datatype)
        self.datatype = datatype


class JoinCondition(Condition):
    """Join two tables with this condition."""

    def __init__(self, table_name1, column1, table_name2, column2):
        """Initialize the condition."""
        self.table_name1 = table_name1
        self.table_name2 = table_name2
        self.column1 = column1
        self.column2 = column2


class AndCondition(Condition):
    """An SQL AND consition."""

    def __init__(self, *conditions):
        """Initialize the condition with several subconditions."""
        conditions = [c for c in conditions if c is not None]
        if not all(isinstance(c, Condition) for c in conditions):
            raise ValueError(f"Invalid conditions: {conditions}")
        self.conditions = conditions


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


def contract_vector_values(rows, query):
    """Contract vector values in a row of a database into one vector.

    Args:
        columns(List[str]): The expanded columns of the database
        datatypes(dict): The datatype for each column
        rows(Iterator[List[Any]]): The rows fetched from the database

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
                column, value, query.datatypes[t_alias],
                temp_vec, vector_datatype
            )
            if is_vec_elem:
                continue

            if temp_vec:  # add the vector to the result
                contracted_row.append(convert_to(temp_vec, vector_datatype))
                temp_vec = list()

            vector_datatype, is_vec_elem = handle_vector_item(
                column, value, query.datatypes[t_alias],
                temp_vec, vector_datatype
            )
            if is_vec_elem:
                continue

            # non vectors are simply added to the result
            contracted_row.append(value)

        if temp_vec:  # add the vector to the result
            contracted_row.append(convert_to(temp_vec,
                                             vector_datatype))
            temp_vec = list()
        yield contracted_row


def expand_vector_condition(condition):
    return condition  # TODO


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


def convert_values(rows, query):
    """Convert the values in the database to the correct datatype.

    Args:
        rows(Iterator[Iterator[Any]]): The rows of the database
        columns(List[str]): The corresponding columns
        datatypes(Dict[str, str]): Mapping from column to datatype

    """
    for row in rows:
        output = []
        for value, (t_alias, column) in zip(row, query.columns):
            output.append(
                convert_to(value, query.datatypes[t_alias][column])
            )
        yield output