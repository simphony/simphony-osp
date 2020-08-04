import os
import unittest2 as unittest
import tempfile
import rdflib
from rdflib.compare import isomorphic
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.namespace_registry import NamespaceRegistry
from osp.core.ontology.installation import OntologyInstallationManager
from osp.core.ontology import OntologyClass, OntologyRelationship, \
    OntologyAttribute

CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")
RDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.ttl")


class TestNamespaces(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.namespace_registry = NamespaceRegistry()
        self.namespace_registry._load_cuba()
        self.installer = OntologyInstallationManager(
            namespace_registry=self.namespace_registry,
            path=self.tempdir.name
        )
        self.graph = self.namespace_registry._graph

    def tearDown(self):
        self.tempdir.cleanup()

    def test_namespace_registry_load_cuba(self):
        g = rdflib.Graph()
        g.parse(CUBA_FILE, format="ttl")
        self.assertTrue(isomorphic(g, self.graph))
        self.assertIn("cuba", self.namespace_registry._namespaces)
        self.assertEqual(self.namespace_registry._namespaces["cuba"],
                         rdflib.URIRef("http://www.osp-core.com/cuba#"))

    def test_namespace_registry_store(self):
        self.graph.parse(RDF_FILE, format="ttl")
        self.graph.bind("parser_test",
                        rdflib.URIRef("http://www.osp-core.com/parser_test#"))
        self.namespace_registry.update_namespaces()
        self.namespace_registry.store(self.tempdir.name)
        self.assertEqual(os.listdir(self.tempdir.name), ["graph.xml",
                                                         "namespaces.txt"])
        g = rdflib.Graph()
        g.parse(os.path.join(self.tempdir.name, "graph.xml"), format="xml")
        g1 = rdflib.Graph()
        g1.parse(CUBA_FILE, format="ttl")
        g1.parse(RDF_FILE, format="ttl")
        self.assertTrue(isomorphic(g, g1))

        with open(os.path.join(self.tempdir.name, "namespaces.txt")) as f:
            lines = set(map(lambda x: x.strip(), f))
            self.assertIn("cuba\thttp://www.osp-core.com/cuba#", lines)
            self.assertIn("parser_test\thttp://www.osp-core.com/parser_test#",
                          lines)

    def test_namespace_registry_load(self):
        # no graph.xml found
        self.namespace_registry.clear()
        self.namespace_registry.load(self.tempdir.name)
        g = rdflib.Graph()
        g.parse(CUBA_FILE, format="ttl")
        self.assertTrue(isomorphic(g, self.namespace_registry._graph))
        self.namespace_registry.clear()
        self.graph = self.namespace_registry._graph

        # graph.ttl found
        self.graph.parse(RDF_FILE, format="ttl")
        self.graph.bind("parser_test",
                        rdflib.URIRef("http://www.osp-core.com/parser_test#"))
        self.namespace_registry.update_namespaces()
        self.namespace_registry.store(self.tempdir.name)

        nr = NamespaceRegistry()
        nr.load(self.tempdir.name)
        self.assertTrue(isomorphic(nr._graph, self.graph))
        self.assertIn("parser_test", nr)

    def test_namespace_registry_clear(self):
        self.namespace_registry.clear()
        self.assertIsNot(self.namespace_registry._graph, self.graph)
        self.assertTrue(isomorphic(self.namespace_registry._graph, self.graph))

    def test_namespace_registry_from_iri(self):
        self.installer.install("city")
        ns_iri = rdflib.URIRef("http://www.osp-core.com/city#")
        city_iri = ns_iri + "City"
        hasPart_iri = ns_iri + "hasPart"
        self.modify_labels()

        c = self.namespace_registry.from_iri(rdflib_cuba.Class)
        self.assertIsInstance(c, OntologyClass)
        self.assertEqual(c.namespace.get_name(), "cuba")
        self.assertEqual(c.name, "Class")
        r = self.namespace_registry.from_iri(rdflib_cuba.relationship)
        self.assertIsInstance(r, OntologyRelationship)
        self.assertEqual(r.namespace.get_name(), "cuba")
        self.assertEqual(r.name, "relationship")
        a = self.namespace_registry.from_iri(rdflib_cuba.attribute)
        self.assertIsInstance(a, OntologyAttribute)
        self.assertEqual(a.namespace.get_name(), "cuba")
        self.assertEqual(a.name, "attribute")
        c = self.namespace_registry.from_iri(city_iri)
        self.assertIsInstance(c, OntologyClass)
        self.assertEqual(c.namespace.get_name(), "city")
        self.assertEqual(c.name, "City")
        r = self.namespace_registry.from_iri(hasPart_iri)
        self.assertIsInstance(r, OntologyRelationship)
        self.assertEqual(r.namespace.get_name(), "city")
        self.assertEqual(r.name, "hasPart")
        from osp.core.namespaces import from_iri
        import osp.core.namespaces
        old_ns_reg = osp.core.namespaces._namespace_registry
        try:
            osp.core.namespaces._namespace_registry = self.namespace_registry
            c = from_iri(rdflib_cuba.Class)
            self.assertIsInstance(c, OntologyClass)
            self.assertEqual(c.namespace.get_name(), "cuba")
            self.assertEqual(c.name, "Class")

            self.graph.add((
                ns_iri,
                rdflib_cuba._reference_by_label,
                rdflib.Literal(True)
            ))
            c = self.namespace_registry.from_iri(city_iri)
            self.assertIsInstance(c, OntologyClass)
            self.assertEqual(c.namespace.get_name(), "city")
            self.assertEqual(c.name, "City_T")
            r = self.namespace_registry.from_iri(hasPart_iri)
            self.assertIsInstance(r, OntologyRelationship)
            self.assertEqual(r.namespace.get_name(), "city")
            self.assertEqual(r.name, "hasPart_T")

            # undefined namespace
            self.graph.add((
                rdflib.URIRef("a/b#c"),
                rdflib.RDF.type,
                rdflib.OWL.Class
            ))
            self.graph.add((
                rdflib.URIRef("d/e/f"),
                rdflib.RDF.type,
                rdflib.OWL.Class
            ))
            a = from_iri("a/b#c")
            b = from_iri("d/e/f")
            self.assertIsInstance(a, OntologyClass)
            self.assertEqual(a.namespace.get_name(), "a/b#")
            self.assertEqual(a.name, "c")
            self.assertIsInstance(b, OntologyClass)
            self.assertEqual(b.namespace.get_name(), "d/e/")
            self.assertEqual(b.name, "f")
        finally:
            osp.core.namespaces._namespace_registry = old_ns_reg

    def test_namespace_registry_update_namespaces(self):
        self.graph.bind("a", rdflib.URIRef("aaa"))
        self.graph.bind("b", rdflib.URIRef("bbb"))
        self.graph.bind("c", rdflib.URIRef("ccc"))
        self.namespace_registry.update_namespaces()
        self.assertEqual(self.namespace_registry.a.get_name(), "a")
        self.assertEqual(self.namespace_registry.a.get_iri(),
                         rdflib.URIRef("aaa"))
        self.assertEqual(self.namespace_registry.b.get_name(), "b")
        self.assertEqual(self.namespace_registry.b.get_iri(),
                         rdflib.URIRef("bbb"))
        self.assertEqual(self.namespace_registry.c.get_name(), "c")
        self.assertEqual(self.namespace_registry.c.get_iri(),
                         rdflib.URIRef("ccc"))

    def test_namespace_registry_get(self):
        self.installer.install("city")
        self.assertIn("city", self.namespace_registry)
        self.assertEqual(self.namespace_registry._get("city").get_name(),
                         "city")
        self.assertEqual(self.namespace_registry.get("city").get_name(),
                         "city")
        self.assertEqual(self.namespace_registry["city"].get_name(),
                         "city")
        self.assertEqual(self.namespace_registry.city.get_name(),
                         "city")
        self.assertRaises(KeyError, self.namespace_registry._get, "invalid")
        self.assertEqual(self.namespace_registry.get("invalid"), None)
        self.assertRaises(KeyError, self.namespace_registry.__getitem__,
                          "invalid")
        self.assertRaises(AttributeError, getattr, self.namespace_registry,
                          "invalid")
        self.assertEqual([x.get_name() for x in self.namespace_registry], [
                         'xml', 'rdf', 'rdfs', 'xsd', 'cuba', 'owl', 'city'])

    def modify_labels(self):
        triples = list()
        for s, p, o in self.graph:
            if (
                s.startswith("http://www.osp-core.com/city#")
                and p == rdflib.RDFS.label
            ):
                triples.append((s, p, rdflib.Literal(f"{o}_T", lang="en")))
            else:
                triples.append((s, p, o))
        self.graph.remove((None, None, None))
        for t in triples:
            self.graph.add(t)

    def test_namespace_get(self):
        self.installer.install("city")
        self.modify_labels()
        namespace = self.namespace_registry.city

        # dot
        self.assertIsInstance(namespace.City, OntologyClass)
        self.assertEqual(namespace.City.name, "City")
        self.assertEqual(namespace.City._iri_suffix, "City")
        self.assertIsInstance(namespace.hasPart, OntologyRelationship)
        self.assertEqual(namespace.hasPart.name, "hasPart")
        self.assertEqual(namespace.hasPart._iri_suffix, "hasPart")
        self.assertIsInstance(namespace.coordinates, OntologyAttribute)
        self.assertEqual(namespace.coordinates.name, "coordinates")
        self.assertEqual(namespace.coordinates._iri_suffix, "coordinates")

        # item
        self.assertIsInstance(namespace["City_T"][0], OntologyClass)
        self.assertEqual(namespace["City_T"][0].name, "City")
        self.assertEqual(namespace["City_T"][0]._iri_suffix, "City")
        self.assertIsInstance(namespace["City_T", "en"][0], OntologyClass)
        self.assertEqual(namespace["City_T", "en"][0].name, "City")
        self.assertEqual(namespace["City_T", "en"][0]._iri_suffix, "City")
        self.assertIsInstance(namespace["hasPart_T"][0], OntologyRelationship)
        self.assertEqual(namespace["hasPart_T"][0].name, "hasPart")
        self.assertEqual(namespace["hasPart_T"][0]._iri_suffix, "hasPart")
        self.assertIsInstance(namespace["coordinates_T"][0], OntologyAttribute)
        self.assertEqual(namespace["coordinates_T"][0].name, "coordinates")
        self.assertEqual(namespace["coordinates_T"][0]._iri_suffix,
                         "coordinates")

        # get
        self.assertIsInstance(namespace.get("City"), OntologyClass)
        self.assertEqual(namespace.get("City").name, "City")
        self.assertEqual(namespace.get("City")._iri_suffix, "City")
        self.assertIsInstance(namespace.get("hasPart"), OntologyRelationship)
        self.assertEqual(namespace.get("hasPart").name, "hasPart")
        self.assertEqual(namespace.get("hasPart")._iri_suffix, "hasPart")
        self.assertIsInstance(namespace.get("coordinates"), OntologyAttribute)
        self.assertEqual(namespace.get("coordinates").name, "coordinates")
        self.assertEqual(namespace.get(
            "coordinates")._iri_suffix, "coordinates")
        self.assertRaises(AttributeError, namespace.__getattr__, "CITY")
        self.assertRaises(KeyError, namespace.__getitem__, "HAS_PART_T")
        self.assertRaises(KeyError, namespace.__getitem__, "HAS_PART")
        self.assertEqual(namespace.get("COORDINATES"), None)

        # reference by label
        namespace._reference_by_label = True
        namespace._label_cache = dict()
        # dot
        self.assertIsInstance(namespace.City_T, OntologyClass)
        self.assertEqual(namespace.City_T.name, "City_T")
        self.assertEqual(namespace.City_T._iri_suffix, "City")
        self.assertIsInstance(namespace.hasPart_T, OntologyRelationship)
        self.assertEqual(namespace.hasPart_T.name, "hasPart_T")
        self.assertEqual(namespace.hasPart_T._iri_suffix, "hasPart")
        self.assertIsInstance(namespace.coordinates_T, OntologyAttribute)
        self.assertEqual(namespace.coordinates_T.name, "coordinates_T")
        self.assertEqual(namespace.coordinates_T._iri_suffix, "coordinates")

        # item
        self.assertIsInstance(namespace["City_T"][0], OntologyClass)
        self.assertEqual(namespace["City_T"][0].name, "City_T")
        self.assertEqual(namespace["City_T"][0]._iri_suffix, "City")
        self.assertIsInstance(namespace["City_T", "en"][0], OntologyClass)
        self.assertEqual(namespace["City_T", "en"][0].name, "City_T")
        self.assertEqual(namespace["City_T", "en"][0]._iri_suffix, "City")
        self.assertIsInstance(namespace["hasPart_T"][0], OntologyRelationship)
        self.assertEqual(namespace["hasPart_T"][0].name, "hasPart_T")
        self.assertEqual(namespace["hasPart_T"][0]._iri_suffix, "hasPart")
        self.assertIsInstance(namespace["coordinates_T"][0], OntologyAttribute)
        self.assertEqual(namespace["coordinates_T"][0].name, "coordinates_T")
        self.assertEqual(namespace["coordinates_T"][0]._iri_suffix,
                         "coordinates")

        # get
        self.assertIsInstance(namespace.get("City_T"), OntologyClass)
        self.assertEqual(namespace.get("City_T").name, "City_T")
        self.assertEqual(namespace.get("City_T")._iri_suffix, "City")
        self.assertIsInstance(namespace.get("hasPart_T"), OntologyRelationship)
        self.assertEqual(namespace.get("hasPart_T").name, "hasPart_T")
        self.assertEqual(namespace.get("hasPart_T")._iri_suffix, "hasPart")
        self.assertIsInstance(namespace.get("coordinates_T"),
                              OntologyAttribute)
        self.assertEqual(namespace.get("coordinates_T").name, "coordinates_T")
        self.assertEqual(namespace.get(
            "coordinates_T")._iri_suffix, "coordinates")
        self.assertRaises(AttributeError, namespace.__getattr__, "CITY")
        self.assertRaises(KeyError, namespace.__getitem__, "HAS_PART_T")
        self.assertRaises(KeyError, namespace.__getitem__, "HAS_PART")
        self.assertEqual(namespace.get("COORDINATES"), None)
        self.assertRaises(AttributeError, namespace.__getattr__, "City")
        self.assertRaises(KeyError, namespace.__getitem__, "City")
        self.assertEqual(namespace.get("coordinates"), None)

    def test_namespace_str(self):
        self.installer.install("city")
        namespace = self.namespace_registry.city
        self.assertEqual(str(namespace),
                         "city (http://www.osp-core.com/city#)")
        self.assertEqual(repr(namespace),
                         "<city: http://www.osp-core.com/city#>")

    def test_get_default_rel(self):
        self.installer.install("city")
        namespace = self.namespace_registry.city
        self.assertEqual(namespace.get_default_rel().name, "hasPart")

    def test_contains(self):
        self.installer.install("city")
        namespace = self.namespace_registry.city
        self.assertIn("City", namespace)
        self.assertIn("hasPart", namespace)


if __name__ == "__main__":
    unittest.main()
