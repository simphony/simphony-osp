from osp.core.ontology.datatypes import convert_from


class EqualsCondition():
    def __init__(self, table_name, column, value, datatype):
        self.table_name = table_name
        self.column = column
        self.value = convert_from(value, datatype)
        self.datatype = datatype


class AndCondition():
    def __init__(self, *conditions):
        self.conditions = conditions
