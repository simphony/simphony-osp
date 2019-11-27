# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import re
from osp.core.ontology.validator import validate, _validate_format


class TestOntologyValidator(unittest.TestCase):
    def test_validate(self):
        """Test the validate method"""

        # pattern is string
        validate({"VERSION": "0.0.1", "NAMESPACE": "TEST", "ONTOLOGY": {}},
                 pattern="/")
        self.assertRaises(ValueError, validate,
                          {"VERSION": "0.0.1", "NAMESPACE": "TEST"},
                          pattern="/")

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
        """Test the validate_format method"""

        # format is a dict
        regex = re.compile("^([A-Z][a-z0-9]+)+$")
        regex2 = re.compile("^[a-z]+(_[a-z0-9]+)*$")
        _validate_format({"a": "MyTest", "b": "MyAwesomeTest"},
                         {"a": regex, "!b": regex}, context="/")
        _validate_format({"b": "MyAwesomeTest"},
                         {"a": regex, "!b": regex}, context="/")
        self.assertRaises(ValueError, _validate_format, {"a": "MyTest"},
                          {"a": regex, "!b": regex}, context="/")
        self.assertRaises(ValueError, _validate_format,
                          {"a": "MyTest", "b": "MyAwesomeTest", "c": "Test"},
                          {"a": regex, "!b": regex}, context="/")

        # format is a list
        _validate_format("MyTest", [regex, regex2], context="/")
        _validate_format("my_test", [regex, regex2], context="/")
        self.assertRaises(ValueError, _validate_format,
                          "My_Test", [regex, regex2], context="/")
