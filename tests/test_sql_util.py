"""Test the abstract SqlWrapper session."""

import numpy as np
import rdflib
import unittest2 as unittest

from osp.core.ontology.cuba import rdflib_cuba
from osp.core.session.db.sql_util import (
    AndCondition,
    EqualsCondition,
    JoinCondition,
    SqlQuery,
    check_characters,
    contract_vector_values,
    determine_datatype,
    expand_vector_cols,
    get_data_table_name,
    get_expanded_cols,
)
from osp.core.session.db.sql_wrapper_session import SqlWrapperSession

COLS = ["1", "2", "3"]
DTYPES = {
    "1": rdflib.XSD.integer,
    "2": rdflib_cuba["_datatypes/VECTOR-2"],
    "3": rdflib_cuba["_datatypes/VECTOR-2-3"],
}
VALS = [100, np.array([1, 2]), np.array([[1, 2, 3], [2, 3, 4]])]
EXPANDED_COLS = [
    "1",
    "2___0",
    "2___1",
    "3___0",
    "3___1",
    "3___2",
    "3___3",
    "3___4",
    "3___5",
]
EXPANDED_DTYPES = {
    "1": rdflib.XSD.integer,
    "2": rdflib_cuba["_datatypes/VECTOR-2"],
    "2___0": rdflib.XSD.float,
    "2___1": rdflib.XSD.float,
    "3": rdflib_cuba["_datatypes/VECTOR-2-3"],
    "3___0": rdflib.XSD.float,
    "3___1": rdflib.XSD.float,
    "3___2": rdflib.XSD.float,
    "3___3": rdflib.XSD.float,
    "3___4": rdflib.XSD.float,
    "3___5": rdflib.XSD.float,
}
EXPANDED_VALS = [100, 1, 2, 1, 2, 3, 2, 3, 4]

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
        self.assertEqual(q._columns, {"alias": EXPANDED_COLS})
        self.assertEqual(q.datatypes, {"alias": EXPANDED_DTYPES})
        self.assertEqual(q.condition, None)

        # test WHERE
        c1 = EqualsCondition("my_table", "1", VALS[0], DTYPES["1"])
        c2 = EqualsCondition("my_table", "2", VALS[1], DTYPES["2"])
        c21 = EqualsCondition(
            "my_table", "2___0", VALS[1][0], EXPANDED_DTYPES["2___0"]
        )
        c22 = EqualsCondition(
            "my_table", "2___1", VALS[1][1], EXPANDED_DTYPES["2___1"]
        )
        c3 = EqualsCondition("my_table", "3", VALS[2], DTYPES["2"])
        c3 = AndCondition(c1, c2, c3)
        q.where(c1)
        self.assertEqual(q.condition, c1)
        q.condition = None
        q.where(c2)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 2)
        self.assertEqual(q.condition, AndCondition(c21, c22))
        q.condition = None
        q.where(c1)
        q.where(c2)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 3)
        self.assertEqual(q.condition, AndCondition(c1, c21, c22))
        q.condition = None
        q.where(c2)
        q.where(c1)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 3)
        self.assertEqual(q.condition, AndCondition(c1, c21, c22))
        q.condition = None
        q.where(c1)
        q.where(c1)
        self.assertIsInstance(q.condition, AndCondition)
        self.assertEqual(len(q.condition.conditions), 1)
        self.assertEqual(q.condition, AndCondition(c1))

        # test JOIN
        c4 = JoinCondition("alias", "1", "alias2", "1")
        q.join("2ndTable", COLS, DTYPES, alias="alias2")
        self.assertEqual(q.order, ["alias", "alias2"])
        self.assertEqual(q.tables, {"alias": "my_table", "alias2": "2ndTable"})
        self.assertEqual(
            q._columns, {"alias": EXPANDED_COLS, "alias2": EXPANDED_COLS}
        )
        self.assertEqual(
            q.datatypes, {"alias": EXPANDED_DTYPES, "alias2": EXPANDED_DTYPES}
        )
        self.assertEqual(q.condition, AndCondition(c1))
        q.where(c4)
        self.assertEqual(q.condition, AndCondition(c1, c4))

    def test_determine_datatype(self):
        """Test determining the datatype of a table."""
        self.assertEqual(
            determine_datatype(data_tbl("XSD_integer")), rdflib.XSD.integer
        )
        self.assertEqual(
            determine_datatype(data_tbl("OWL_rational")),
            rdflib.URIRef("http://www.w3.org/2002/07/owl" "#rational"),
        )
        # Replaced rdflib.OWL.rational with URIRef('...'), as it seems to
        # have disappeared in rdflib 6.0.0.
        # TODO: return to original form when a fix for rdflib is available.
        self.assertEqual(
            determine_datatype(data_tbl("RDF_PlainLiteral")),
            rdflib.RDF.PlainLiteral,
        )
        self.assertEqual(
            determine_datatype(data_tbl("RDFS_Literal")), rdflib.RDFS.Literal
        )
        self.assertEqual(
            determine_datatype(data_tbl("VECTOR-2-2")),
            rdflib_cuba["_datatypes/VECTOR-2-2"],
        )

    def test_get_data_table_name(self):
        """Test getting the name of a data table from data type."""
        self.assertEqual(
            get_data_table_name(rdflib.XSD.integer), data_tbl("XSD_integer")
        )
        self.assertEqual(
            get_data_table_name(
                rdflib.URIRef("http://www.w3.org/2002/07/owl#rational")
            ),
            data_tbl("OWL_rational"),
        )
        # Replaced rdflib.OWL.rational with URIRef('...'), as it seems to
        # have disappeared in rdflib 6.0.0.
        # TODO: return to original form when a fix for rdflib is available.
        self.assertEqual(
            get_data_table_name(rdflib.RDF.PlainLiteral),
            data_tbl("RDF_PlainLiteral"),
        )
        self.assertEqual(
            get_data_table_name(rdflib.RDFS.Literal), data_tbl("RDFS_Literal")
        )
        self.assertEqual(
            get_data_table_name(rdflib_cuba["_datatypes/VECTOR-2-2"]),
            data_tbl("VECTOR-2-2"),
        )
        self.assertRaises(
            NotImplementedError, get_data_table_name, rdflib.SKOS.prefLabel
        )

    def test_check_characters(self):
        """Test character check."""
        c1 = EqualsCondition("c", "d", "e", rdflib.XSD.string)
        c2 = EqualsCondition("c;", "d", "e", rdflib.XSD.string)
        c3 = EqualsCondition("c", "d;", "e", rdflib.XSD.string)
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

    def test_get_expanded_cols(self):
        """Test getting the expanded columns."""
        x1 = get_expanded_cols("column", rdflib.XSD.string)
        x2 = get_expanded_cols(COLS[2], DTYPES[COLS[2]])
        self.assertEqual(x1, (["column"], rdflib.XSD.string))
        self.assertEqual(x2, (EXPANDED_COLS[3:], rdflib.XSD.float))

    def test_expand_vector_cols(self):
        """Test the expand_vector_cols method."""
        cols, dtypes, vals = expand_vector_cols(
            columns=COLS, datatypes=DTYPES, values=VALS
        )
        self.assertEqual(cols, EXPANDED_COLS)
        self.assertEqual(dtypes, EXPANDED_DTYPES)
        self.assertEqual(vals, EXPANDED_VALS)

    def test_contract_vector_values(self):
        """Test the contract_vector_values method."""
        q = SqlQuery("table", EXPANDED_COLS, EXPANDED_DTYPES)
        r = contract_vector_values([EXPANDED_VALS], q)
        np.testing.assert_equal(next(r), VALS)

    def test_expand_vector_condition(self):
        """Test expanding a condition on a vector."""
        pass


if __name__ == "__main__":
    unittest.main()
