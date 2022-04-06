"""A session to connect osp-core to a SQLite backend."""

import sqlite3

import rdflib

from osp.core.ontology.cuba import rdflib_cuba
from osp.core.session.db.sql_util import (
    AndCondition,
    EqualsCondition,
    JoinCondition,
)
from osp.core.session.db.sql_wrapper_session import SqlWrapperSession


class SqliteSession(SqlWrapperSession):
    """A session to connect osp-core to a SQLite backend.

    This SQLite backend can be used to store CUDS in an SQLite database.
    """

    def __init__(self, path, check_same_thread=True, **kwargs):
        """Initialize the SqliteSession.

        Args:
            path (str): The path to the sqlite database file. Will be created
                if it doesn't exist.
            check_same_thread (bool, optional): Argument of sqlite.
                Defaults to True.
        """
        conn = sqlite3.connect(
            path, isolation_level=None, check_same_thread=check_same_thread
        )
        super().__init__(engine=conn, **kwargs)

    def __str__(self):
        """Convert the Session to a static string."""
        return "Sqlite Wrapper Session"

    # OVERRIDE
    def close(self):
        """Close the connection to the SQLite database."""
        self._engine.close()

    # OVERRIDE
    def _commit(self):
        """Commit the data to the SQLite database."""
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
        """Transform a list of values to corresponding pattern and value dict.

        Args:
            prefix (str): The prefix to use for the pattern
            values (List[Any]): The list of values
            join_pattern (bool): Whether to join the pattern by a comma,
                defaults to True


        Returns:
            Tuple[str, Dict]: The pattern and the value dict.
        """
        pattern = [":%s_%s" % (prefix, i) for i in range(len(values))]
        if join_pattern:
            pattern = ", ".join(pattern)
        values = {("%s_%s" % (prefix, i)): val for i, val in enumerate(values)}
        return pattern, values

    # OVERRIDE
    def _db_select(self, query):
        cond_pattern, cond_values = self._get_condition_pattern(
            query.condition
        )
        columns = ["`%s`.`%s`" % (a, c) for a, c in query.columns]
        tables = ["`%s` AS `%s`" % (t, a) for a, t in query.tables.items()]
        sql_pattern = "SELECT %s FROM %s WHERE %s;" % (  # nosec
            ", ".join(columns),
            ", ".join(tables),
            cond_pattern,
        )
        c = self._engine.cursor()
        c.execute(sql_pattern, cond_values)
        return c

    # OVERRIDE
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
        columns = [
            c
            if c not in datatypes
            else "`%s` `%s`" % (c, self._to_sqlite_datatype(datatypes[c]))
            for c in columns
        ]
        constraints = []
        if primary_key:
            constraints += [
                "PRIMARY KEY(%s)"
                % ", ".join(map(lambda x: "`%s`" % x, primary_key))
            ]
        constraints += [
            "FOREIGN KEY(`%s`) REFERENCES `%s`(`%s`)" % (col, ref[0], ref[1])
            for col, ref in foreign_key.items()
        ]
        c = self._engine.cursor()
        sql = "CREATE TABLE IF NOT EXISTS `%s` (%s);" % (
            table_name,
            ", ".join(columns + constraints),
        )
        c.execute(sql)
        for index in indexes:
            sql = "CREATE INDEX IF NOT EXISTS `idx_%s_%s` ON `%s`(%s)" % (
                table_name,
                "_".join(index),
                table_name,
                ", ".join(map(lambda x: "`%s`" % x, index)),
            )
            c.execute(sql)

    # OVERRIDE
    def _db_insert(self, table_name, columns, values, datatypes):
        val_pattern, val_values = self._sql_list_pattern("val", values)
        columns = map(lambda x: "`%s`" % x, columns)
        sql_pattern = "INSERT INTO `%s` (%s) VALUES (%s);" % (  # nosec
            table_name,
            ", ".join(columns),
            val_pattern,
        )
        c = self._engine.cursor()
        try:
            c.execute(sql_pattern, val_values)
            return c.lastrowid
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                return
            raise e

    # OVERRIDE
    def _db_update(self, table_name, columns, values, condition, datatypes):
        cond_pattern, cond_values = self._get_condition_pattern(condition)
        val_pattern, val_values = self._sql_list_pattern("val", values, False)
        update_pattern = ", ".join(
            ("`%s` = %s" % (c, v) for c, v in zip(columns, val_pattern))
        )
        sql_pattern = "UPDATE `%s` SET %s WHERE %s;" % (  # nosec
            table_name,
            update_pattern,
            cond_pattern,
        )
        sql_values = dict(**val_values, **cond_values)
        c = self._engine.cursor()
        c.execute(sql_pattern, sql_values)

    # OVERRIDE
    def _db_delete(self, table_name, condition):
        cond_pattern, cond_values = self._get_condition_pattern(condition)
        sql_pattern = "DELETE FROM `%s` WHERE %s;" % (  # nosec
            table_name,
            cond_pattern,
        )
        c = self._engine.cursor()
        c.execute(sql_pattern, cond_values)

    # OVERRIDE
    def _db_drop(self, table_name):
        sql_command = f"DROP TABLE IF EXISTS `{table_name}`"
        c = self._engine.cursor()
        c.execute(sql_command)

    # OVERRIDE
    def _get_table_names(self, prefix):
        c = self._engine.cursor()
        sql = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = c.execute(sql)
        return set([x[0] for x in tables if x[0].startswith(prefix)])

    def _get_condition_pattern(self, condition, prefix="cond"):
        """Convert the given condition.

        It should be converted to a Sqlite condition pattern
        and the corresponding values.

        Args:
            condition (Union[AndCondition, EqualsCondition]): The Condition.

        Raises:
            NotImplementedError: Unknown condition type

        Returns:
            str: The resulting condition
        """
        if condition is None:
            return "1", dict()
        if isinstance(condition, EqualsCondition):
            value = condition.value
            pattern = "`%s`.`%s`=:%s_value" % (
                condition.table_name,
                condition.column,
                prefix,
            )
            values = {"%s_value" % prefix: value}
            return pattern, values
        if isinstance(condition, JoinCondition):
            return (
                f"`{condition.table_name1}`.`{condition.column1}` = "
                f"`{condition.table_name2}`.`{condition.column2}`",
                {},
            )
        if isinstance(condition, AndCondition):
            if not condition.conditions:
                return "1", dict()
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
        raise NotImplementedError(f"Unsupported condition {condition}")

    def _to_sqlite_datatype(self, rdflib_datatype):
        """Convert the given Cuds datatype to a datatype of sqlite.

            rdflib_datatype: The given cuds_object datatype.
        :type rdflib_datatype: URIRef
        :raises NotImplementedError: Unsupported datatype given.
        :return: A sqlite datatype.
        :rtype: str
        """
        if rdflib_datatype is None:
            return "TEXT"
        if rdflib_datatype == "UID":
            return "TEXT"
        if rdflib_datatype == rdflib.XSD.integer:
            return "INTEGER"
        if rdflib_datatype == rdflib.XSD.boolean:
            return "BOOLEAN"
        if rdflib_datatype == rdflib.XSD.float:
            return "REAL"
        if rdflib_datatype == rdflib.XSD.string:
            return "REAL"
        if str(rdflib_datatype).startswith(
            str(rdflib_cuba["_datatypes/STRING-"])
        ):
            return "TEXT"
        else:
            raise NotImplementedError(
                f"Unsupported data type " f"{rdflib_datatype}!"
            )
