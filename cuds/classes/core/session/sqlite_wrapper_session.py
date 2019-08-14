# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sqlite3
from .db_wrapper_session import DbWrapperSession


class SqliteWrapperSession(DbWrapperSession):

    def __init__(self, path):
        super().__init__(engine=sqlite3.connect(path))

    def __str__(self):
        return "Sqlite Wrapper Session"

    # OVERRIDE
    def _initialize_tables(self):
        c = self._engine.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS CUBA_MASTER "
                  + "(uid, cuba, first_level);")
        c.execute("CREATE TABLE IF NOT EXISTS CUBA_RELATIONSHIPS "
                  + "(origin, target, name, cuba);")

    # OVERRIDE
    def _load_first_level(self):
        pass

    # OVERRIDE
    def _apply_added(self):
        c = self._engine.cursor()

        # Create new tables
        tables = c.execute("SELECT name FROM sqlite_master "
                           + "WHERE type='table';")
        tables = set([x[0] for x in tables])
        for added in self._added.values():
            if added.uid == self.root:
                continue
            if added.cuba_key.value not in tables and added._values:
                tables.add(added.cuba_key.value)
                sql = "CREATE TABLE %s (uid, %s);" % \
                    (added.cuba_key.value, ", ".join(added._values))
                c.execute(sql)

        # Insert the items
        for added in self._added.values():
            if added.uid == self.root:
                continue
            if added._values:
                values = [getattr(added, attr) for attr in added._values]
                sql = "INSERT INTO %s (uid, %s) VALUES ('%s', '%s');" % \
                    (added.cuba_key.value,
                     ", ".join(added._values),
                     added.uid,
                     "', '".join(values))
                c.execute(sql)

            # Add to master
            is_first_level = False
            root = self._registry.get(self.root)
            for rel, uids in root.items():
                if added.uid in uids:
                    is_first_level = True
                    break
            sql = "INSERT INTO CUBA_MASTER (uid, cuba, first_level) " \
                + "VALUES('%s', '%s', '%s');" % \
                (added.uid,
                 added.cuba_key.value,
                 is_first_level
                 )
            c.execute(sql)

            # Insert the relationships
            for rel, uid_cuba in added.items():
                for uid, cuba in uid_cuba.items():
                    if uid == self.root:
                        continue
                    sql = "INSERT INTO CUBA_RELATIONSHIPS " \
                        + "(origin, target, name, cuba) VALUES " \
                        + "('%s', '%s', '%s', '%s')" % \
                        (added.uid, uid, rel.__name__, cuba)
                    c.execute(sql)

    # OVERRIDE
    def _apply_updated(self):
        pass

    # OVERRIDE
    def _apply_deleted(self):
        pass

    # OVERRIDE
    def _load_missing(self, *uids):
        pass
