# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import unittest2 as unittest
from cuds.ontology.parser import Parser


class TestRegistryCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_parser(self):
        parser = Parser()
        path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(path, "..", "ontology", "ontology.city.yml")
        parser.parse(path)


if __name__ == '__main__':
    unittest.main()
