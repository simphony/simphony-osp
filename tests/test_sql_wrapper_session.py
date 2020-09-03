# """Test the abstract SqlWrapper session."""

# import unittest2 as unittest
# import numpy as np
# import rdflib
# from osp.core.ontology.cuba import rdflib_cuba
# from osp.core.session.db.sql_wrapper_session import \
#     SqlWrapperSession

# EXPANDED_COLS = ['1',
#                  '2___0', '2___1',
#                  '3___0', '3___1', '3___2',
#                  '3___3', '3___4', '3___5']
# EXPANDED_DTYPES = {'1': rdflib.XSD.integer,
#                    '2': rdflib_cuba["_datatypes/VECTOR-2"],
#                    '2___0': rdflib.XSD.float, '2___1': rdflib.XSD.float,
#                    '3': rdflib_cuba["_datatypes/VECTOR-2-3"],
#                    '3___0': rdflib.XSD.float, '3___1': rdflib.XSD.float,
#                    '3___2': rdflib.XSD.float, '3___3': rdflib.XSD.float,
#                    '3___4': rdflib.XSD.float, '3___5': rdflib.XSD.float}
# EXPANDED_VALS = [100, 1, 2, 1, 2, 3, 2, 3, 4]
# VALS = [100, np.array([1, 2]), np.array([[1, 2, 3], [2, 3, 4]])]


# class TestSqliteCity(unittest.TestCase):
#     """Test the sqlite wrapper with the City ontology."""

#     def test_expand_vector_cols(self):
#         """Test the expand_vector_cols method."""
#         cols, dtypes, vals = SqlWrapperSession._expand_vector_cols(
#             columns=["1", "2", "3"],
#             datatypes={"1": rdflib.XSD.integer,
#                        "2": rdflib_cuba["_datatypes/VECTOR-2"],
#                        "3": rdflib_cuba["_datatypes/VECTOR-2-3"]},
#             values=VALS
#         )
#         self.assertEqual(cols, EXPANDED_COLS)
#         self.assertEqual(dtypes, EXPANDED_DTYPES)
#         self.assertEqual(vals, EXPANDED_VALS)

#     def test_contract_vector_values(self):
#         """Test the contract_vector_values method."""
#         r = SqlWrapperSession._contract_vector_values(EXPANDED_COLS,
#                                                       EXPANDED_DTYPES,
#                                                       [EXPANDED_VALS])
#         np.testing.assert_equal(next(r), VALS)


# if __name__ == '__main__':
#     unittest.main()
