"""Test namespace registry and namespaces."""

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
from osp.core.namespaces import cuba

CUBA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "osp", "core", "ontology", "docs", "cuba.ttl")
RDF_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "parser_test.ttl")


class TestNamespaces(unittest.TestCase):
    """Test namespace registry and namespaces."""

    def setUp(self):
        """Set up some temporary directories."""
        self.tempdir = tempfile.TemporaryDirectory()
        self.namespace_registry = NamespaceRegistry()
        self.namespace_registry._load_cuba()
        self.installer = OntologyInstallationManager(
            namespace_registry=self.namespace_registry,
            path=self.tempdir.name
        )
        self.graph = self.namespace_registry._graph

    def tearDown(self):
        """Clean up all temporary directories."""
        self.tempdir.cleanup()

    def test_namespace_registry_load_cuba(self):
        """Test loading the CUBA namespace."""
        g = rdflib.Graph()
        g.parse(CUBA_FILE, format="ttl")
        self.assertTrue(isomorphic(g, self.graph))
        self.assertIn("cuba", self.namespace_registry._namespaces)
        self.assertEqual(self.namespace_registry._namespaces["cuba"],
                         rdflib.URIRef("http://www.osp-core.com/cuba#"))

    def test_namespace_registry_store(self):
        """Test storing loaded namespaces."""
        self.graph.parse(RDF_FILE, format="ttl")
        self.graph.bind("parser_test",
                        rdflib.URIRef("http://www.osp-core.com/parser_test#"))
        self.namespace_registry.bind("parser_test",
                                     rdflib.URIRef("http://www.osp-core.com"
                                                   "/parser_test#"))
        self.namespace_registry.update_namespaces()
        self.namespace_registry.store(self.tempdir.name)
        self.assertItemsEqual(os.listdir(self.tempdir.name),
                              ["graph.xml", "namespaces.txt"])
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
        """Test loading an installed namespaces."""
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
        self.namespace_registry.bind("parser_test",
                                     rdflib.URIRef("http://www.osp-core.com/"
                                                   "parser_test#"))
        self.namespace_registry.update_namespaces()
        self.namespace_registry.store(self.tempdir.name)

        nr = NamespaceRegistry()
        nr.load(self.tempdir.name)
        self.assertTrue(isomorphic(nr._graph, self.graph))
        self.assertIn("parser_test", nr)

    def test_namespace_registry_clear(self):
        """Test clearing a namespace registry."""
        self.namespace_registry.clear()
        self.assertIsNot(self.namespace_registry._graph, self.graph)
        self.assertTrue(isomorphic(self.namespace_registry._graph, self.graph))

    def test_namespace_registry_from_iri(self):
        """Test getting namespaces from iri."""
        self.installer.install("city")
        ns_iri = rdflib.URIRef("http://www.osp-core.com/city#")
        city_iri = ns_iri + "City"
        hasPart_iri = ns_iri + "hasPart"
        self.modify_labels()

        c = self.namespace_registry.from_iri(rdflib_cuba.Entity)
        self.assertIsInstance(c, OntologyClass)
        self.assertEqual(c.namespace.get_name(), "cuba")
        self.assertEqual(c.name, "Entity")
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
        import osp.core.namespaces
        old_ns_reg = osp.core.ontology.namespace_registry.namespace_registry
        try:
            osp.core.ontology.namespace_registry.namespace_registry = \
                self.namespace_registry
            osp.core.namespaces.from_iri = self.namespace_registry.from_iri

            from osp.core.namespaces import from_iri
            c = from_iri(rdflib_cuba.Entity)
            self.assertIsInstance(c, OntologyClass)
            self.assertEqual(c.namespace.get_name(), "cuba")
            self.assertEqual(c.name, "Entity")

            self.graph.add((
                ns_iri,
                rdflib_cuba._reference_by_label,
                rdflib.Literal(True)
            ))
            self.namespace_registry.from_iri.cache_clear()
            c = from_iri(city_iri)
            self.assertIsInstance(c, OntologyClass)
            self.assertEqual(c.namespace.get_name(), "city")
            self.assertEqual(c.name, "City_T")
            r = from_iri(hasPart_iri)
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
            osp.core.ontology.namespace_registry = old_ns_reg
            osp.core.namespaces.from_iri = old_ns_reg.from_iri

    def test_namespace_registry_update_namespaces(self):
        """Test updateing the namespaces."""
        self.graph.bind("a", rdflib.URIRef("aaa"))
        self.namespace_registry.bind("a", rdflib.URIRef("aaa"))
        self.graph.bind("b", rdflib.URIRef("bbb"))
        self.namespace_registry.bind("b", rdflib.URIRef("bbb"))
        self.graph.bind("c", rdflib.URIRef("ccc"))
        self.namespace_registry.bind("c", rdflib.URIRef("ccc"))
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
        """Test getting namsepaces from namespace registry."""
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
        self.assertEqual({x.get_name() for x in self.namespace_registry}, {
                         'cuba', 'city'})

    def modify_labels(self):
        """Modify the labels in the graph. Append a T.

        Helper method.
        """
        namespace = self.namespace_registry.city
        triples = list()
        for s, p, o in self.graph:
            if s in namespace and p in (rdflib.SKOS.prefLabel,
                                        rdflib.RDFS.label):
                # To test querying by label.
                label_SKOS = f"{o}_T"
                triples.append((s, rdflib.SKOS.prefLabel,
                                rdflib.Literal(label_SKOS, lang='en')))
                # To test RDFS labels and special characters.
                label_RDFS = f"{o}-$"
                triples.append((s, rdflib.RDFS.label,
                                rdflib.Literal(label_RDFS, lang='en')))
                # To test non-english languages.
                label_RDFS_jp = f"{o}_T_jp"
                triples.append((s, rdflib.RDFS.label,
                                rdflib.Literal(label_RDFS_jp, lang='jp')))
                label_SKOS_aa = f"{o}_T_aa_SKOS"
                triples.append((s, rdflib.SKOS.prefLabel,
                                rdflib.Literal(label_SKOS_aa, lang='aa')))
                # To test undefined languages.
                label_RDFS_unk = f"{o}_T_unknown_lang"
                triples.append((s, rdflib.RDFS.label,
                                rdflib.Literal(label_RDFS_unk)))
                # To test labels that coincide in different languages.
                label_RDFS_es = f"{o}_T_cosa"
                label_RDFS_it = f"{o}_T_cosa"
                for label, lang in ((label_RDFS_es, 'es'),
                                    (label_RDFS_it, 'it')):
                    triples.append((s, rdflib.RDFS.label,
                                    rdflib.Literal(label, lang=lang)))
            else:
                triples.append((s, p, o))
        # Test different concepts with same label, and querying by language.
        triples.append((rdflib.URIRef(str(namespace._iri) + 'City'),
                        rdflib.RDFS.label, rdflib.Literal('Burro', lang='it')))
        triples.append((rdflib.URIRef(str(namespace._iri) + 'Street'),
                        rdflib.RDFS.label, rdflib.Literal('Burro', lang='es')))
        self.graph.remove((None, None, None))
        for t in triples:
            self.graph.add(t)

    def test_namespace_get(self):
        """Test getting entities from namespace."""
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
        self.assertIsInstance(namespace["City_T"], OntologyClass)
        self.assertEqual(namespace["City_T"].name, "City")
        self.assertEqual(namespace["City_T"]._iri_suffix, "City")
        self.assertIsInstance(namespace["City_T", "en"], OntologyClass)
        self.assertEqual(namespace["City_T", "en"].name, "City")
        self.assertEqual(namespace["City_T", "en"]._iri_suffix, "City")
        self.assertIsInstance(namespace["hasPart_T"], OntologyRelationship)
        self.assertEqual(namespace["hasPart_T"].name, "hasPart")
        self.assertEqual(namespace["hasPart_T"]._iri_suffix, "hasPart")
        self.assertIsInstance(namespace["coordinates_T"], OntologyAttribute)
        self.assertEqual(namespace["coordinates_T"].name, "coordinates")
        self.assertEqual(namespace["coordinates_T"]._iri_suffix,
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
        self.assertIsInstance(namespace["City_T"], OntologyClass)
        self.assertEqual(namespace["City_T"].name, "City_T")
        self.assertEqual(namespace["City_T"]._iri_suffix, "City")
        self.assertIsInstance(namespace["City_T", "en"], OntologyClass)
        self.assertEqual(namespace["City_T", "en"].name, "City_T")
        self.assertEqual(namespace["City_T", "en"]._iri_suffix, "City")
        self.assertIsInstance(namespace["hasPart_T"], OntologyRelationship)
        self.assertEqual(namespace["hasPart_T"].name, "hasPart_T")
        self.assertEqual(namespace["hasPart_T"]._iri_suffix, "hasPart")
        self.assertIsInstance(namespace["coordinates_T"], OntologyAttribute)
        self.assertEqual(namespace["coordinates_T"].name, "coordinates_T")
        self.assertEqual(namespace["coordinates_T"]._iri_suffix,
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

        # Special characters and RDFS labels.
        # RDFS label (special characters)
        self.assertIsInstance(getattr(namespace, 'City-$'), OntologyClass)
        self.assertEqual(getattr(namespace, 'City-$').name, "City-$")
        self.assertEqual(getattr(namespace, 'City-$')._iri_suffix, "City")

        # Language.
        # Refer to the label in non-english language.
        self.assertIsInstance(namespace.City_T_jp, OntologyClass)
        self.assertEqual(namespace.City_T_jp.name, "City_T_jp")
        self.assertEqual(namespace.City_T._iri_suffix, "City")
        # Labels with unknown languages.
        self.assertEqual(namespace['City_T_unknown_lang'].name,
                         'City_T_unknown_lang')
        # Coincident label in different languages.
        self.assertIsInstance(namespace.City_T_cosa, OntologyClass)
        self.assertEqual(namespace.City_T_cosa.name, "City_T_cosa")
        self.assertEqual(namespace.City_T._iri_suffix, "City")
        # Different concepts with the same label.
        self.assertRaises(AttributeError, namespace.__getattr__, 'Burro')
        # Same word with different concept in different languages.
        self.assertEqual(namespace['Burro', 'it'], namespace.City_T)
        self.assertEqual(namespace['Burro', 'es'], namespace.Street_T)

    def test_namespace_str(self):
        """Test converting namespace object to string."""
        self.installer.install("city")
        namespace = self.namespace_registry.city
        self.assertEqual(str(namespace),
                         "city (http://www.osp-core.com/city#)")
        self.assertEqual(repr(namespace),
                         "<city: http://www.osp-core.com/city#>")

    def test_get_default_rel(self):
        """Test getting the default relationship."""
        # default rel defined as flag in entity name
        self.installer.install("city")
        namespace = self.namespace_registry.city
        self.assertEqual(namespace.get_default_rel().name, "hasPart")

        onto_def_rel = os.path.join(
            os.path.dirname(__file__),
            'default_rel_across_namespace_valid.yml'
        )
        self.installer.install(onto_def_rel)
        namespace = self.namespace_registry.default_rel_test_namespace_valid
        self.assertEqual(namespace.get_default_rel(), cuba.activeRelationship)

        onto_def_rel = os.path.join(
            os.path.dirname(__file__),
            'default_rel_across_namespace_two_definitions.yml'
        )
        self.assertRaises(ValueError, self.installer.install, onto_def_rel)

        onto_def_rel = os.path.join(
            os.path.dirname(__file__),
            'default_rel_across_namespace_uninstalled_entity.yml'
        )
        self.assertRaises(ValueError, self.installer.install, onto_def_rel)

        onto_def_rel = os.path.join(
            os.path.dirname(__file__),
            'default_rel_across_namespace_uninstalled_namespace.yml'
        )
        self.assertRaises(ValueError, self.installer.install, onto_def_rel)

    def test_contains(self):
        """Test containment."""
        self.installer.install("city")
        namespace = self.namespace_registry.city
        self.assertIn("City", namespace)
        self.assertIn("hasPart", namespace)

    def test_iter(self):
        """Test the __iter__() magic method."""
        self.installer.install("city")
        namespace = self.namespace_registry.city
        entities = set(namespace)
        self.assertIn(namespace.encloses, entities)
        self.assertIn(namespace.City, entities)
        self.assertIn(namespace.name, entities)
        self.assertEqual(len(entities), 32)

    def test_get_namespace_from_iri(self):
        """Test getting namespace object from IRI."""
        self.installer.install("city")
        ns_iri = rdflib.URIRef("http://www.osp-core.com/city#")
        namespace = self.namespace_registry.namespace_from_iri(ns_iri)
        self.assertEqual(namespace.get_name(), "city")
        self.assertEqual(namespace.get_iri(), ns_iri)
        ns_iri = rdflib.URIRef("http://www.random_namespace.com#")
        namespace = self.namespace_registry.namespace_from_iri(ns_iri)
        self.assertEqual(namespace.get_name(),
                         "http://www.random_namespace.com#")
        self.assertEqual(namespace.get_iri(), ns_iri)

    def test_get_namespace_name_and_iri(self):
        """Test getting namespace name and IRI."""
        self.installer.install("city")
        self.assertEqual(
            self.namespace_registry._get_namespace_name_and_iri(
                rdflib.URIRef("http://www.osp-core.com/city#City")
            ),
            ("city", rdflib.URIRef("http://www.osp-core.com/city#"))
        )
        self.assertEqual(
            self.namespace_registry._get_namespace_name_and_iri(
                rdflib.URIRef("http://www.random_namespace.com#Bla")
            ),
            ("http://www.random_namespace.com#",
             rdflib.URIRef("http://www.random_namespace.com#"))
        )
        self.assertEqual(
            self.namespace_registry._get_namespace_name_and_iri(
                rdflib.URIRef("http://www.random_namespace.com/Bla")
            ),
            ("http://www.random_namespace.com/",
             rdflib.URIRef("http://www.random_namespace.com/"))
        )

    def test_get_reference_by_label(self):
        """Test getting the reference style."""
        self.installer.install("city")
        ns_iri = rdflib.URIRef("http://www.osp-core.com/city#")
        self.assertFalse(
            self.namespace_registry._get_reference_by_label(ns_iri)
        )

        self.graph.add((
            ns_iri,
            rdflib_cuba._reference_by_label,
            rdflib.Literal(True)
        ))

        self.assertTrue(
            self.namespace_registry._get_reference_by_label(ns_iri)
        )

    def test_get_entity_name(self):
        """Test getting the name of an entity."""
        self.installer.install("city")
        self.modify_labels()
        ns_iri = rdflib.URIRef("http://www.osp-core.com/city#")
        iri = rdflib.URIRef("http://www.osp-core.com/city#City")
        self.assertEqual(
            self.namespace_registry._get_entity_name(iri, ns_iri),
            "City"
        )

        self.graph.add((
            ns_iri,
            rdflib_cuba._reference_by_label,
            rdflib.Literal(True)
        ))

        self.assertEqual(
            self.namespace_registry._get_entity_name(iri, ns_iri),
            "City_T"
        )


if __name__ == "__main__":
    unittest.main()
