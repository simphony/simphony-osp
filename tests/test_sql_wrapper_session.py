"""Test the abstract SqlWrapper session."""

import unittest2 as unittest
import rdflib
import uuid
import numpy as np
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.session import SqlWrapperSession
from osp.core.session.db.sql_util import AndCondition, JoinCondition, \
    EqualsCondition
from osp.core.utils import iri_from_uid
from osp.core.namespaces import cuba

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

CUDS_TABLE = SqlWrapperSession.CUDS_TABLE
ENTITIES_TABLE = SqlWrapperSession.ENTITIES_TABLE
TYPES_TABLE = SqlWrapperSession.TYPES_TABLE
NAMESPACES_TABLE = SqlWrapperSession.NAMESPACES_TABLE
RELATIONSHIP_TABLE = SqlWrapperSession.RELATIONSHIP_TABLE
DATA_TABLE_PREFIX = SqlWrapperSession.DATA_TABLE_PREFIX


def data_tbl(suffix):
    """Prepend data table prefix."""
    return DATA_TABLE_PREFIX + suffix


class TestSqlWrapperSession(unittest.TestCase):
    """Test helper method of the Sql Wrapper."""

    def setUp(self):
        """Create the session."""
        self.session = MockSqlWrapperSession()
        # , str(city.get_iri()): 2}
        self.session._ns_to_idx = {str(rdflib_cuba): 1}
        # , 2: str(city.get_iri())}
        self.session._idx_to_ns = {1: str(rdflib_cuba)}

    def test_queries_subject_given(self):
        """Test computing the queries corresponding to a triple pattern."""
        r = sorted(self.session._queries(
            pattern=(iri_from_uid(uuid.UUID(int=1)),
                     None, None)), key=lambda x: x[1])
        self.assertEqual(len(r), 4)
        self.assertEqual(r[0][1], data_tbl("VECTOR-2-2"))
        self.assertEqual(r[1][1], data_tbl("XSD_string"))
        self.assertEqual(r[2][1], RELATIONSHIP_TABLE)
        self.assertEqual(r[3][1], TYPES_TABLE)
        self.assertEqual(r[0][2], rdflib_cuba["_datatypes/VECTOR-2-2"])
        self.assertEqual(r[1][2], rdflib.XSD.string)
        self.assertEqual(r[2][2], rdflib.XSD.integer)
        self.assertEqual(r[3][2], rdflib.XSD.integer)
        self.assertEqual(r[0][0].order, ["ts", "tp", data_tbl("VECTOR-2-2")])

        # first query
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("VECTOR-2-2"): ["o___0", "o___1", "o___2", "o___3"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(data_tbl("VECTOR-2-2"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("VECTOR-2-2"), "p", "tp", "entity_idx"),
            EqualsCondition("ts", "uid", str(uuid.UUID(int=1)), "UUID")
        ))
        self.assertEqual(r[0][0].datatypes, {
            data_tbl("VECTOR-2-2"): {"o": rdflib_cuba["_datatypes/VECTOR-2-2"],
                                     "o___0": rdflib.XSD.float,
                                     "o___1": rdflib.XSD.float,
                                     "o___2": rdflib.XSD.float,
                                     "o___3": rdflib.XSD.float},
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("VECTOR-2-2"): data_tbl("VECTOR-2-2")
        })

        # second query
        self.assertEqual(r[1][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("XSD_string"): ["o"]})
        self.assertEqual(r[1][0].condition, AndCondition(
            JoinCondition(data_tbl("XSD_string"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("XSD_string"), "p", "tp", "entity_idx"),
            EqualsCondition("ts", "uid", str(uuid.UUID(int=1)), "UUID")
        ))
        self.assertEqual(r[1][0].datatypes, {
            data_tbl("XSD_string"): {"o": rdflib.XSD.string},
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer}
        })
        self.assertEqual(r[1][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("XSD_string"): data_tbl("XSD_string")
        })

        # third query
        self.assertEqual(r[2][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"], RELATIONSHIP_TABLE: [],
            "to": ["uid"]})
        self.assertEqual(r[2][0].condition, AndCondition(
            JoinCondition(RELATIONSHIP_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "p", "tp", "entity_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "o", "to", "cuds_idx"),
            EqualsCondition("ts", "uid", str(uuid.UUID(int=1)), "UUID")
        ))
        self.assertEqual(r[2][0].datatypes, {
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer},
            "to": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            RELATIONSHIP_TABLE: {}
        })
        self.assertEqual(r[2][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE, "to": CUDS_TABLE,
            RELATIONSHIP_TABLE: RELATIONSHIP_TABLE
        })

        # fourth query
        self.assertEqual(r[3][0]._columns, {
            "ts": ["uid"], TYPES_TABLE: [], "to": ["ns_idx", "name"]})
        self.assertEqual(r[3][0].condition, AndCondition(
            JoinCondition(TYPES_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(TYPES_TABLE, "o", "to", "entity_idx"),
            EqualsCondition("ts", "uid", str(uuid.UUID(int=1)), "UUID")
        ))
        self.assertEqual(r[3][0].datatypes, {
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "to": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer},
            TYPES_TABLE: {}
        })
        self.assertEqual(r[3][0].tables, {
            "ts": CUDS_TABLE, "to": ENTITIES_TABLE, TYPES_TABLE: TYPES_TABLE
        })

    def test_queries_predicate_given(self):
        """Test the _queries method with a given relationship."""
        # object property
        r = sorted(self.session._queries(
            pattern=(None, cuba.activeRelationship.iri, None)),
            key=lambda x: x[1]
        )
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (RELATIONSHIP_TABLE, rdflib.XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"], RELATIONSHIP_TABLE: [],
            "to": ["uid"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(RELATIONSHIP_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "p", "tp", "entity_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "o", "to", "cuds_idx"),
            EqualsCondition("tp", "ns_idx", 1, rdflib.XSD.integer),
            EqualsCondition("tp", "name", "activeRelationship",
                            rdflib.XSD.string)
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer},
            "to": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            RELATIONSHIP_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE, "to": CUDS_TABLE,
            RELATIONSHIP_TABLE: RELATIONSHIP_TABLE
        })

        # type
        r = sorted(self.session._queries(
            pattern=(None, rdflib.RDF.type, None)),
            key=lambda x: x[1]
        )
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (TYPES_TABLE, rdflib.XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], TYPES_TABLE: [], "to": ["ns_idx", "name"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(TYPES_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(TYPES_TABLE, "o", "to", "entity_idx")
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "to": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer},
            TYPES_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "to": ENTITIES_TABLE, TYPES_TABLE: TYPES_TABLE
        })

        # data
        r = sorted(self.session._queries(
            pattern=(None, city.coordinates.iri, None)),
            key=lambda x: x[1]
        )
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (data_tbl("VECTOR-INT-2"),
                                    rdflib_cuba["_datatypes/VECTOR-INT-2"]))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("VECTOR-INT-2"): ["o___0", "o___1"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(data_tbl("VECTOR-INT-2"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("VECTOR-INT-2"), "p", "tp", "entity_idx"),
            EqualsCondition("tp", "ns_idx", 2, rdflib.XSD.integer),
            EqualsCondition("tp", "name", "coordinates", rdflib.XSD.string)
        ))
        self.assertEqual(r[0][0].datatypes, {
            data_tbl("VECTOR-INT-2"): {
                "o": rdflib_cuba["_datatypes/VECTOR-INT-2"],
                "o___1": rdflib.XSD.integer,
                "o___0": rdflib.XSD.integer
            },
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("VECTOR-INT-2"): data_tbl("VECTOR-INT-2")
        })

        # data with value
        dtype = rdflib_cuba["_datatypes/VECTOR-INT-2"]
        r = sorted(self.session._queries(
            pattern=(None, city.coordinates.iri,
                     rdflib.Literal(np.array([1, 1]), datatype=dtype))),
                   key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (data_tbl("VECTOR-INT-2"),
                                    rdflib_cuba["_datatypes/VECTOR-INT-2"]))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("VECTOR-INT-2"): ["o___0", "o___1"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(data_tbl("VECTOR-INT-2"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("VECTOR-INT-2"), "p", "tp", "entity_idx"),
            EqualsCondition("tp", "ns_idx", 2, rdflib.XSD.integer),
            EqualsCondition("tp", "name", "coordinates", rdflib.XSD.string),
            AndCondition(
                EqualsCondition(data_tbl("VECTOR-INT-2"), "o___0",
                                1, rdflib.XSD.integer),
                EqualsCondition(data_tbl("VECTOR-INT-2"), "o___1",
                                1, rdflib.XSD.integer),
            )
        ))
        self.assertEqual(r[0][0].datatypes, {
            data_tbl("VECTOR-INT-2"): {
                "o": rdflib_cuba["_datatypes/VECTOR-INT-2"],
                "o___0": rdflib.XSD.integer,
                "o___1": rdflib.XSD.integer
            },
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("VECTOR-INT-2"): data_tbl("VECTOR-INT-2")
        })

    def test_queries_object_given(self):
        """Test the _queries method when the object is given."""
        # type given
        r = sorted(self.session._queries(
            pattern=(None, None, city.City.iri)),
            key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (TYPES_TABLE, rdflib.XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "to": ["ns_idx", "name"], TYPES_TABLE: []})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(TYPES_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(TYPES_TABLE, "o", "to", "entity_idx"),
            EqualsCondition("to", "ns_idx", 2, rdflib.XSD.integer),
            EqualsCondition("to", "name", "City", rdflib.XSD.string)
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "to": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer},
            TYPES_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "to": ENTITIES_TABLE, TYPES_TABLE: TYPES_TABLE
        })

        # UUID given
        r = sorted(self.session._queries(
            pattern=(None, None, iri_from_uid(uuid.UUID(int=1)))),
            key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (RELATIONSHIP_TABLE, rdflib.XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"], RELATIONSHIP_TABLE: [],
            "to": ["uid"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(RELATIONSHIP_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "p", "tp", "entity_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "o", "to", "cuds_idx"),
            EqualsCondition("to", "uid", str(uuid.UUID(int=1)), "UUID")
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            "tp": {"name": rdflib.XSD.string, "ns_idx": rdflib.XSD.integer,
                   "entity_idx": rdflib.XSD.integer},
            "to": {"uid": "UUID", "cuds_idx": rdflib.XSD.integer},
            RELATIONSHIP_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE, "to": CUDS_TABLE,
            RELATIONSHIP_TABLE: RELATIONSHIP_TABLE
        })

    def test_construct_remove_condition(self):
        """Test construction a remove condition."""
        # from rel table
        r = sorted(self.session._queries(
            pattern=(iri_from_uid(uuid.UUID(int=1)), city.hasInhabitant.iri,
                     iri_from_uid(uuid.UUID(int=2))), mode="delete"),
                   key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1], RELATIONSHIP_TABLE)
        self.assertEqual(r[0][2], rdflib.XSD.integer)
        self.assertEqual(r[0][0], AndCondition(
            EqualsCondition(RELATIONSHIP_TABLE, "s", 1, rdflib.XSD.integer),
            EqualsCondition(RELATIONSHIP_TABLE, "p", 42, rdflib.XSD.integer),
            EqualsCondition(RELATIONSHIP_TABLE, "o", 2, rdflib.XSD.integer)
        ))
        # from types table
        r = sorted(self.session._queries(
            pattern=(iri_from_uid(uuid.UUID(int=1)), rdflib.RDF.type,
                     city.City.iri),
            mode="delete"), key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1], TYPES_TABLE)
        self.assertEqual(r[0][2], rdflib.XSD.integer)
        self.assertEqual(r[0][0], AndCondition(
            EqualsCondition(TYPES_TABLE, "s", 1, rdflib.XSD.integer),
            EqualsCondition(TYPES_TABLE, "o", 42, rdflib.XSD.integer)
        ))

    def test_rows_to_triples(self):
        """Test transforming sql table rows to triples."""
        # relationship table
        cursor = iter([
            (uuid.UUID(int=1), 2, "hasInhabitant", uuid.UUID(int=2)),
            (uuid.UUID(int=1), 1, "activeRelationship", uuid.UUID(int=3))
        ])
        triples = list(
            self.session._rows_to_triples(cursor, RELATIONSHIP_TABLE,
                                          rdflib.XSD.integer)
        )
        self.assertEqual(triples, [
            (iri_from_uid(uuid.UUID(int=1)), city.hasInhabitant.iri,
             iri_from_uid(uuid.UUID(int=2))),
            (iri_from_uid(uuid.UUID(int=1)), cuba.activeRelationship.iri,
             iri_from_uid(uuid.UUID(int=3)))
        ])

        # types table
        cursor = iter([
            (uuid.UUID(int=1), 2, "City"), (uuid.UUID(int=2), 1, "Entity")
        ])
        triples = list(
            self.session._rows_to_triples(cursor, TYPES_TABLE,
                                          rdflib.XSD.integer)
        )
        self.assertEqual(sorted(triples), sorted([
            (iri_from_uid(uuid.UUID(int=1)), rdflib.RDF.type, city.City.iri),
            (iri_from_uid(uuid.UUID(int=2)), rdflib.RDF.type, cuba.Entity.iri)
        ]))

        # data table
        cursor = iter([
            (uuid.UUID(int=1), 2, "coordinates", np.array([1, 2])),
            (uuid.UUID(int=2), 1, "attribute", np.array([3, 4]))
        ])
        triples = list(
            self.session._rows_to_triples(
                cursor, data_tbl("VECTOR-INT-2"),
                rdflib_cuba["_datatypes/VECTOR-INT-2"])
        )
        self.assertEqual(triples, [
            (iri_from_uid(uuid.UUID(int=1)), city.coordinates.iri,
             rdflib.Literal(np.array([1, 2]),
                            datatype=rdflib_cuba["_datatypes/VECTOR-INT-2"])),
            (iri_from_uid(uuid.UUID(int=2)), cuba.attribute.iri,
             rdflib.Literal(np.array([3, 4]),
                            datatype=rdflib_cuba["_datatypes/VECTOR-INT-2"]))
        ])

    def test_get_values(self):
        """Test the get values method for adding triples."""
        v = self.session._get_values(
            (iri_from_uid(uuid.UUID(int=1)), city.hasInhabitant.iri,
             iri_from_uid(uuid.UUID(int=2))), RELATIONSHIP_TABLE)
        self.assertEqual(v, (1, 42, 2))
        v = self.session._get_values(
            (iri_from_uid(uuid.UUID(int=1)), city.coordinates.iri,
             rdflib.Literal(np.array([1, 2]),
                            datatype=rdflib_cuba["_datatypes/VECTOR-INT-2"])),
            data_tbl("VECTOR-INT-2"))
        np.testing.assert_equal(v, (1, 42, np.array([1, 2])))
        v = self.session._get_values(
            (iri_from_uid(uuid.UUID(int=1)), rdflib.XSD.type, city.City.iri),
            TYPES_TABLE)
        self.assertEqual(v, (1, 42))


