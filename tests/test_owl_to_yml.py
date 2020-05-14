import os
import io
import unittest2 as unittest
from osp.core.tools.owl2yml import OwlToYmlConverter


class TestOwlToYml(unittest.TestCase):
    def test_owl_to_yml(self):
        c = OwlToYmlConverter(
            os.path.join(os.path.dirname(__file__), "test_owl_to_yml.owl"),
            os.path.join(os.path.dirname(__file__), "test_owl_to_yml.co.yml"),
            "TEST", "0.0.1"
        )
        c.convert()
        r = io.StringIO()
        c.write(file=r)

        self.maxDiff = None
        with open(
            os.path.join(os.path.dirname(__file__),
                         "test_owl_to_yml.yml"), "r"
        ) as f:
            self.assertEqual(r.getvalue(), "".join(list(f)))
