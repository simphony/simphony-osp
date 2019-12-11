# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import numpy as np
from osp.core.session.db.sql_wrapper_session import \
    SqlWrapperSession

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")

EXPANDED_COLS = ['1',
                 '2___0', '2___1',
                 '3___0', '3___1', '3___2',
                 '3___3', '3___4', '3___5']
EXPANDED_DTYPES = {'1': 'INT', '2': 'VECTOR:2',
                   '2___0': 'FLOAT', '2___1': 'FLOAT',
                   '3': 'VECTOR:2:3',
                   '3___0': 'FLOAT', '3___1': 'FLOAT',
                   '3___2': 'FLOAT', '3___3': 'FLOAT',
                   '3___4': 'FLOAT', '3___5': 'FLOAT'}
EXPANDED_VALS = [100, 1, 2, 1, 2, 3, 2, 3, 4]
VALS = [100, np.array([1, 2]), np.array([[1, 2, 3], [2, 3, 4]])]


class TestSqliteCity(unittest.TestCase):

    def test_expand_vector_cols(self):
        cols, dtypes, vals = SqlWrapperSession._expand_vector_cols(
            columns=["1", "2", "3"],
            datatypes={"1": "INT", "2": "VECTOR:2", "3": "VECTOR:2:3"},
            values=VALS
        )
        self.assertEqual(cols, EXPANDED_COLS)
        self.assertEqual(dtypes, EXPANDED_DTYPES)
        self.assertEqual(vals, EXPANDED_VALS)

    def test_contract_vector_values(self):
        r = SqlWrapperSession._contract_vector_values(EXPANDED_COLS,
                                                      EXPANDED_DTYPES,
                                                      [EXPANDED_VALS])
        np.testing.assert_equal(next(r), VALS)
