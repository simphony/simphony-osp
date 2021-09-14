"""This file contains a tool for migrating from old to new database schemas."""

import functools

import numpy as np
from rdflib import OWL, RDF, RDFS, XSD, URIRef

from osp.core.namespaces import cuba
from osp.core.ontology.datatypes import Vector
from osp.core.session.db.sql_util import SqlQuery

INT = XSD.integer
STR = XSD.string

versions = {
    "OSP_MASTER": 0,
    "OSP_V1_CUDS": 1,
    "OSP_V2_CUDS": 2,
}

supported_versions = [2]


def detect_current_schema_version(tables):
    """Detect the current sql schema.

    Args:
        tables (List[str]): A list of the existing table names.

    Raises:
        RuntimeError: Could not detect the version.

    Returns:
        int: The version of the current data schema.
    """
    if not tables:
        return max(versions.values())
    try:
        return min(v for tbl, v in versions.items() if tbl in tables)
    except ValueError:
        raise RuntimeError("No valid data on database found. "
                           "Either database is corrupt or it has been created "
                           "with a newer version of osp-core")


def check_supported_schema_version(sql_session):
    """Raise an error if sql session has data in not-supported.

    Args:
        sql_session (): [description]

    Raises:
        RuntimeError: [description]
    """
    tables = sql_session._get_table_names("")
    if detect_current_schema_version(tables) not in supported_versions:
        raise RuntimeError("Please update your database by running "
                           "$python -m osp.wrappers.<sql_module>.migrate")
    return True


