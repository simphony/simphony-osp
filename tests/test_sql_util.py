"""Test the abstract SqlWrapper session."""

import unittest2 as unittest
import numpy as np
import rdflib
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.session.db.sql_util import (
    expand_vector_cols,
    contract_vector_values, SqlQuery, EqualsCondition, JoinCondition,
    AndCondition, determine_datatype, get_data_table_name
)

COLS = ['1', '2', '3']
DTYPES = {"1": rdflib.XSD.integer,
          "2": rdflib_cuba["_datatypes/VECTOR-2"],
          "3": rdflib_cuba["_datatypes/VECTOR-2-3"]}
VALS = [100, np.array([1, 2]), np.array([[1, 2, 3], [2, 3, 4]])]
EXPANDED_COLS = ['1',
                 '2___0', '2___1',
                 '3___0', '3___1', '3___2',
                 '3___3', '3___4', '3___5']
EXPANDED_DTYPES = {'1': rdflib.XSD.integer,
                   '2': rdflib_cuba["_datatypes/VECTOR-2"],
                   '2___0': rdflib.XSD.float, '2___1': rdflib.XSD.float,
                   '3': rdflib_cuba["_datatypes/VECTOR-2-3"],
                   '3___0': rdflib.XSD.float, '3___1': rdflib.XSD.float,
                   '3___2': rdflib.XSD.float, '3___3': rdflib.XSD.float,
                   '3___4': rdflib.XSD.float, '3___5': rdflib.XSD.float}
EXPANDED_VALS = [100, 1, 2, 1, 2, 3, 2, 3, 4]


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
        c21 = EqualsCondition("my_table", "2___0",
                              VALS[1][0], EXPANDED_DTYPES["2___0"])
        c22 = EqualsCondition("my_table", "2___1",
                              VALS[1][1], EXPANDED_DTYPES["2___1"])
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
        self.assertEqual(q._columns, {"alias": EXPANDED_COLS,
                                      "alias2": EXPANDED_COLS})
        self.assertEqual(q.datatypes, {"alias": EXPANDED_DTYPES,
                                       "alias2": EXPANDED_DTYPES})
        self.assertEqual(q.condition, AndCondition(c1))
        q.where(c4)
        self.assertEqual(q.condition, AndCondition(c1, c4))

    def test_determine_datatype(self):
        """Test determining the datatype of a table."""
        self.assertEqual(determine_datatype("DATA_XSD_integer"),
                         rdflib.XSD.integer)
        self.assertEqual(determine_datatype("DATA_OWL_rational"),
                         rdflib.OWL.rational)
        self.assertEqual(determine_datatype("DATA_RDF_PlainLiteral"),
                         rdflib.RDF.PlainLiteral)
        self.assertEqual(determine_datatype("DATA_RDFS_Literal"),
                         rdflib.RDFS.Literal)
        self.assertEqual(determine_datatype("DATA_VECTOR-2-2"),
                         rdflib_cuba["_datatypes/VECTOR-2-2"])

    def test_get_data_table_name(self):
        """Test getting the name of a data table from data type."""
        self.assertEqual(get_data_table_name(rdflib.XSD.integer),
                         "DATA_XSD_integer")
        self.assertEqual(get_data_table_name(rdflib.OWL.rational),
                         "DATA_OWL_rational")
        self.assertEqual(get_data_table_name(rdflib.RDF.PlainLiteral),
                         "DATA_RDF_PlainLiteral")
        self.assertEqual(get_data_table_name(rdflib.RDFS.Literal),
                         "DATA_RDFS_Literal")
        self.assertEqual(
            get_data_table_name(rdflib_cuba["_datatypes/VECTOR-2-2"]),
            "DATA_VECTOR-2-2"
        )

    def test_check_characters(self):
        """Test character check."""

    def test_get_expanded_cols(self):
        """Test getting the expanded columns."""

    def test_handle_vector_item(self):
        """Test handling an element of a vector in a query result row."""

    def test_expand_vector_cols(self):
        """Test the expand_vector_cols method."""
        cols, dtypes, vals = expand_vector_cols(
            columns=COLS,
            datatypes=DTYPES,
            values=VALS
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


if __name__ == '__main__':
    unittest.main()
