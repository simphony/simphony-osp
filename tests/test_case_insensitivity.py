import unittest2 as unittest
from osp.core.ontology.yml.case_insensitivity import \
    get_case_insensitive_alternative as alt


class TestAPICity(unittest.TestCase):

    def setUp(self):
        pass

    def test_get_case_insensitive_alternative(self):
        self.assertIsNone(alt("activeRelationship", True))
        self.assertEqual(alt("ActiveRelationship", True), "activeRelationship")
        self.assertEqual(alt("ACTIVE_RELATIONSHIP", True),
                         "activeRelationship")
        self.assertEqual(alt("active_relationship", True),
                         "activeRelationship")

        self.assertEqual(alt("wrapper", True), "Wrapper")
        self.assertIsNone(alt("Wrapper", True))
        self.assertEqual(alt("WRAPPER", True), "Wrapper")

        self.assertEqual(alt("someEntity", False), "SOME_ENTITY")
        self.assertEqual(alt("SomeEntity", False), "SOME_ENTITY")
        self.assertEqual(alt("some_entity", False), "SOME_ENTITY")
        self.assertEqual(alt("SOME_ENTITY", False), "SOME_ENTITY")


if __name__ == "__main__":
    unittest.main()
