"""Test the abstract SqlWrapper session."""

import unittest2 as unittest
import numpy as np
from rdflib import RDF, RDFS, SKOS, XSD, URIRef

from osp.core.ontology.datatypes import Vector
from osp.core.session.db.sql_wrapper_session import SqlWrapperSession
from osp.core.session.db.sql_util import (
    SqlQuery, EqualsCondition, JoinCondition, AndCondition,
    determine_datatype, get_data_table_name, check_characters,
)

COLS = ['1', '2', '3']
DTYPES = {"1": XSD.integer,
          "2": Vector.iri}
VALS = [100, np.array([1, 2]), np.array([[1, 2, 3], [2, 3, 4]])]

DATA_TABLE_PREFIX = SqlWrapperSession.DATA_TABLE_PREFIX


def data_tbl(suffix):
    """Prepend data table prefix."""
    return DATA_TABLE_PREFIX + suffix


class TestSqlUtil(unittest.TestCase):
    """Test the utility methods for sql wrappers."""

    def test_sql_query(self):
        """Test the SqlQuery class."""
        q = SqlQuery("my_table", COLS, DTYPES, "alias")
        self.assertEqual(q.order, ["alias"])
        self.assertEqual(q.tables, {"alias": "my_table"})
        self.assertEqual(q.condition, None)

        # test WHERE
        c1 = EqualsCondition("my_table", "1", VALS[0], DTYPES["1"])
        c2 = EqualsCondition("my_table", "2", VALS[1], DTYPES["2"])
        q.where(c1)
        self.assertEqual(q.condition, c1)
        q.condition = None
        q.where(c2)
        self.assertIsInstance(q.condition, EqualsCondition)
        q.condition = None
        q.where(c1)
        q.where(c2)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 2)
        q.condition = None
        q.where(c2)
        q.where(c1)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 2)
        q.condition = None
        q.where(c1)
        q.where(c1)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 1)
        self.assertEqual(q.condition, AndCondition(c1))

        # test JOIN
        c3 = JoinCondition("alias", "1", "alias2", "1")
        q.join("2ndTable", COLS, DTYPES, alias="alias2")
        self.assertEqual(q.order, ["alias", "alias2"])
        self.assertEqual(q.tables, {"alias": "my_table", "alias2": "2ndTable"})
        self.assertEqual(q.condition, AndCondition(c1))
        q.where(c3)
        self.assertEqual(q.condition, AndCondition(c1, c3))

    def test_determine_datatype(self):
        """Test determining the datatype of a table."""
        self.assertEqual(determine_datatype(data_tbl("XSD_integer")),
                         XSD.integer)
        self.assertEqual(determine_datatype(data_tbl("OWL_rational")),
                         URIRef('http://www.w3.org/2002/07/owl#rational'))
        # Replaced OWL.rational with URIRef('...'), as it seems to
        # have disappeared in rdflib 6.0.0.
        # TODO: return to original form when a fix for rdflib is available.
        self.assertEqual(determine_datatype(data_tbl("RDF_PlainLiteral")),
                         RDF.PlainLiteral)
        self.assertEqual(determine_datatype(data_tbl("RDFS_Literal")),
                         RDFS.Literal)
        self.assertEqual(determine_datatype(data_tbl("CUSTOM_Vector")),
                         Vector.iri)

    def test_get_data_table_name(self):
        """Test getting the name of a data table from data type."""
        self.assertEqual(get_data_table_name(XSD.integer),
                         data_tbl("XSD_integer"))
        self.assertEqual(get_data_table_name(
            URIRef('http://www.w3.org/2002/07/owl#rational')),
            data_tbl("OWL_rational"))
        # Replaced OWL.rational with URIRef('...'), as it seems to
        # have disappeared in rdflib 6.0.0.
        # TODO: return to original form when a fix for rdflib is available.
        self.assertEqual(get_data_table_name(RDF.PlainLiteral),
                         data_tbl("RDF_PlainLiteral"))
        self.assertEqual(get_data_table_name(RDFS.Literal),
                         data_tbl("RDFS_Literal"))
        self.assertEqual(
            get_data_table_name(Vector.iri),
            data_tbl("CUSTOM_Vector")
        )
        self.assertRaises(NotImplementedError,
                          get_data_table_name, SKOS.prefLabel)

    def test_check_characters(self):
        """Test character check."""
        c1 = EqualsCondition("c", "d", "e", XSD.string)
        c2 = EqualsCondition("c;", "d", "e", XSD.string)
        c3 = EqualsCondition("c", "d;", "e", XSD.string)
        c4 = JoinCondition("g", "h", "i", "j")
        c5 = JoinCondition("g;", "h", "i", "j")
        c6 = JoinCondition("g", "h;", "i", "j")
        c7 = JoinCondition("g", "h", "i;", "j")
        c8 = JoinCondition("g", "h", "i", "j;")
        x = {"key": ["a", ("b", AndCondition(c1, c4))]}
        x1 = {"key;": ["a", ("b", AndCondition(c1, c4))]}
        x2 = {"key": ["a;", ("b", AndCondition(c1, c4))]}
        x3 = {"key": ["a", ("b;", AndCondition(c1, c4))]}

        x4 = {"key": ["a", ("b", AndCondition(c2, c4))]}
        x5 = {"key": ["a", ("b", AndCondition(c3, c4))]}

        x6 = {"key": ["a", ("b", AndCondition(c1, c5))]}
        x7 = {"key": ["a", ("b", AndCondition(c1, c6))]}
        x8 = {"key": ["a", ("b", AndCondition(c1, c7))]}
        x9 = {"key": ["a", ("b", AndCondition(c1, c8))]}
        check_characters(x)
        self.assertRaises(ValueError, check_characters, x1)
        self.assertRaises(ValueError, check_characters, x2)
        self.assertRaises(ValueError, check_characters, x3)
        self.assertRaises(ValueError, check_characters, x4)
        self.assertRaises(ValueError, check_characters, x5)
        self.assertRaises(ValueError, check_characters, x6)
        self.assertRaises(ValueError, check_characters, x7)
        self.assertRaises(ValueError, check_characters, x8)
        self.assertRaises(ValueError, check_characters, x9)


if __name__ == '__main__':
    unittest.main()
