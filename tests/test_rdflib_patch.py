"""Tests the patch  applied to RDFLib <= 5.0.0 in `osp/__init__.py`.

See osp-core issue https://github.com/simphony/osp-core/issues/558 (the drive
letter from the path is stripped on Windows by the graph.Graph.serialize method
of RDFLib <= 5.0.0).
"""

import unittest
from osp import _compare_version_leq as compare_version_leq


class TestRDFLibPatch(unittest.TestCase):
    """Test the RDFLib patch."""

    def test_version_comparison(self):
        """Test the version comparison function for a few version strings."""
        test_version_pairs = (('0.0.1', '0.0.1', True),
                              ('0.0.1', '0.0.1.0', True),
                              ('0.0.1.0', '0.0.1', True),
                              ('0.0.1', '0.0.1.0.0.0.19.0.23', True),
                              ('0.0.1.0.0.0.19.0.23', '0.0.1', False),
                              ('0.0.1', '0.0.5', True),
                              ('0.1', '0.0.5', False),
                              ('0.20', '5.1', True),
                              )

        for version, other_version, expected_result in test_version_pairs:
            with self.subTest(msg="Testing version {version} <= "
                                  "{other_version}"
                                  .format(version=version,
                                          other_version=other_version)):
                self.assertIs(compare_version_leq(version, other_version),
                              expected_result)


if __name__ == "__main__":
    unittest.main()
