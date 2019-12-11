# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import shutil
import unittest2 as unittest
from osp.core.ontology import OntologyInstallationManager
import logging

logger = logging.getLogger("osp.core")
logger.setLevel(logging.CRITICAL)


class TestInstallation(unittest.TestCase):
    def test_init(self):
        oim = OntologyInstallationManager(path=os.path.dirname(__file__))
        self.assertEqual(
            oim.path,
            os.path.join(os.path.dirname(__file__), ".osp_ontologies")
        )
        self.assertEqual(
            oim.yaml_path,
            os.path.join(os.path.dirname(__file__),
                         ".osp_ontologies", "yml")
        )
        self.assertEqual(
            oim.installed_path,
            os.path.join(os.path.dirname(__file__),
                         ".osp_ontologies", "yml", "installed")
        )
        self.assertEqual(
            oim.tmp_path,
            os.path.join(os.path.dirname(__file__),
                         ".osp_ontologies", "yml", str(oim.session_id))
        )
        self.assertEqual(
            oim.pkl_path,
            os.path.join(os.path.dirname(__file__),
                         ".osp_ontologies", "ontology.pkl")
        )

    def test_tmp_open(self):
        """Check of ontology file is moved to temporary dir"""
        oim = OntologyInstallationManager(path=os.path.dirname(__file__))
        city_path = os.path.join(
            os.path.dirname(__file__),
            "..", "osp", "core", "ontology", "yml",
            "ontology.city.yml"
        )
        oim._create_directories()
        oim.tmp_open(city_path)
        try:
            f1 = open(city_path, "r")
            self.assertEqual(  # check if file has been moved
                os.listdir(oim.tmp_path),
                ["ontology.city.yml"]
            )  # check contents of the file
            f2 = open(os.path.join(oim.tmp_path, "ontology.city.yml"), "r")
            num_lines = 0
            for l1, l2 in zip(f1, f2):
                self.assertEqual(l1, l2)
                num_lines += 1
            self.assertEqual(num_lines, 258)
        finally:
            shutil.rmtree(oim.path)
            f1.close()
            f2.close()

    def test_sort_for_installation(self):
        """Check if sort for installation works"""
        oim = OntologyInstallationManager(path=os.path.dirname(__file__))
        oim.namespace_registry = set()
        self.assertEqual(
            oim._sort_for_installation(["city"]),
            ["cuba", "city"]
        )

        self.assertEqual(
            oim._sort_for_installation(["city", "parser_test"]),
            ["cuba", "city", "parser_test"]
        )

        self.assertRaises(RuntimeError,
                          oim._sort_for_installation, ["parser_test"])

        self.assertEqual(
            oim._sort_for_installation(["parser_test", "city", "cuba"]),
            ["cuba", "city", "parser_test"]
        )

        self.assertEqual(
            oim._sort_for_installation(["city", "parser_test"]),
            ["cuba", "city", "parser_test"]
        )

        oim.namespace_registry = set(["cuba"])
        self.assertEqual(
            oim._sort_for_installation(["city"]),
            ["city"]
        )

        oim.namespace_registry = set(["cuba", "city"])
        self.assertEqual(
            oim._sort_for_installation(["city", "cuba", "parser_test"]),
            ["parser_test"]
        )

        oim.namespace_registry = set(["cuba", "city"])
        self.assertEqual(
            oim._sort_for_installation(["parser_test"]),
            ["parser_test"]
        )

    def test_get_namespace(self):
        """Get the namespace of a file"""
        self.assertEqual(
            OntologyInstallationManager._get_namespace("city"), "city"
        )
        self.assertEqual(
            OntologyInstallationManager._get_namespace("parser_test"),
            "parser_test"
        )
        self.assertEqual(
            OntologyInstallationManager._get_namespace("cuba"), "cuba"
        )