class MockSqlWrapperSession(SqlWrapperSession):
    """A SqlWrapper session for testing purposes."""

    def __init__(self, engine=None,
                 data_tables=(data_tbl("XSD_string"), data_tbl("VECTOR-2-2"))):
        """Call the super constructor."""
        self._data_tables = data_tables
        super().__init__(engine)

    def __str__(self):
        """Create a string representation of the mock session."""
        return "Mock SQL session"

    def _db_create(self, *args, **kwargs):
        """Do nothing."""

    def _db_delete(self, *args, **kwargs):
        """Do nothing."""

    def _db_insert(self, table_name, columns, values, datatypes):
        """Do nothing."""
        if (
            table_name == NAMESPACES_TABLE and columns == ["namespace"]
            and values == [str(city.get_iri())]
        ):
            return 2

    def _db_select(self, query):
        """Do nothing."""
        if (
            list(query.tables.values()) == [CUDS_TABLE]
            and list(query._columns.values()) == [["cuds_idx", "uid"]]

        ):
            yield int(query.condition.value[-1]), query.condition.value
        elif (
            list(query.tables.values()) == [ENTITIES_TABLE]
            and list(query._columns.values()) == [
                ["entity_idx", "ns_idx", "name"]]

        ):
            yield 42, 2, "hasInhabitant"
        elif (
            list(query.tables.values()) == [NAMESPACES_TABLE]
            and list(query._columns.values()) == [
                ["ns_idx", "namespace"]]
        ):
            yield (1, cuba.get_iri())
            yield (2, city.get_iri())

    def _db_update(self, *args, **kwargs):
        """Do nothing."""

    def _get_table_names(self, prefix):
        """Do nothing."""
        assert prefix == SqlWrapperSession.DATA_TABLE_PREFIX
        return self._data_tables

    def _init_transaction(self, *args, **kwargs):
        """Do nothing."""

    def _rollback_transaction(self, *args, **kwargs):
        """Do nothing."""

    def close(self, *args, **kwargs):
        """Do nothing."""

    def _db_drop(self, table_name):
        """Do nothing."""


if __name__ == '__main__':
    unittest.main()
