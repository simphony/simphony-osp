"""Test the OntologyEntity."""

import numpy as np
import unittest2 as unittest
from rdflib import OWL, RDF, RDFS, SKOS, XSD, BNode, Literal, URIRef

from osp.core.namespaces import cuba
from osp.core.ontology.datatypes import Vector

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city


class TestOntologyEntity(unittest.TestCase):
    """Test the OntologyEntity."""

    def test_str(self):
        """Test conversion to string."""
        self.assertEqual(str(city.City), "city.City")
        self.assertEqual(repr(city.City), "<OntologyClass city.City>")

    def test_properties(self):
        """Test the properties of the oclass."""
        self.assertEqual(
            city.City.iri,
            URIRef('http://www.osp-core.com/city#City')
        )
        self.assertEqual(city.City.tblname, "city___City")
        self.assertEqual(city.City.namespace, city)
        self.assertEqual(city.City.description, "To Be Determined")
        self.assertEqual(city.LivingBeing.description, "A being that lives")

    def test_subclass(self):
        """Test the subclass method."""
        self.assertEqual(city.GeographicalPlace.subclasses, {
            city.GeographicalPlace, city.ArchitecturalStructure,
            city.PopulatedPlace, city.City, city.Neighborhood,
            city.Street, city.Building
        })
        self.assertEqual(city.GeographicalPlace.superclasses, {
            cuba.Entity, city.GeographicalPlace
        })
        self.assertEqual(city.GeographicalPlace.direct_subclasses, {
            city.PopulatedPlace, city.ArchitecturalStructure
        })
        self.assertEqual(city.GeographicalPlace.direct_superclasses, {
            cuba.Entity
        })
        self.assertEqual(city.hasPart.subclasses, {
            city.hasPart, city.hasMajor, city.hasChild, city.hasWorker
        })
        self.assertEqual(city.hasPart.superclasses, {
            city.encloses, cuba.activeRelationship, cuba.relationship,
            city.hasPart
        })
        self.assertEqual(city.hasPart.direct_subclasses, {
            city.hasChild, city.hasWorker
        })
        self.assertEqual(city.hasPart.direct_superclasses, {city.encloses})
        self.assertEqual(city.name.subclasses, {city.name})
        self.assertEqual(city.name.superclasses, {city.name, cuba.attribute})
        self.assertEqual(city.name.direct_subclasses, set())
        self.assertEqual(city.name.direct_superclasses, {cuba.attribute})

        self.assertTrue(city.City.is_subclass_of(city.GeographicalPlace))
        self.assertFalse(city.City.is_superclass_of(city.GeographicalPlace))
        self.assertTrue(city.City.is_subclass_of(city.City))
        self.assertTrue(city.City.is_superclass_of(city.City))
        self.assertFalse(city.GeographicalPlace.is_subclass_of(city.City))
        self.assertTrue(city.GeographicalPlace.is_superclass_of(city.City))

    def test_get_triples(self):
        """Test the get_triples method."""
        self.assertEqual(set(city.City.get_triples()), {
            (city.City.iri, SKOS.prefLabel,
             Literal('City', lang='en')),
            (city.City.iri, RDFS.subClassOf, city.PopulatedPlace.iri),
            (city.City.iri, RDF.type, OWL.Class)
        })
        self.assertEqual(set(city.hasPart.get_triples()), {
            (city.hasPart.iri, SKOS.prefLabel,
             Literal('hasPart', lang='en')),
            (city.hasPart.iri, RDFS.subPropertyOf, city.encloses.iri),
            (city.hasPart.iri, RDF.type, OWL.ObjectProperty),
            (city.hasPart.iri, OWL.inverseOf, city.isPartOf.iri)
        })
        self.assertEqual(set(city.coordinates.get_triples()), {
            (city.coordinates.iri, SKOS.prefLabel,
             Literal('coordinates', lang='en')),
            (city.coordinates.iri, RDFS.subPropertyOf,
             cuba.attribute.iri),
            (city.coordinates.iri, RDF.type,
             OWL.DatatypeProperty),
            (city.coordinates.iri, RDF.type,
             OWL.FunctionalProperty),
            (city.coordinates.iri, RDFS.range,
             URIRef("http://www.osp-core.com/types#Vector"))
        })

    def test_transitive_hull(self):
        """Test the transitive_hull method."""
        self.assertEqual(set(
            city.PopulatedPlace._transitive_hull(
                RDFS.subClassOf, blacklist={OWL.Thing})),
            {city.GeographicalPlace, cuba.Entity}
        )
        self.assertEqual(
            set(city.PopulatedPlace._transitive_hull(RDFS.subClassOf,
                                                     inverse=True)),
            {city.Street, city.City, city.Neighborhood}
        )

    def test_directly_connected(self):
        """Test the _directly_connected method."""
        self.assertEqual(set(
            city.PopulatedPlace._directly_connected(RDFS.subClassOf)),
            {city.GeographicalPlace}
        )
        self.assertEqual(
            set(city.PopulatedPlace._directly_connected(RDFS.subClassOf,
                                                        inverse=True)),
            {city.Street, city.City, city.Neighborhood}
        )

    def test_oclass_attributes(self):
        """Test the attributes of ontology classes."""
        self.assertEqual(city.City.attribute_declaration, {
            city.name: (None, True, None),
            city.coordinates: (Vector([0, 0]), False, None),
        })
        self.assertEqual(city.City._direct_attributes, {})
        self.assertEqual(city.GeographicalPlace._direct_attributes, {
            city.name: (None, True, None),
        })
        self.maxDiff = None
        self.assertEqual(city.LivingBeing._direct_attributes, {
            city.name: ("John Smith", False, None),
            city.age: (25, False, None)
        })
        self.assertEqual(city.Person.attribute_declaration, {
            city.name: ("John Smith", False, None),
            city.age: (25, False, None)
        })
        self.assertEqual(city.PopulatedPlace.attribute_declaration, {
            city.name: (None, True, None),
            city.coordinates: ([0, 0], False, None)
        })
        self.assertEqual(city.GeographicalPlace.attribute_declaration, {
            city.name: (None, True, None),
        })

    def test_oclass_get_default(self):
        """Test getting the default values of attributes."""
        self.assertEqual(city.City._get_default_python_object(city.name,
                                                              city.City.iri),
                         None)
        self.assertEqual(city.City._get_default_python_object(city.name,
                                                              city.GeographicalPlace.iri),
                         None)
        self.assertEqual(city.City._get_default_python_object(city.coordinates,
                                                              city.City.iri),
                         None)
        self.assertEqual(city.City._get_default_python_object(city.coordinates,
                                                              city.PopulatedPlace.iri),
                         [0, 0])

    def test_get_attribute_values(self):
        """Test getting the values of attributes."""
        self.assertRaises(TypeError, city.City.attributes,
                          kwargs={}, _force=False)
        self.assertRaises(TypeError, city.City.attributes,
                          kwargs={"name": "name", "invalid": "invalid"},
                          _force=False)
        self.assertEqual(city.City.attributes(kwargs={},
                                              _force=True),
                         {city.coordinates: [[0, 0]]})
        self.assertEqual(city.City.attributes(kwargs={},
                                              _force=True),
                         {city.coordinates: [[0, 0]]})
        self.assertEqual(city.City.attributes(
            kwargs={"name": "Freiburg"}, _force=True),
            {city.name: ["Freiburg"],
             city.coordinates: [[0, 0]]}
        )
        self.assertEqual(city.City.attributes(
            kwargs={"name": "Freiburg", "coordinates": [1, 1]}, _force=True),
            {city.name: ["Freiburg"],
             city.coordinates: [[1, 1]]}
        )

    def test_get_attribute_by_argname(self):
        """Test getting an attribute by the argument name."""
        self.assertEqual(city.City.get_attribute_by_argname("name"), city.name)
        self.assertEqual(city.City.get_attribute_by_argname("coordinates"),
                         city.coordinates)
        self.assertIs(city.City.get_attribute_by_argname("invalid"), None)

    def test_oclass_call(self):
        """Test calling an close to create CUDS."""
        c = city.City(name="Freiburg")
        self.assertEqual(c.name, "Freiburg")
        self.assertTrue(c.coordinates == Vector([0, 0]))
        c = city.City(name="Basel", coordinates=[1, 2])
        self.assertEqual(c.name, "Basel")
        self.assertTrue(c.coordinates == Vector([1, 2]))
        self.assertRaises(TypeError, city.City)
        self.assertRaises(TypeError, city.City, name="Name", invalid="invalid")

    def test_rel_inverse(self):
        """Test the inverse of relationships."""
        self.assertEqual(city.hasPart.inverse, city.isPartOf)
        self.assertEqual(city.isPartOf.inverse, city.hasPart)
        self.assertEqual(cuba.relationship.inverse, cuba.relationship)
        self.assertEqual(cuba.activeRelationship.inverse,
                         cuba.passiveRelationship)
        self.assertEqual(cuba.passiveRelationship.inverse,
                         cuba.activeRelationship)
        self.assertEqual(city.hasMajor.inverse,
                         city.INVERSE_OF_hasMajor)
        self.assertEqual(city.INVERSE_OF_hasMajor.direct_superclasses,
                         {city.worksIn})
        self.assertEqual(city.INVERSE_OF_hasMajor.inverse, city.hasMajor)

    def test_attribute_datatype(self):
        """Test the datatypes of the attributes."""
        self.assertEqual(city.name.datatype, None)
        self.assertEqual(city.coordinates.datatype,
                         URIRef("http://www.osp-core.com/types#Vector"))
        self.assertEqual(cuba.attribute.datatype, None)
        self.assertEqual(city.name.convert_to_datatype("abc"), "abc")
        self.assertEqual(city.name.convert_to_datatype(12.3), '12.3')
        self.assertEqual(city.name.convert_to_datatype([1, 2, 3]), '[1, 2, 3]')
        self.assertTrue(np.all(
            city.coordinates.convert_to_datatype([1, 2])
            == np.array([1, 2])))
        self.assertTrue(city.coordinates.convert_to_datatype(Literal([1, 2]))
                        == Vector([1, 2]))

    def test_hasValue_statement(self):
        """Test hasValue statement from the OWL ontology for data properties.

        The hasValue statement is an OWL restriction, and forces the individual
        to be connected at least once to a specific literal through a specific
        datatype restriction.
        """
        graph = city._graph
        namespace_registry = city._namespace_registry

        triples_hassymboldata = ((URIRef("http://www.osp-core.com/city#"
                                         "hasSymbolData"),
                                  RDF.type,
                                  OWL.DatatypeProperty),
                                 )
        bnode = BNode()
        triples_restriction = ((bnode, RDF.type,
                                OWL.Restriction),
                               (bnode, OWL.onProperty,
                                URIRef("http://www.osp-core.com/city#"
                                       "hasSymbolData")),
                               (bnode, OWL.hasValue,
                                Literal('C', datatype=XSD.string)),
                               )
        triples_carbonsymbol = ((URIRef("http://www.osp-core.com/city#"
                                        "CarbonSymbol"),
                                 RDF.type, OWL.Class),
                                (URIRef("http://www.osp-core.com/city#"
                                        "CarbonSymbol"),
                                 RDFS.subClassOf, bnode),
                                )
        triples = (*triples_hassymboldata, *triples_carbonsymbol,
                   *triples_restriction)

        for triple in triples:
            graph.add(triple)
        namespace_registry.update_namespaces()
        try:
            carbon_symbol = city.CarbonSymbol()
            self.assertEqual(carbon_symbol.hasSymbolData, 'C')
        finally:
            for triple in triples:
                graph.remove(triple)
            namespace_registry.update_namespaces()


if __name__ == "__main__":
    unittest.main()
