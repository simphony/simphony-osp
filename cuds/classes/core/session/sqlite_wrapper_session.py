# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlite3
from cuds.classes.core.session.db_wrapper_session import DbWrapperSession


class SqliteWrapperSession(DbWrapperSession):

    def __init__(self, path):
        super().__init__(engine=sqlite3.connect(path))

    def __str__(self):
        return "Sqlite Wrapper Session"

    def close(self):
        self._engine.close()

    def _commit(self):
        self._engine.commit()

    def _db_select(self, table_name, columns, condition):
        c = self._engine.cursor()
        c.execute("SELECT %s FROM %s WHERE %s;" % (
            ", ".join(columns),
            table_name,
            condition
        ))
        return c

    def _db_create(self, table_name, columns):
        c = self._engine.cursor()  # TODO consider data types
        c.execute("CREATE TABLE IF NOT EXISTS %s (%s);" %(
            table_name,
            ", ".join(columns)
        ))

    def _db_insert(self, table_name, columns, values):
        c = self._engine.cursor()
        c.execute("INSERT INTO %s (%s) VALUES (%s);" % (
            table_name,
            ", ".join(columns),
            ", ".join(["'%s'" % v for v in values])  # TODO consider type
        ))

    def _db_update(self, table_name, columns, values, condition):
        c = self._engine.cursor()
        c.execute("UPDATE %s SET %s WHERE %s;" % (
            table_name,  # TODO consider data type of values
            ", ".join(("%s = '%s'" % (c, v)) for c, v in zip(columns, values)),
            condition
        ))

    def _db_delete(self, table_name, condition):
        c = self._engine.cursor()
        c.execute("DELETE FROM %s WHERE %s;" % (table_name, condition))

    def _get_table_names(self):
        c = self._engine.cursor()
        tables = c.execute("SELECT name FROM sqlite_master "
                           + "WHERE type='table';")
        return set([x[0] for x in tables])
