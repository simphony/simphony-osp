# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlite3
from cuds.classes.core.session.db.conditions import (EqualsCondition,
                                                     AndCondition)
from cuds.classes.core.session.db.sql_wrapper_session import SqlWrapperSession


class SqliteWrapperSession(SqlWrapperSession):

    def __init__(self, path, **kwargs):
        super().__init__(engine=sqlite3.connect(path), **kwargs)

    def __str__(self):
        return "Sqlite Wrapper Session"

    # OVERRIDE
    def close(self):
        self._engine.close()

    # OVERRIDE
    def _commit(self):
        self._engine.commit()

    # OVERRIDE
    def _init_transaction(self):
        pass  # TODO

    # OVERRIDE
    def _rollback_transaction(self):
        pass  # TODO

    # OVERRIDE
    def _db_select(self, table_name, columns, condition, datatypes):
        c = self._engine.cursor()
        condition_str = self._get_condition_string(condition)
        c.execute("SELECT %s FROM %s WHERE %s;" % (
            ", ".join(columns),
            table_name,
            condition_str
        ))
        return self._convert_values(c, columns, datatypes)

    # OVERRIDE
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, foreign_key, index):
        # TODO Primary key, foreign key, index
        columns = [c if c not in datatypes
                   else "%s %s" % (c, self._to_sqlite_datatype(datatypes[c]))
                   for c in columns]
        c = self._engine.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS %s (%s);" % (
            table_name,
            ", ".join(columns)
        ))

    # OVERRIDE
    def _db_insert(self, table_name, columns, values, datatypes):
        c = self._engine.cursor()
        c.execute("INSERT INTO %s (%s) VALUES (%s);" % (
            table_name,
            ", ".join(columns),
            ", ".join([self._to_sqlite_value(v, datatypes.get(c))
                       for c, v in zip(columns, values)])
        ))

    # OVERRIDE
    def _db_update(self, table_name, columns, values, condition, datatypes):
        c = self._engine.cursor()
        condition_str = self._get_condition_string(condition)
        c.execute("UPDATE %s SET %s WHERE %s;" % (
            table_name,
            ", ".join(("%s = %s" %
                      (c, self._to_sqlite_value(v, datatypes.get(c))))
                      for c, v in zip(columns, values)),
            condition_str
        ))

    # OVERRIDE
    def _db_delete(self, table_name, condition):
        c = self._engine.cursor()
        condition_str = self._get_condition_string(condition)
        c.execute("DELETE FROM %s WHERE %s;" % (table_name, condition_str))

    def _get_condition_string(self, condition):
        """Convert the given condition to a Sqlite condition string.

        :param condition: The Condition
        :type condition: Uniton[AndCondition, EqualsCondition]
        :raises NotImplementedError: Unknown condition type
        :return: The resulting condition
        :rtype: str
        """
        if condition is None:
            return '1'
        if isinstance(condition, EqualsCondition):
            value = self._to_sqlite_value(condition.value, condition.datatype)
            return "%s.%s=%s" % (condition.table_name,
                                 condition.column_name,
                                 value)
        if isinstance(condition, AndCondition):
            return " AND ".join([self._get_condition_string(c)
                                 for c in condition.conditions])
        raise NotImplementedError("Unsupported condition")

    def _to_sqlite_datatype(self, cuds_datatype):
        """Convert the given Cuds datatype to a datatype of sqlite.

        :param cuds_datatype: The given cuds_object datatype.
        :type cuds_datatype: str
        :raises NotImplementedError: Unsupported datatype given.
        :return: A sqlite datatype.
        :rtype: str
        """
        if cuds_datatype == "UUID":
            return "TEXT"
        if cuds_datatype == "INT":
            return "INTEGER"
        if cuds_datatype == "BOOL":
            return "BOOLEAN"
        if cuds_datatype == "FLOAT":
            return "REAL"
        elif cuds_datatype.startswith("STRING"):
            return "TEXT"
        else:
            raise NotImplementedError("Unsupported data type!")

    def _to_sqlite_value(self, value, cuds_datatype):
        """Convert the given value s.t. it can be used in a sqlite query.

        :param value: The value to convert.
        :type value: Any
        :param cuds_datatype: The datatype to convert to.
        :type cuds_datatype: str
        :raises NotImplementedError: Unsupported datatype.
        :return: The converted value.
        :rtype: str
        """
        if cuds_datatype is None or \
                cuds_datatype == "UUID" or cuds_datatype.startswith("STRING"):
            return "'%s'" % value
        if cuds_datatype in ["INT", "BOOL"]:
            return str(int(value))
        if cuds_datatype == "FLOAT":
            return str(float(value))
        else:
            raise NotImplementedError("Unsupported data type!")