class SqlMigrate:
    """Tool to migrate from old to new database schema."""

    def __init__(self, sql_session):
        """Initialize the migration tool."""
        self.session = sql_session
        self.tables = sql_session._get_table_names("")
        self.version = detect_current_schema_version(self.tables)
        self.max_version = max(versions.values())
        self.procedure = SqlMigrate.procedures[self.version][self.max_version]

    def run(self):
        """Run the migration."""
        self.procedure(self)

    def no_migration(self):
        """Do nothing."""

    def migrate_1_2(self):
        """Migrate from version 1 to 2."""
        commit = self.session.commit  # avoid commit during initialization.
        self.session.commit = lambda: True
        self.session.check_schema = lambda: True
        cuba.Wrapper(session=self.session)
        try:
            self.migrate_1_2_cut_table(
                'OSP_V1_CUDS',
                "OSP_V2_CUDS",
                {"cuds_idx": INT,
                 "uid": URIRef('http://www.osp-core.com/types#UID')}
            )
            self.migrate_1_2_cut_table(
                'OSP_V1_NAMESPACES',
                "OSP_V2_NAMESPACES",
                {"ns_idx": INT, "namespace": STR})
            self.migrate_1_2_cut_table(
                'OSP_V1_ENTITIES',
                "OSP_V2_ENTITIES",
                {"entity_idx": INT, "ns_idx": INT, "name": STR},
            )
            self.migrate_1_2_cut_table(
                'OSP_V1_RELATIONS',
                "OSP_V2_RELATIONS",
                {"s": INT, "p": INT, "o": INT},
            )
            self.migrate_1_2_cut_table(
                'OSP_V1_TYPES',
                "OSP_V2_TYPES",
                {"s": INT, "o": INT},
            )
            self.migrate_1_2_vectors()
            self.migrate_1_2_strings()
            self.migrate_1_2_standard_data_types()
            commit()
        except Exception as e:
            self.session.rollback_transaction()
            raise e

    migrate_1_2_YML_numpy = {
        "BOOL": np.dtype('bool'),
        "INT": np.dtype('int'),
        "FLOAT": np.dtype('float'),
        "STRING": np.dtype('str'),
    }

    migrate_1_2_YML_RDF = {
        "BOOL": XSD.boolean,
        "INT": XSD.integer,
        "FLOAT": XSD.float,
        "STRING": XSD.string,
    }

    def migrate_1_2_cut_table(self, source_table_name,
                              target_table_name, dtypes):
        """Cut all entries from table and paste them in another table.

        Both the source and the target tables must already exist. The source
        table is dropped after the process is complete.
        """
        c = self.session._do_db_select(SqlQuery(source_table_name,
                                                list(dtypes.keys()),
                                                dtypes))
        for row in c:
            self.session._do_db_insert(target_table_name,
                                       list(dtypes.keys()),
                                       row,
                                       dtypes)
        self.session._do_db_drop(source_table_name)

    def migrate_1_2_standard_data_types(self):
        """Transfer the standard data types to the new tables."""
        tables = (x for x in self.session._get_table_names("")
                  if x.startswith('DATA_V1_')
                  and not any(x.startswith(prefix)
                              for prefix in ('DATA_V1_VECTOR',
                                             'DATA_V1_STRING')))
        for table in tables:
            datatype = table[len('DATA_V1_'):]
            c = self.session._do_db_select(
                SqlQuery(
                    table, ["s", "p", "o"],
                    {"s": INT, "p": INT,
                     "o": self.aux_1_2_data_table_name_to_datatype(table)}))
            for row in c:
                self.session._do_db_insert(
                    f"OSP_DATA_V2_{datatype}", ["s", "p", "o"],
                    row,
                    {"s": INT, "p": INT,
                     "o": self.aux_1_2_data_table_name_to_datatype(table)}
                )
            self.session._do_db_drop(table)

    def migrate_1_2_vectors(self):
        """Transfer the vectors to their new tables and format."""
        vector_tables = (x for x in self.session._get_table_names("")
                         if x.startswith('DATA_V1_VECTOR-'))
        self.session._do_db_create(
            table_name='OSP_DATA_V2_CUSTOM_Vector',
            columns=["s", "p", "o"],
            datatypes={"s": INT, "p": INT, "o": Vector.iri},
            primary_key=["s", "p", "o"],
            generate_pk=False,
            foreign_key={
                "s": ("OSP_V2_CUDS", "cuds_idx"),
                "p": ("OSP_V2_ENTITIES", "entity_idx")
            },
            indexes=["s", "p"],
        )
        for table in vector_tables:
            data_type = table
            data_type = data_type[len('DATA_V1_VECTOR-'):]
            data_type = data_type[0:data_type.find('-')]
            shape = table
            shape = shape[len('DATA_V1_VECTOR-' + data_type + '-'):]
            shape = shape.split('-')
            shape = tuple(int(x) for x in shape)
            num_elements = functools.reduce(lambda x, y: x * y, shape)
            vector_colums = tuple(f'o___{i}' for i in range(0, num_elements))
            c = self.session._do_db_select(
                SqlQuery(table, ["s", "p", *[v_c for v_c in vector_colums]],
                         {"s": INT,
                          "p": INT,
                          **{
                              v_c: self.migrate_1_2_YML_RDF[data_type]
                              for v_c in vector_colums
                          }})
            )
            for row in c:
                array = np.array(row[2:],
                                 dtype=self.migrate_1_2_YML_numpy[data_type])
                array.shape = shape
                vector = Vector(array)
                self.session._do_db_insert(
                    "OSP_DATA_V2_CUSTOM_Vector", ["s", "p", "o"],
                    [row[0], row[1], vector],
                    {"s": INT, "p": INT, "o": Vector.iri}
                )
            self.session._do_db_drop(table)

    def migrate_1_2_strings(self):
        """Convert the fixed-length strings to standrd XSD strings."""
        string_tables = (x for x in self.session._get_table_names("")
                         if x.startswith('DATA_V1_STRING-'))
        for table in string_tables:
            c = self.session._do_db_select(
                SqlQuery(table, ["s", "p", "o"],
                         {"s": INT, "p": INT, "o": STR}))
            for row in c:
                self.session._do_db_insert(
                    "OSP_DATA_V2_XSD_string", ["s", "p", "o"],
                    row,
                    {"s": INT, "p": INT, "o": STR}
                )
            self.session._do_db_drop(table)

    @staticmethod
    def aux_1_2_data_table_name_to_datatype(table):
        """Get datatype from data table name (v1 names)."""
        datatype = table[len('DATA_V1_'):]
        if datatype.startswith('XSD_'):
            return getattr(XSD, datatype[len('XSD_'):])
        if datatype.startswith('OWL_'):
            return getattr(OWL, datatype[len('OWL_'):])
        if datatype.startswith('RDF_'):
            return getattr(RDF, datatype[len('RDF_'):])
        if datatype.startswith('RDFS_'):
            return getattr(RDFS, datatype[len('RDFS_'):])
        raise NotImplementedError(f"Unsupported datatype {datatype}")

    def migrate_0_2(self):
        """Migration from v0 is not supported.

        Request the user to use v3.5.5-beta to migrate to v1 instead, then use
        a later version of OSP-core to migrate from v1 to v2.
        """
        raise NotImplementedError("Migrating from the schema of this "
                                  "database version is not supported by the "
                                  "current version of OSP-core."
                                  "Please download the latest compatible "
                                  "version (v3.5.5-beta) from "
                                  "https://github.com/simphony/osp-core/"
                                  "releases/tag/v3.5.5-beta, install it, and"
                                  "migrate your database by running "
                                  "$python -m osp.wrappers.<sql_module>."
                                  "migrate. Make sure that the ontologies "
                                  "that the database is using are installed."
                                  "\n"
                                  "Afterwards, install again an up-to-date "
                                  "version of OSP-core and migrate again "
                                  "using the same command.")

    def migrate_0_1(self):
        """Migration from v0 is not supported.

        In addition, the user is trying to migrate to v1 which is already
        outdated. Request migration to v2 instead.
        """
        raise NotImplementedError("The version of the schema you want to "
                                  "migrate to is currently not supported. "
                                  "Please migrate to the newest version of "
                                  "the schema instead.")

    procedures = {
        0: {
            0: no_migration,
            1: migrate_0_1,
            2: migrate_0_2,
        },
        1: {
            1: no_migration,
            2: migrate_1_2,
        }
    }


if __name__ == "__main__":
    from osp.wrappers.sqlite import SQLiteInterface
    session = SQLiteInterface("test.interfaces")
    m = SqlMigrate(session)
    m.run()
