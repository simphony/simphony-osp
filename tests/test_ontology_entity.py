"""Test the OntologyEntity."""

import unittest2 as unittest
import rdflib
import numpy as np

from osp.core.namespaces import cuba
from osp.core.ontology.cuba import rdflib_cuba

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city


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
            rdflib.term.URIRef('http://www.osp-core.com/city#City')
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
            (city.City.iri, rdflib.SKOS.prefLabel,
             rdflib.term.Literal('City', lang='en')),
            (city.City.iri, rdflib.RDFS.subClassOf, city.PopulatedPlace.iri),
            (city.City.iri, rdflib.RDF.type, rdflib.OWL.Class)
        })
        self.assertEqual(set(city.hasPart.get_triples()), {
            (city.hasPart.iri, rdflib.SKOS.prefLabel,
             rdflib.term.Literal('hasPart', lang='en')),
            (city.hasPart.iri, rdflib.RDFS.subPropertyOf, city.encloses.iri),
            (city.hasPart.iri, rdflib.RDF.type, rdflib.OWL.ObjectProperty),
            (city.hasPart.iri, rdflib.OWL.inverseOf, city.isPartOf.iri)
        })
        self.assertEqual(set(city.coordinates.get_triples()), {
            (city.coordinates.iri, rdflib.SKOS.prefLabel,
             rdflib.term.Literal('coordinates', lang='en')),
            (city.coordinates.iri, rdflib.RDFS.subPropertyOf,
             cuba.attribute.iri),
            (city.coordinates.iri, rdflib.RDF.type,
             rdflib.OWL.DatatypeProperty),
            (city.coordinates.iri, rdflib.RDF.type,
             rdflib.OWL.FunctionalProperty),
            (city.coordinates.iri, rdflib.RDFS.range,
             rdflib_cuba["_datatypes/VECTOR-INT-2"])
        })

    def test_transitive_hull(self):
        """Test the transitive_hull method."""
        self.assertEqual(set(
            city.PopulatedPlace._transitive_hull(
                rdflib.RDFS.subClassOf, blacklist={rdflib.OWL.Thing})),
            {city.GeographicalPlace, cuba.Entity}
        )
        self.assertEqual(
            set(city.PopulatedPlace._transitive_hull(rdflib.RDFS.subClassOf,
                                                     inverse=True)),
            {city.Street, city.City, city.Neighborhood}
        )

    def test_directly_connected(self):
        """Test the _directly_connected method."""
        self.assertEqual(set(
            city.PopulatedPlace._directly_connected(rdflib.RDFS.subClassOf)),
            {city.GeographicalPlace}
        )
        self.assertEqual(
            set(city.PopulatedPlace._directly_connected(rdflib.RDFS.subClassOf,
                                                        inverse=True)),
            {city.Street, city.City, city.Neighborhood}
        )

    def test_oclass_attributes(self):
        """Test the attributes of ontology classes."""
        self.assertEqual(city.City.attributes, {
            city.name: (None, True, None),
            city.coordinates: (rdflib.Literal('[0, 0]'), False, None),
        })
        self.assertEqual(city.City.own_attributes, {})
        self.assertEqual(city.GeographicalPlace.own_attributes, {
            city.name: (None, True, None),
        })
        self.maxDiff = None
        self.assertEqual(city.LivingBeing.own_attributes, {
            city.name: (rdflib.Literal("John Smith"), False, None),
            city.age: (rdflib.Literal(25), False, None)
        })
        self.assertEqual(city.Person.attributes, {
            city.name: (rdflib.Literal("John Smith"), False, None),
            city.age: (rdflib.Literal(25), False, None)
        })
        self.assertEqual(city.PopulatedPlace.attributes, {
            city.name: (None, True, None),
            city.coordinates: (rdflib.Literal('[0, 0]'), False, None)
        })
        self.assertEqual(city.GeographicalPlace.attributes, {
            city.name: (None, True, None),
        })

    def test_oclass_get_default(self):
        """Test getting the default values of attributes."""
        self.assertEqual(city.City._get_default(city.name.iri, city.City.iri),
                         None)
        self.assertEqual(city.City._get_default(city.name.iri,
                                                city.GeographicalPlace.iri),
                         None)
        self.assertEqual(city.City._get_default(city.coordinates.iri,
                                                city.City.iri),
                         None)
        self.assertEqual(city.City._get_default(city.coordinates.iri,
                                                city.PopulatedPlace.iri),
                         rdflib.term.Literal('[0, 0]'))

    def test_get_attribute_values(self):
        """Test getting the values of attributes."""
        self.assertRaises(TypeError, city.City._get_attributes_values,
                          kwargs={}, _force=False)
        self.assertRaises(TypeError, city.City._get_attributes_values,
                          kwargs={"name": "name", "invalid": "invalid"},
                          _force=False)
        self.assertEqual(city.City._get_attributes_values(kwargs={},
                                                          _force=True),
                         {city.coordinates: rdflib.term.Literal('[0, 0]')})
        self.assertEqual(city.City._get_attributes_values(kwargs={},
                                                          _force=True),
                         {city.coordinates: rdflib.term.Literal('[0, 0]')})
        self.assertEqual(city.City._get_attributes_values(
            kwargs={"name": "Freiburg"}, _force=True),
            {city.name: "Freiburg",
             city.coordinates: rdflib.term.Literal('[0, 0]')}
        )
        self.assertEqual(city.City._get_attributes_values(
            kwargs={"name": "Freiburg", "coordinates": [1, 1]}, _force=True),
            {city.name: "Freiburg",
             city.coordinates: [1, 1]}
        )

    def test_get_attribute_by_argname(self):
        """Test getting an attribute by the argument name."""
        self.assertEqual(city.City.get_attribute_by_argname("name"), city.name)
        self.assertEqual(city.City.get_attribute_by_argname("coordinates"),
                         city.coordinates)
        self.assertEqual(city.City.get_attribute_by_argname("invalid"),
                         None)

    def test_oclass_call(self):
        """Test calling an close to create CUDS."""
        c = city.City(name="Freiburg")
        self.assertEqual(c.name, "Freiburg")
        self.assertTrue(np.all(c.coordinates == np.array([0, 0])))
        c = city.City(name="Basel", coordinates=[1, 2])
        self.assertEqual(c.name, "Basel")
        self.assertTrue(np.all(c.coordinates == np.array([1, 2])))
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
                         rdflib_cuba["_datatypes/VECTOR-INT-2"])
        self.assertEqual(cuba.attribute.datatype, None)
        self.assertEqual(city.name.convert_to_datatype("abc"), "abc")
        self.assertEqual(city.name.convert_to_datatype(12.3), "12.3")
        self.assertEqual(city.name.convert_to_datatype([1, 2, 3]), "[1, 2, 3]")
        self.assertTrue(np.all(
            city.coordinates.convert_to_datatype([1, 2])
            == np.array([1, 2])))
        self.assertRaises(ValueError, city.coordinates.convert_to_datatype,
                          "[1, 2]")
        self.assertRaises(ValueError, city.coordinates.convert_to_datatype,
                          [1, 2, 3])
        self.assertTrue(np.all(
            city.coordinates.convert_to_datatype(rdflib.Literal([1, 2]))
            == np.array([1, 2])))
        self.assertEqual(
            city.coordinates.convert_to_basic_type(np.array([1, 2])),
            [1, 2]
        )


if __name__ == "__main__":
    unittest.main()
