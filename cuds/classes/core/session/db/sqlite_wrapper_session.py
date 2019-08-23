# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlite3
from uuid import UUID
from cuds.classes.core.session.db.conditions import EqualsCondition
from cuds.classes.core.session.db.db_wrapper_session import DbWrapperSession


class SqliteWrapperSession(DbWrapperSession):

    def __init__(self, path):
        super().__init__(engine=sqlite3.connect(path))

    def __str__(self):
        return "Sqlite Wrapper Session"

    # OVERRIDE
    def close(self):
        self._engine.close()

    # OVERRIDE
    def _commit(self):
        self._engine.commit()

    # OVERRIDE
    def _db_select(self, table_name, columns, condition, datatypes):
        c = self._engine.cursor()
        condition_str = self._get_condition_string(condition)
        c.execute("SELECT %s FROM %s WHERE %s;" % (
            ", ".join(columns),
            table_name,
            condition_str
        ))
        uuid_columns = [i for i, c in enumerate(columns)
                        if c in datatypes and datatypes[c] == "UUID"]
        return map(lambda v: self._convert_uuid_values(v, uuid_columns, "hex"),
                   c)

    # OVERRIDE
    def _db_create(self, table_name, columns, datatypes):
        columns = [c if c not in datatypes
                   else "%s %s" % (c, self._to_sqlite_datatype(datatypes[c]))
                   for c in columns]
        c = self._engine.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS %s (%s);" % (
            table_name,
            ", ".join(columns)
        ))

    def _to_sqlite_datatype(self, cuds_datatype):
        """Convert the given Cuds datatype to a datatype of sqlite.

        :param cuds_datatype: The given cuds datatype.
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

    # OVERRIDE
    def _get_table_names(self):
        c = self._engine.cursor()
        tables = c.execute("SELECT name FROM sqlite_master "
                           + "WHERE type='table';")
        return set([x[0] for x in tables])

    def _get_condition_string(self, condition):
        if isinstance(condition, EqualsCondition):
            if isinstance(condition.value, (str, UUID)):
                return "%s='%s'" % (condition.column_name,
                                    condition.value)
            else:
                return "%s=%s" % (condition.column_name,
                                  condition.value)
        raise NotImplementedError("Unsupported condition")
