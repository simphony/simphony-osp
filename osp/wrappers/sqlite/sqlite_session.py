# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlite3
from osp.core.session.db.conditions import (EqualsCondition,
                                            AndCondition)
from osp.core.session.db.sql_wrapper_session import SqlWrapperSession


class SqliteSession(SqlWrapperSession):

    def __init__(self, path, check_same_thread=True, **kwargs):
        conn = sqlite3.connect(path,
                               isolation_level=None,
                               check_same_thread=check_same_thread)
        super().__init__(engine=conn, **kwargs)

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
        c = self._engine.cursor()
        c.execute("BEGIN;")

    # OVERRIDE
    def _rollback_transaction(self):
        c = self._engine.cursor()
        c.execute("ROLLBACK;")

    @staticmethod
    def _sql_list_pattern(prefix, values, join_pattern=True):
        """Transform a list of values to corresponding pattern and value dict

        :param prefix: The prefix to use for the pattern
        :type prefix: str
        :param values: The list of values
        :type values: List[Any]
        :param join_pattern: Whether to join the pattern by a comma,
            defaults to True
        :type join_pattern: bool, optional
        :return: The pattern and the value dict
        :rtype: Tuple[str, Dict]
        """
        pattern = [":%s_%s" % (prefix, i) for i in range(len(values))]
        if join_pattern:
            pattern = ", ".join(pattern)
        values = {
            ("%s_%s" % (prefix, i)): val for i, val in enumerate(values)
        }
        return pattern, values

    # OVERRIDE
    def _db_select(self, table_name, columns, condition, datatypes):
        cond_pattern, cond_values = self._get_condition_pattern(condition)
        sql_pattern = "SELECT %s FROM %s WHERE %s;" % (
            ", ".join(columns), table_name, cond_pattern
        )
        c = self._engine.cursor()
        c.execute(sql_pattern, cond_values)
        return c

    # OVERRIDE
    def _db_create(self, table_name, columns, datatypes,
                   primary_key, foreign_key, indexes):
        columns = [
            c if c not in datatypes
            else "'%s' '%s'" % (c, self._to_sqlite_datatype(datatypes[c]))
            for c in columns
        ]
        constraints = [
            "PRIMARY KEY(%s)" % ", ".join(
                map(lambda x: "'%s'" % x, primary_key)
            )
        ]
        constraints += [
            "FOREIGN KEY('%s') REFERENCES '%s'('%s')" % (col, ref[0], ref[1])
            for col, ref in foreign_key.items()
        ]
        c = self._engine.cursor()
        sql = "CREATE TABLE IF NOT EXISTS '%s' (%s);" % (
            table_name,
            ", ".join(columns + constraints)
        )
        c.execute(sql)
        for index in indexes:
            sql = "CREATE INDEX IF NOT EXISTS 'idx_%s_%s' ON '%s'(%s)" % (
                table_name, "_".join(index),
                table_name, ", ".join(map(lambda x: "'%s'" % x, index))
            )
            c.execute(sql)

    # OVERRIDE
    def _db_insert(self, table_name, columns, values, datatypes):
        val_pattern, val_values = self._sql_list_pattern("val", values)
        columns = map(lambda x: "'%s'" % x, columns)
        sql_pattern = "INSERT INTO '%s' (%s) VALUES (%s);" % (
            table_name, ", ".join(columns), val_pattern
        )
        c = self._engine.cursor()
        c.execute(sql_pattern, val_values)

    # OVERRIDE
    def _db_update(self, table_name, columns, values, condition, datatypes):
        cond_pattern, cond_values = self._get_condition_pattern(condition)
        val_pattern, val_values = self._sql_list_pattern("val", values, False)
        update_pattern = ", ".join(
            ("'%s' = %s" % (c, v) for c, v in zip(columns, val_pattern))
        )
        sql_pattern = "UPDATE '%s' SET %s WHERE %s;" % (
            table_name, update_pattern, cond_pattern
        )
        sql_values = dict(**val_values, **cond_values)
        c = self._engine.cursor()
        c.execute(sql_pattern, sql_values)

    # OVERRIDE
    def _db_delete(self, table_name, condition):
        cond_pattern, cond_values = self._get_condition_pattern(condition)
        sql_pattern = ("DELETE FROM '%s' WHERE %s;"
                       % (table_name, cond_pattern))
        c = self._engine.cursor()
        c.execute(sql_pattern, cond_values)

    # OVERRIDE
    def _get_table_names(self, prefix):
        c = self._engine.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = c.execute(sql)
        return set([x[0] for x in tables if x[0].startswith(prefix)])

    def _get_condition_pattern(self, condition, prefix="cond"):
        """Convert the given condition to a Sqlite condition pattern
        and the corresponding values.

        :param condition: The Condition
        :type condition: Uniton[AndCondition, EqualsCondition]
        :raises NotImplementedError: Unknown condition type
        :return: The resulting condition
        :rtype: str
        """
        if condition is None:
            return '1', dict()
        if isinstance(condition, EqualsCondition):
            value = condition.value
            pattern = "'%s'.'%s'=:%s_value" % (
                condition.table_name, condition.column, prefix
            )
            values = {
                "%s_value" % prefix: value
            }
            return pattern, values
        if isinstance(condition, AndCondition):
            pattern = ""
            values = dict()
            for i, sub_condition in enumerate(condition.conditions):
                if pattern:
                    pattern += " AND "
                sub_prefix = prefix + str(i)
                sub_pattern, sub_values = self._get_condition_pattern(
                    sub_condition, sub_prefix
                )
                pattern += sub_pattern
                values.update(sub_values)
                return pattern, values
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
        elif cuds_datatype == "UNDEFINED":
            return "TEXT"
        else:
            raise NotImplementedError("Unsupported data type!")
