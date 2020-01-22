# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
from osp.core.session.core_session import CoreSession
from osp.core.session.result import QueryResult, ResultEmptyError, \
    MultipleResultsError


class TestQueryResult(unittest.TestCase):

    def test_all(self):
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertEqual(r.all(), list(range(10)))
        self.assertEqual(r.all(), list(range(10)))
        r = QueryResult(CoreSession(), iter(range(10)))
        next(r)
        self.assertEqual(r.all(), list(range(10)))
        self.assertEqual(r.all(), list(range(10)))

    def test_iter(self):
        r = QueryResult(CoreSession(), iter(range(10)))
        i = iter(r)
        self.assertEqual(list(zip(i, range(5))),
                         list(zip(range(5), range(5))))
        self.assertEqual(list(zip(i, range(5))),
                         list(zip(range(6, 10), range(5))))
        self.assertEqual(r.all(), list(range(10)))

    def test_first(self):
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertEqual(r.first(), 0)
        self.assertEqual(r.first(), 0)
        self.assertEqual(r.all(), list(range(10)))
        r = QueryResult(CoreSession(), iter(range(0)))
        self.assertEqual(r.first(), None)
        self.assertEqual(r.first(), None)
        self.assertEqual(r.all(), list(range(0)))

    def test_one(self):
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertRaises(MultipleResultsError, r.one)
        self.assertRaises(MultipleResultsError, r.one)
        self.assertEqual(r.all(), list(range(10)))
        r = QueryResult(CoreSession(), iter(range(2)))
        next(r)
        self.assertRaises(MultipleResultsError, r.one)
        self.assertRaises(MultipleResultsError, r.one)
        self.assertEqual(r.all(), list(range(2)))
        r = QueryResult(CoreSession(), iter(range(0)))
        self.assertRaises(ResultEmptyError, r.one)
        self.assertRaises(ResultEmptyError, r.one)
        self.assertEqual(r.all(), list(range(0)))

    def test_next(self):
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertEqual(0, next(r))
        self.assertEqual(1, next(r))
        self.assertEqual(2, next(r))
        self.assertEqual(r.all(), list(range(10)))
        self.assertRaises(StopIteration, next, r)

    def test_contains(self):
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertIn(1, r)
        self.assertIn(9, r)
        self.assertNotIn(11, r)
