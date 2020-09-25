"""Test the abstract SqlWrapper session."""

import unittest2 as unittest


class TestSqlWrapperSession(unittest.TestCase):
    """Test helper method of the Sql Wrapper."""

    def test_queries(self):
        """Test computing the queries corresponding to a triple pattern."""

    def test_queries_for_subject(self):
        """Test computing queries to get all triples with given subject."""

    def test_construct_remove_condition(self):
        """Test construction a remove condition."""

    def test_rows_to_triples(self):
        """Test transforming sql table rows to triples."""

    def test_get_ns_idx(self):
        """Test getting the namespace index from namespace."""

    def test_split_namespace(self):
        """Test splitting am iri to namespace index and suffix."""

    def test_get_conditions(self):
        """Test getting the conditions for a query."""

    def test_construct_query(self):
        """Test construction a query."""

    def test_determine_table(self):
        """Test determining the table to look for data."""


if __name__ == '__main__':
    unittest.main()
