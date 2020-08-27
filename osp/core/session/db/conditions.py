"""Object to create backend independent filters for SQL queries."""

from osp.core.ontology.datatypes import convert_from


class EqualsCondition():
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


class AndCondition():
    """An SQL AND consition."""

    def __init__(self, *conditions):
        """Initialize the condition with several subconditions."""
        self.conditions = conditions
