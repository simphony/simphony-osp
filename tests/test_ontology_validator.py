"""Test the ontology validator."""

import re

import unittest2 as unittest

from osp.core.ontology.parser.yml.validator import _validate_format, validate


class TestOntologyValidator(unittest.TestCase):
    """Test the ontology validator."""

    def test_validate(self):
        """Test the validate method."""
        # pattern is string
        validate(
            {"version": "0.0.1", "namespace": "test", "ontology": {}},
            pattern="/",
        )
        self.assertRaises(
            ValueError,
            validate,
            {"version": "0.0.1", "namespace": "test"},
            pattern="/",
        )

        # pattern is regex pattern
        regex = re.compile("^([A-Z][a-z0-9]+)+$")
        validate("MyTest", regex)
        self.assertRaises(ValueError, validate, "MyTEst", regex)

        # pattern is a list
        validate(["MyTest", "MyAwesomeTest"], [regex])
        self.assertRaises(ValueError, validate, "MyTest", [regex])
        self.assertRaises(ValueError, validate, ["MyTEst"], [regex])

        # pattern is a dict
        validate({1: "MyTest", 2: "MyAwesomeTest"}, {int: regex})
        self.assertRaises(ValueError, validate, [1, "MyTest"], {int: regex})
        self.assertRaises(ValueError, validate, {"1": "MyTest"}, {int: regex})
        self.assertRaises(ValueError, validate, {1: "MyTEst"}, {int: regex})

    def test_validate_format(self):
        """Test the validate_format method."""
        # format is a dict
        regex = re.compile("^([A-Z][a-z0-9]+)+$")
        regex2 = re.compile("^[a-z]+(_[a-z0-9]+)*$")
        _validate_format(
            {"a": "MyTest", "b": "MyAwesomeTest"},
            {"a": regex, "!b": regex},
            context="/",
        )
        _validate_format(
            {"b": "MyAwesomeTest"}, {"a": regex, "!b": regex}, context="/"
        )
        self.assertRaises(
            ValueError,
            _validate_format,
            {"a": "MyTest"},
            {"a": regex, "!b": regex},
            context="/",
        )
        self.assertRaises(
            ValueError,
            _validate_format,
            {"a": "MyTest", "b": "MyAwesomeTest", "c": "Test"},
            {"a": regex, "!b": regex},
            context="/",
        )

        # format is a list
        _validate_format("MyTest", [regex, regex2], context="/")
        _validate_format("my_test", [regex, regex2], context="/")
        self.assertRaises(
            ValueError,
            _validate_format,
            "My_Test",
            [regex, regex2],
            context="/",
        )
