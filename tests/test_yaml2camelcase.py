"""Test cases for the Yaml2CamelCase tool."""

import yaml
import tempfile
import unittest
from pathlib import Path
from osp.core.tools.yaml2camelcase import Yaml2CamelCaseConverter

caps = Path(__file__).parent / "city_caps.ontology.yml"
camel = Path(__file__).parents[1] / "osp" / "core" / "ontology" / "files" \
    / "city.ontology.yml"


class TestYaml2CamelCase(unittest.TestCase):
    """Test the Yaml2CamelCase tool."""

    def setUp(self):
        """Set up the tests."""
        self.maxDiff = None
        with open(caps) as f:
            self.caps_doc = yaml.safe_load(f)

        with open(camel) as f:
            self.camel_doc = yaml.safe_load(f)

    def test_convert(self):
        """Test the convert method."""
        converter = Yaml2CamelCaseConverter(caps)
        converter.convert()
        with tempfile.NamedTemporaryFile("wt") as f:
            f.close()
            converter.store(f.name)

            with open(f.name, "rt") as f2:
                self.assertEqual(self.camel_doc, yaml.safe_load(f2))


if __name__ == "__main__":
    unittest.main()
