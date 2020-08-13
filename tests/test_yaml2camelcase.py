import unittest2 as unittest
import yaml
import tempfile
from pathlib import Path

from osp.core.tools.yaml2camelcase import Yaml2CamelCaseConverter

caps = Path(__file__).parent / "city_caps.ontology.yml"
camel = Path(__file__).parents[1] / "osp" / "core" / "ontology" / "docs" \
    / "city.ontology.yml"


class TestYaml2CamelCase(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        with open(caps) as f:
            self.caps_doc = yaml.safe_load(f)

        with open(camel) as f:
            self.camel_doc = yaml.safe_load(f)

    def test_convert(self):
        converter = Yaml2CamelCaseConverter(caps)
        converter.convert()
        with tempfile.NamedTemporaryFile("wt") as f:
            converter.store(f.name)

            with open(f.name, "rt") as f2:
                self.assertEqual(self.camel_doc, yaml.safe_load(f2))


if __name__ == "__main__":
    unittest.main()
