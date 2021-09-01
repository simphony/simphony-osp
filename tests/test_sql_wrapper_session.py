"""Test the abstract SqlWrapper session."""

import numpy as np
import unittest2 as unittest
from rdflib import RDF, XSD, Literal

from osp.core.ontology.cuba import cuba_namespace
from osp.core.ontology.datatypes import UID, Vector
from osp.core.session import SqlWrapperSession
from osp.core.session.db.sql_util import AndCondition, JoinCondition, \
    EqualsCondition
from osp.core.namespaces import cuba

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city

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
        self.session._ns_to_idx = {str(cuba_namespace): 1}
        # , 2: str(city.get_iri())}
        self.session._idx_to_ns = {1: str(cuba_namespace)}

    def test_queries_subject_given(self):
        """Test computing the queries corresponding to a triple pattern."""
        r = sorted(self.session._queries(
            pattern=(UID(1).to_iri(), None, None)),
            key=lambda x: x[1])
        self.assertEqual(len(r), 4)
        self.assertEqual(r[0][1], data_tbl("CUSTOM_Vector"))
        self.assertEqual(r[1][1], data_tbl("XSD_string"))
        self.assertEqual(r[2][1], RELATIONSHIP_TABLE)
        self.assertEqual(r[3][1], TYPES_TABLE)
        self.assertEqual(r[0][2], Vector.iri)
        self.assertEqual(r[1][2], XSD.string)
        self.assertEqual(r[2][2], XSD.integer)
        self.assertEqual(r[3][2], XSD.integer)
        self.assertEqual(r[0][0].order, ["ts", "tp",
                                         data_tbl("CUSTOM_Vector")])

        # first query
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("CUSTOM_Vector"): ["o"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(data_tbl("CUSTOM_Vector"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("CUSTOM_Vector"), "p", "tp", "entity_idx"),
            EqualsCondition("ts", "uid", UID(1), UID.iri)
        ))
        self.assertEqual(r[0][0].datatypes, {
            data_tbl("CUSTOM_Vector"): {"o": Vector.iri},
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("CUSTOM_Vector"): data_tbl("CUSTOM_Vector")
        })

        # second query
        self.assertEqual(r[1][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("XSD_string"): ["o"]})
        self.assertEqual(r[1][0].condition, AndCondition(
            JoinCondition(data_tbl("XSD_string"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("XSD_string"), "p", "tp", "entity_idx"),
            EqualsCondition("ts", "uid", UID(1), UID.iri)
        ))
        self.assertEqual(r[1][0].datatypes, {
            data_tbl("XSD_string"): {"o": XSD.string},
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer}
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
            EqualsCondition("ts", "uid", UID(1), UID.iri)
        ))
        self.assertEqual(r[2][0].datatypes, {
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer},
            "to": {"uid": UID.iri, "cuds_idx": XSD.integer},
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
            EqualsCondition("ts", "uid", UID(1), UID.iri)
        ))
        self.assertEqual(r[3][0].datatypes, {
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "to": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer},
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
        self.assertEqual(r[0][1:], (RELATIONSHIP_TABLE, XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"], RELATIONSHIP_TABLE: [],
            "to": ["uid"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(RELATIONSHIP_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "p", "tp", "entity_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "o", "to", "cuds_idx"),
            EqualsCondition("tp", "ns_idx", 1, XSD.integer),
            EqualsCondition("tp", "name", "activeRelationship", XSD.string)
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer},
            "to": {"uid": UID.iri, "cuds_idx": XSD.integer},
            RELATIONSHIP_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE, "to": CUDS_TABLE,
            RELATIONSHIP_TABLE: RELATIONSHIP_TABLE
        })

        # type
        r = sorted(self.session._queries(
            pattern=(None, RDF.type, None)),
            key=lambda x: x[1]
        )
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (TYPES_TABLE, XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], TYPES_TABLE: [], "to": ["ns_idx", "name"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(TYPES_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(TYPES_TABLE, "o", "to", "entity_idx")
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "to": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer},
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
        self.assertEqual(r[0][1:], (data_tbl("CUSTOM_Vector"), Vector.iri))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("CUSTOM_Vector"): ["o"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(data_tbl("CUSTOM_Vector"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("CUSTOM_Vector"), "p", "tp", "entity_idx"),
            EqualsCondition("tp", "ns_idx", 2, XSD.integer),
            EqualsCondition("tp", "name", "coordinates", XSD.string)
        ))
        self.assertEqual(r[0][0].datatypes, {
            data_tbl("CUSTOM_Vector"): {"o": Vector.iri},
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("CUSTOM_Vector"): data_tbl("CUSTOM_Vector")
        })

        # data with value
        dtype = Vector.iri
        r = sorted(self.session._queries(
            pattern=(None, city.coordinates.iri,
                     Literal(np.array([1, 1]), datatype=dtype))),
                   key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (data_tbl("CUSTOM_Vector"), Vector.iri))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"],
            data_tbl("CUSTOM_Vector"): ["o"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(data_tbl("CUSTOM_Vector"), "s", "ts", "cuds_idx"),
            JoinCondition(data_tbl("CUSTOM_Vector"), "p", "tp", "entity_idx"),
            EqualsCondition("tp", "ns_idx", 2, XSD.integer),
            EqualsCondition("tp", "name", "coordinates", XSD.string),
            EqualsCondition(data_tbl("CUSTOM_Vector"), "o", Vector([1, 1]),
                            Vector.iri),
        ))
        self.assertEqual(r[0][0].datatypes, {
            data_tbl("CUSTOM_Vector"): {
                "o": Vector.iri,
            },
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE,
            data_tbl("CUSTOM_Vector"): data_tbl("CUSTOM_Vector")
        })

    def test_queries_object_given(self):
        """Test the _queries method when the object is given."""
        # type given
        r = sorted(self.session._queries(
            pattern=(None, None, city.City.iri)),
            key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (TYPES_TABLE, XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "to": ["ns_idx", "name"], TYPES_TABLE: []})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(TYPES_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(TYPES_TABLE, "o", "to", "entity_idx"),
            EqualsCondition("to", "ns_idx", 2, XSD.integer),
            EqualsCondition("to", "name", "City", XSD.string)
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "to": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer},
            TYPES_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "to": ENTITIES_TABLE, TYPES_TABLE: TYPES_TABLE
        })

        # UID given
        r = sorted(
            self.session._queries(pattern=(None, None, UID(1).to_iri())),
            key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1:], (RELATIONSHIP_TABLE, XSD.integer))
        self.assertEqual(r[0][0]._columns, {
            "ts": ["uid"], "tp": ["ns_idx", "name"], RELATIONSHIP_TABLE: [],
            "to": ["uid"]})
        self.assertEqual(r[0][0].condition, AndCondition(
            JoinCondition(RELATIONSHIP_TABLE, "s", "ts", "cuds_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "p", "tp", "entity_idx"),
            JoinCondition(RELATIONSHIP_TABLE, "o", "to", "cuds_idx"),
            EqualsCondition("to", "uid", UID(1), UID.iri)
        ))
        self.assertEqual(r[0][0].datatypes, {
            "ts": {"uid": UID.iri, "cuds_idx": XSD.integer},
            "tp": {"name": XSD.string, "ns_idx": XSD.integer,
                   "entity_idx": XSD.integer},
            "to": {"uid": UID.iri, "cuds_idx": XSD.integer},
            RELATIONSHIP_TABLE: {}
        })
        self.assertEqual(r[0][0].tables, {
            "ts": CUDS_TABLE, "tp": ENTITIES_TABLE, "to": CUDS_TABLE,
            RELATIONSHIP_TABLE: RELATIONSHIP_TABLE
        })

    def test_construct_remove_condition(self):
        """Test construction a remove condition."""
        # from rel table
        r = sorted(
            self.session._queries(
                pattern=(UID(1).to_iri(),
                         city.hasInhabitant.iri,
                         UID(2).to_iri()),
                mode="delete"),
            key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1], RELATIONSHIP_TABLE)
        self.assertEqual(r[0][2], XSD.integer)
        self.assertEqual(r[0][0], AndCondition(
            EqualsCondition(RELATIONSHIP_TABLE, "s", UID(1), XSD.integer),
            EqualsCondition(RELATIONSHIP_TABLE, "p", 42, XSD.integer),
            EqualsCondition(RELATIONSHIP_TABLE, "o", UID(2), XSD.integer)
        ))
        # from types table
        r = sorted(self.session._queries(
            pattern=(UID(1).to_iri(), RDF.type,
                     city.City.iri),
            mode="delete"), key=lambda x: x[1])
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0][1], TYPES_TABLE)
        self.assertEqual(r[0][2], XSD.integer)
        self.assertEqual(r[0][0], AndCondition(
            EqualsCondition(TYPES_TABLE, "s", UID(1), XSD.integer),
            EqualsCondition(TYPES_TABLE, "o", 42, XSD.integer)
        ))

    def test_rows_to_triples(self):
        """Test transforming sql table rows to triples."""
        # relationship table
        cursor = iter([
            (UID(1), 2, "hasInhabitant", UID(2)),
            (UID(1), 1, "activeRelationship", UID(3))
        ])
        triples = list(
            self.session._rows_to_triples(cursor, RELATIONSHIP_TABLE,
                                          XSD.integer)
        )
        self.assertEqual(triples, [
            (UID(1).to_iri(),
             city.hasInhabitant.iri,
             UID(2).to_iri()),
            (UID(1).to_iri(),
             cuba.activeRelationship.iri,
             UID(3).to_iri())
        ])

        # types table
        cursor = iter([
            (UID(1), 2, "City"), (UID(2), 1, "Entity")
        ])
        triples = list(
            self.session._rows_to_triples(cursor, TYPES_TABLE, XSD.integer)
        )
        self.assertEqual(sorted(triples), sorted([
            (UID(1).to_iri(), RDF.type, city.City.iri),
            (UID(2).to_iri(), RDF.type, cuba.Entity.iri)
        ]))

        # data table
        cursor = iter([
            (UID(1), 2, "coordinates", np.array([1, 2])),
            (UID(2), 1, "attribute", np.array([3, 4]))
        ])
        triples = list(
            self.session._rows_to_triples(
                cursor, data_tbl("CUSTOM_Vector"), Vector.iri)
        )
        self.assertEqual(triples, [
            (UID(1).to_iri(), city.coordinates.iri,
             Literal(np.array([1, 2]), datatype=Vector.iri)),
            (UID(2).to_iri(), cuba.attribute.iri,
             Literal(np.array([3, 4]), datatype=Vector.iri))
        ])

    def test_get_values(self):
        """Test the get values method for adding triples."""
        v = self.session._get_values(
            (UID(1).to_iri(), city.hasInhabitant.iri,
             UID(2).to_iri()), RELATIONSHIP_TABLE)
        self.assertEqual(v, (UID(1), 42, UID(2)))
        v = self.session._get_values(
            (UID(1).to_iri(), city.coordinates.iri,
             Literal([1, 2], datatype=Vector.iri)),
            data_tbl("CUSTOM_Vector"))
        np.testing.assert_equal(v, (UID(1), 42, [1, 2]))
        v = self.session._get_values(
            (UID(1).to_iri(),
             XSD.anyURI,
             city.City.iri),
            TYPES_TABLE)
        # The next assertion should pass using any value for the predicate
        # in the previous function.
        self.assertEqual(v, (UID(1), 42))


class MockSqlWrapperSession(SqlWrapperSession):
    """A SqlWrapper session for testing purposes."""

    def __init__(self, engine=None,
                 data_tables=(data_tbl("XSD_string"),
                              data_tbl("CUSTOM_Vector"))):
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
            yield query.condition.value, query.condition.value
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
            yield 1, str(cuba.get_iri())
            yield 2, str(city.get_iri())

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
