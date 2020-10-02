"""This file contains a tool for migrating from old to new database schemas."""

import rdflib
from osp.core.session.db.sql_wrapper_session import SqlWrapperSession
from osp.core.session.db.sql_util import SqlQuery
from osp.core.namespaces import get_entity
from osp.core.utils import iri_from_uid
from osp.core.namespaces import cuba

INT = rdflib.XSD.integer
STR = rdflib.XSD.string

versions = {
    "OSP_MASTER": 0,
    "OSP_V1_CUDS": 1
}


class SqlMigrate():
    """Tool to migrate from old to new database schema."""

    def __init__(self, sql_session: SqlWrapperSession):
        """Initialize the migration tool."""
        self.session = sql_session
        self.tables = sql_session._get_table_names("")
        self.version = min(v for tbl, v in versions.items()
                           if tbl in self.tables)
        self.max_version = max(versions.values())
        self.procedure = SqlMigrate.procedures[self.version][self.max_version]

    def run(self):
        """Run the migration."""
        self.procedure(self)

    def migrate_0_1(self):
        """Migrate from version 0 to 1."""
        self.namespaces = {}
        self.entities = {}
        self.cuds = {}

        if self.session.root is None:
            cuba.Wrapper(session=self.session)
        self.migrate_master_0_1()
        self.migrate_relations_0_1()

    def migrate_master_0_1(self):
        """Migrate the OSP_MASTER table."""
        c = self.session._do_db_select(
            SqlQuery("OSP_MASTER", ["uid", "oclass"],
                     {"uid": "UUID", "oclass": STR})
        )
        for uid, oclass in c:
            oclass = get_entity(oclass) if oclass != "" else cuba.Wrapper
            ns_iri = str(oclass.namespace.get_iri())
            oclass_iri = str(oclass.iri)
            cuds_iri = iri_from_uid(uid)

            if ns_iri not in self.namespaces:
                self.namespaces[ns_iri] = self.session._do_db_insert(
                    "OSP_V1_NAMESPACES", ["namespace"], [ns_iri],
                    {"namespace": STR}
                )
            ns_idx = self.namespaces[ns_iri]

            if oclass_iri not in self.entities:
                self.entities[oclass_iri] = self.session._do_db_insert(
                    "OSP_V1_ENTITIES", ["ns_idx", "name"],
                    [ns_idx, oclass.name], {"ns_idx": INT, "name": STR}
                )
            oclass_idx = self.entities[oclass_iri]

            if cuds_iri not in self.cuds:
                self.cuds[cuds_iri] = self.session._do_db_insert(
                    "OSP_V1_CUDS", ["uid"], [str(uid)], {"uid": "UUID"}
                )
            cuds_idx = self.cuds[cuds_iri]

            self.session._do_db_insert(
                "OSP_V1_TYPES", ["s", "o"], [cuds_idx, oclass_idx],
                {"s": INT, "o": INT}
            )

    def migrate_relations_0_1(self):
        """Migrate the relations from v0 to v1."""
        c = self.session._do_db_select(
            SqlQuery("OSP_RELATIONSHIPS", ["origin", "target", "name"],
                     {"origin": "UUID", "oclass": STR})
        )

    def no_migration(self):
        """Do nothing."""

    procedures = {
        0: {
            0: no_migration,
            1: migrate_0_1
        }
    }


if __name__ == "__main__":
    from osp.wrappers.sqlite import SqliteSession
    session = SqliteSession("test.db")
    m = SqlMigrate(session)
    m.run()
