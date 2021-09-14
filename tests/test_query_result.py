"""This file contains tests for the QueryResult class."""

import unittest2 as unittest
from osp.core.session.interfaces.core_session import CoreSession
from osp.core.session.result import QueryResult, ResultEmptyError, \
    MultipleResultsError


class TestQueryResult(unittest.TestCase):
    """This class contains tests for the QueryResult class."""

    def test_all(self):
        """Test the all() method."""
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertEqual(r.all(), list(range(10)))
        self.assertEqual(r.all(), list(range(10)))
        r = QueryResult(CoreSession(), iter(range(10)))
        next(r)
        self.assertEqual(r.all(), list(range(10)))
        self.assertEqual(r.all(), list(range(10)))

    def test_iter(self):
        """Test the __iter__() magic method."""
        r = QueryResult(CoreSession(), iter(range(10)))
        i = iter(r)
        self.assertEqual(list(zip(i, range(5))),
                         list(zip(range(5), range(5))))
        self.assertEqual(list(zip(i, range(5))),
                         list(zip(range(6, 10), range(5))))
        self.assertEqual(r.all(), list(range(10)))

    def test_first(self):
        """Test the first() method."""
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertEqual(r.first(), 0)
        self.assertEqual(r.first(), 0)
        self.assertEqual(r.all(), list(range(10)))
        r = QueryResult(CoreSession(), iter(range(0)))
        self.assertEqual(r.first(), None)
        self.assertEqual(r.first(), None)
        self.assertEqual(r.all(), list(range(0)))

    def test_one(self):
        """Test the one() method."""
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
        """Test __next__ magic method."""
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertEqual(0, next(r))
        self.assertEqual(1, next(r))
        self.assertEqual(2, next(r))
        self.assertEqual(r.all(), list(range(10)))
        self.assertRaises(StopIteration, next, r)

    def test_contains(self):
        """Test containment."""
        r = QueryResult(CoreSession(), iter(range(10)))
        self.assertIn(1, r)
        self.assertIn(9, r)
        self.assertNotIn(11, r)
