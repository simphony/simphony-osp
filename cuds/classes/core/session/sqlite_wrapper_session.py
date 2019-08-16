# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlite3
from uuid import UUID
from cuds.classes.core.session.db_wrapper_session import DbWrapperSession


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
        c.execute("SELECT %s FROM %s WHERE %s;" % (
            ", ".join(columns),
            table_name,
            condition
        ))
        uuid_columns = [i for i, c in enumerate(columns)
                        if c in datatypes and datatypes[c] == "UUID"]
        return map(lambda v: self._convert_uuid_values(v, uuid_columns, "hex"),
                   c)

    # OVERRIDE
    def _db_create(self, table_name, columns, datatypes):
        columns = [c if c not in datatypes
                   else "%s %s" % (c, self.to_sqlite_datatype(datatypes[c]))
                   for c in columns]
        c = self._engine.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS %s (%s);" % (
            table_name,
            ", ".join(columns)
        ))

    def to_sqlite_datatype(self, cuds_datatype):
        if cuds_datatype == "UUID":
            return "TEXT"
        if cuds_datatype == "INT":
            return "INTEGER"
        if cuds_datatype == "FLOAT":
            return "REAL"
        else:
            return "TEXT"

    # OVERRIDE
    def _db_insert(self, table_name, columns, values, datatypes):
        c = self._engine.cursor()
        c.execute("INSERT INTO %s (%s) VALUES (%s);" % (
            table_name,
            ", ".join(columns),
            ", ".join(["'%s'" % v if isinstance(v, (str, UUID)) else str(v)
                       for v in values])
        ))

    # OVERRIDE
    def _db_update(self, table_name, columns, values, condition, datatypes):
        c = self._engine.cursor()
        c.execute("UPDATE %s SET %s WHERE %s;" % (
            table_name,
            ", ".join(("%s = '%s'" % (c, v)) if isinstance(v, (str, UUID))
                      else ("%s = %s" % (c, v))
                      for c, v in zip(columns, values)),
            condition
        ))

    # OVERRIDE
    def _db_delete(self, table_name, condition):
        c = self._engine.cursor()
        c.execute("DELETE FROM %s WHERE %s;" % (table_name, condition))

    # OVERRIDE
    def _get_table_names(self):
        c = self._engine.cursor()
        tables = c.execute("SELECT name FROM sqlite_master "
                           + "WHERE type='table';")
        return set([x[0] for x in tables])
