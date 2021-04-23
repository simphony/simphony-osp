"""Test the utility functions."""

import io
from osp.core.utils.general import import_rdf_file
import unittest
import responses
import os
import osp.core
import rdflib
import json
import uuid
import tempfile
from rdflib_jsonld.parser import to_rdf as json_to_rdf
from osp.core.namespaces import cuba
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.session.transport.transport_utils import serializable
from osp.core.session.core_session import CoreSession
from osp.core.session.buffers import EngineContext
from osp.core.utils import (
    clone_cuds_object,
    create_recycle, create_from_cuds_object,
    check_arguments, find_cuds_object,
    find_cuds_object_by_uid, remove_cuds_object,
    pretty_print, deserialize,
    find_cuds_objects_by_oclass, find_relationships,
    find_cuds_objects_by_attribute, post,
    get_relationships_between,
    get_neighbor_diff, change_oclass, branch, validate_tree_against_schema,
    ConsistencyError, CardinalityError, get_rdf_graph,
    delete_cuds_object_recursively,
    serialize, get_custom_datatype_triples, get_custom_datatypes
)
from osp.core.session.buffers import BufferContext
from osp.core.cuds import Cuds

try:
    from .test_session_city import TestWrapperSession
    from .test_transport_session import assertJsonLdEqual
except ImportError:
    from test_session_city import TestWrapperSession
    from test_transport_session import assertJsonLdEqual

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser(namespace_registry._graph).parse("city")
    namespace_registry.update_namespaces()
    city = namespace_registry.city


PRFX = 'http://www.osp-core.com/cuds#00000000-0000-0000-0000-0000000000'
CUDS_DICT = [{
    '@id': PRFX + "01",
    '@type': ['http://www.osp-core.com/city#City']
}, {
    '@id': PRFX + "03",
    '@type': ['http://www.osp-core.com/city#Person']
}, {
    '@id': PRFX + "02",
    '@type': ['http://www.osp-core.com/city#Person']
}, {
    '@id': PRFX + "7b",
    '@type': ['http://www.osp-core.com/city#Citizen'],
    'http://www.osp-core.com/city#INVERSE_OF_hasInhabitant': [
        {'@id': PRFX + "01"}],
    'http://www.osp-core.com/city#age': [{'@value': 23}],
    'http://www.osp-core.com/city#hasChild': [
        {'@id': PRFX + "02"},
        {'@id': PRFX + "03"}],
    'http://www.osp-core.com/city#name': [{'@value': 'Peter'}]
}, {
    '@id': rdflib_cuba._serialization,
    str(rdflib.RDF.first): [{'@value': "00000000-0000-0000-0000-00000000007b"}]
}]

CUDS_LIST = [
    {"@id": PRFX + "01",
     "http://www.osp-core.com/city#name": [{"@value": "Freiburg"}],
     "http://www.osp-core.com/city#coordinates": [{
         "@value": "[0, 0]",
         "@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2"}],
     "@type": ["http://www.osp-core.com/city#City"],
     "http://www.osp-core.com/city#hasPart": [
         {"@id": PRFX + "02"}]},
    {"@id": PRFX + "02",
     "http://www.osp-core.com/city#hasPart": [
         {"@id": PRFX + "03"}],
     "@type": ["http://www.osp-core.com/city#Neighborhood"],
     "http://www.osp-core.com/city#coordinates": [{
         "@value": "[0, 0]",
         "@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2"}],
     "http://www.osp-core.com/city#name": [{"@value": "Littenweiler"}],
     "http://www.osp-core.com/city#isPartOf": [
         {"@id": PRFX + "01"}]},
    {"@id": PRFX + "03",
     "http://www.osp-core.com/city#coordinates": [{
         "@value": "[0, 0]",
         "@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2"}],
     "http://www.osp-core.com/city#isPartOf": [
         {"@id": PRFX + "02"}],
     "@type": ["http://www.osp-core.com/city#Street"],
     "http://www.osp-core.com/city#name": [{"@value": "Schwarzwaldstraße"}]},
    {"@id": rdflib_cuba._serialization,
     str(rdflib.RDF.first): [
         {"@value": "00000000-0000-0000-0000-000000000001"}]
     }
]


def get_test_city():
    """Set up a test City for the tests."""
    c = city.City(name="Freiburg", coordinates=[1, 2])
    p1 = city.Citizen(name="Rainer")
    p2 = city.Citizen(name="Carlos")
    p3 = city.Citizen(name="Maria")
    n1 = city.Neighborhood(name="Zähringen", coordinates=[2, 3])
    n2 = city.Neighborhood(name="St. Georgen", coordinates=[3, 4])
    s1 = city.Street(name="Lange Straße", coordinates=[4, 5])

    c.add(p1, p2, p3, rel=city.hasInhabitant)
    p1.add(p3, rel=city.hasChild)
    p2.add(p3, rel=city.hasChild)
    c.add(n1, n2)
    n1.add(s1)
    n2.add(s1)
    s1.add(p2, p3, rel=city.hasInhabitant)
    return [c, p1, p2, p3, n1, n2, s1]


class TestUtils(unittest.TestCase):
    """Test the utility functions."""

    def setUp(self):
        """Set up the testcases: Reset the session."""
        from osp.core.cuds import Cuds
        from osp.core.session import CoreSession
        Cuds._session = CoreSession()

    def test_get_rdf_graph(self):
        """Test the get_rdf_graph function."""
        with TestWrapperSession() as session:
            wrapper = cuba.Wrapper(session=session)
            c = city.City(name='freiburg', session=session)
            wrapper.add(c, rel=cuba.activeRelationship)
            graph = get_rdf_graph(c.session, skip_ontology=False)

            # cuds must be in the grap
            iri = rdflib.URIRef(
                "http://www.osp-core.com/cuds#%s" % c.uid
            )
            subjects = list(graph.subjects())
            self.assertTrue(iri in subjects)
            # ontology entities must be in the graph
            cuba_entity_iri = rdflib.URIRef(
                "http://www.osp-core.com/cuba#Entity"
            )
            self.assertTrue(cuba_entity_iri in subjects)
            # fail on invalid arguments
            self.assertRaises(TypeError, get_rdf_graph, c)
            self.assertRaises(TypeError, get_rdf_graph, 42)

            self.maxDiff = None
            g2 = get_rdf_graph(c.session, True)
            self.assertIn((city.coordinates.iri, rdflib.RDFS.range,
                           rdflib_cuba["_datatypes/VECTOR-INT-2"]),
                          set(graph - g2))
            self.assertIn((rdflib_cuba["_datatypes/VECTOR-INT-2"],
                           rdflib.RDF.type, rdflib.RDFS.Datatype),
                          set(graph - g2))

    def test_get_custom_datatypes(self):
        """Test the get_custom_datatypes function."""
        self.assertIn(rdflib_cuba["_datatypes/VECTOR-INT-2"],
                      get_custom_datatypes())
        for elem in get_custom_datatypes():
            self.assertIn(elem, rdflib_cuba)
        self.assertIn((city.coordinates.iri, rdflib.RDFS.range,
                       rdflib_cuba["_datatypes/VECTOR-INT-2"]),
                      get_custom_datatype_triples())
        self.assertIn((rdflib_cuba["_datatypes/VECTOR-INT-2"],
                       rdflib.RDF.type, rdflib.RDFS.Datatype),
                      get_custom_datatype_triples())

    def test_validate_tree_against_schema(self):
        """Test validation of CUDS tree against schema.yml."""
        schema_file = os.path.join(
            os.path.dirname(__file__),
            'test_validation_schema_city.yml'
        )
        schema_file_with_missing_entity = os.path.join(
            os.path.dirname(__file__),
            'test_validation_schema_city_with_missing_entity.yml'
        )
        schema_file_with_missing_relationship = os.path.join(
            os.path.dirname(__file__),
            'test_validation_schema_city_with_missing_relationship.yml'
        )
        schema_file_with_optional_subtree = os.path.join(
            os.path.dirname(__file__),
            'test_validation_schema_city_with_optional_subtree.yml'
        )

        c = city.City(name='freiburg')

        # empty city is not valid
        self.assertRaises(
            ConsistencyError,
            validate_tree_against_schema,
            c,
            schema_file
        )

        # unless I do not specify relationships for it
        validate_tree_against_schema(c, schema_file_with_missing_relationship)

        # but it at least should be a city,
        # even when no relationships are defined
        wrong_object = cuba.File(path='some path')
        self.assertRaises(
            ConsistencyError,
            validate_tree_against_schema,
            wrong_object,
            schema_file_with_missing_relationship
        )

        # with opional inhabitants an empty city is ok
        validate_tree_against_schema(c, schema_file_with_optional_subtree)

        # but the optional subtree should follow its own constraints
        # (here a citizen needs to work in a city)
        c.add(city.Citizen(name='peter'), rel=city.hasInhabitant)
        self.assertRaises(
            CardinalityError,
            validate_tree_against_schema,
            c,
            schema_file_with_optional_subtree
        )

        c.add(city.Neighborhood(name='some hood'))
        c.add(city.Citizen(name='peter'), rel=city.hasInhabitant)

        # street of neighborhood violated
        self.assertRaises(
            CardinalityError,
            validate_tree_against_schema,
            c,
            schema_file
        )

        c.get(oclass=city.Neighborhood)[0].add(city.Street(name='abc street'))

        # now the city is valid and validation should pass
        validate_tree_against_schema(c, schema_file)

        # entity that was defined is completely missing in cuds tree
        self.assertRaises(
            ConsistencyError,
            validate_tree_against_schema,
            c,
            schema_file_with_missing_entity
        )

    def test_branch(self):
        """Test the branch function."""
        x = branch(
            branch(
                city.City(name="Freiburg"),
                city.Citizen(name="Peter"),
                city.Citizen(name="Maria"),
                rel=city.hasInhabitant
            ),
            city.Neighborhood(name="Herdern"),
            city.Neighborhood(name="Vauban")
        )
        self.assertEqual(x.name, "Freiburg")
        self.assertEqual({"Herdern", "Vauban"},
                         set(map(lambda x: x.name,
                                 x.get(oclass=city.Neighborhood))))
        self.assertEqual({"Peter", "Maria"},
                         set(map(lambda x: x.name,
                                 x.get(rel=city.hasInhabitant))))

    @responses.activate
    def test_post(self):
        """Test sending a cuds object to the server."""
        def request_callback(request):
            headers = {'request-id': '728d329e-0e86-11e4-a748-0c84dc037c13'}
            return (200, headers, request.body)

        responses.add_callback(
            responses.POST, 'http://dsms.com',
            callback=request_callback,
            content_type='application/json',
        )

        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        response = post('http://dsms.com', c)

        serialized = serializable([c, p1, p2, p3, n1, n2, s1],
                                  partition_cuds=False, mark_first=True)
        assertJsonLdEqual(self, serialized, response.json())

        response = post('http://dsms.com', c, max_depth=1)
        serialized = serializable([c, p1, p2, p3, n1, n2],
                                  partition_cuds=False, mark_first=True)
        assertJsonLdEqual(self, serialized, response.json())

    def test_deserialize(self):
        """Test the deserialize function."""
        result = deserialize(CUDS_DICT)
        self.assertTrue(result.is_a(city.Citizen))
        self.assertEqual(result.name, "Peter")
        self.assertEqual(result.age, 23)

        self.setUp()
        assertJsonLdEqual(self, CUDS_LIST,
                          json.loads(serialize(deserialize(CUDS_LIST))))

    def test_import_rdf_file(self):
        """Test the deserialize function."""
        g = json_to_rdf(CUDS_DICT[:-1], rdflib.Graph())
        with TestWrapperSession() as s:
            with tempfile.TemporaryDirectory() as d:
                f = os.path.join(d, "test")
                g.serialize(f, format="ttl")
                import_rdf_file(f, format="ttl", session=s)
                self.assertEqual(set(s._buffers[0][0]), {
                    uuid.UUID(int=1), uuid.UUID(int=2), uuid.UUID(int=3),
                    uuid.UUID(int=123)})
                self.assertEqual(s._buffers[0][1:], [{}, {}])
                self.assertEqual(s._buffers[1], [{}, {}, {}])

        self.setUp()

        g = json_to_rdf(CUDS_LIST[:-1], rdflib.Graph())
        with TestWrapperSession() as s:
            with tempfile.TemporaryDirectory() as d:
                f = os.path.join(d, "test")
                g.serialize(f, format="ttl")
                import_rdf_file(f, format="ttl", session=s)
                self.assertEqual(set(s._buffers[0][0]), {
                    uuid.UUID(int=1), uuid.UUID(int=2), uuid.UUID(int=3)})
                self.assertEqual(s._buffers[0][1:], [{}, {}])
                self.assertEqual(s._buffers[1], [{}, {}, {}])

    def test_serialize(self):
        """Test the serialize function."""
        c = branch(
            city.City(name="Freiburg", uid=1),
            branch(
                city.Neighborhood(name="Littenweiler", uid=2),
                city.Street(name="Schwarzwaldstraße", uid=3)
            )
        )
        self.maxDiff = None
        assertJsonLdEqual(
            self,
            json.loads(serialize(c)),
            CUDS_LIST
        )
        assertJsonLdEqual(
            self,
            serialize(c, json_dumps=False),
            CUDS_LIST
        )

    def test_clone_cuds_object(self):
        """Test cloning of cuds."""
        a = city.City(name="Freiburg")
        with CoreSession() as session:
            w = city.CityWrapper(session=session)
            aw = w.add(a)
            clone = clone_cuds_object(aw)
            self.assertIsNot(aw, None)
            self.assertIs(clone.session, aw.session)
            self.assertEqual(clone.uid, aw.uid)
            self.assertIs(aw, session._registry.get(aw.uid))
            self.assertEqual(clone.name, "Freiburg")

    def test_create_recycle(self):
        """Test creation of cuds_objects for different session."""
        default_session = CoreSession()
        osp.core.cuds.Cuds._session = default_session
        a = city.City(name="Freiburg")
        self.assertIs(a.session, default_session)
        with TestWrapperSession() as session:
            w = city.CityWrapper(session=session)
            with EngineContext(session):
                b = create_recycle(
                    oclass=city.City,
                    kwargs={"name": "Offenburg"},
                    uid=a.uid,
                    session=session,
                    fix_neighbors=False)
            self.assertEqual(b.name, "Offenburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid, w.uid})
            self.assertIs(session._registry.get(b.uid), b)
            self.assertEqual(session._buffers, [
                [{w.uid: w}, dict(), dict()],
                [{b.uid: b}, dict(), dict()]]
            )

            x = city.Citizen(session=default_session)
            x = b.add(x, rel=city.hasInhabitant)

            c = create_recycle(oclass=city.City,
                               kwargs={"name": "Emmendingen"},
                               session=session, uid=a.uid,
                               fix_neighbors=False)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Emmendingen")
            self.assertEqual(c.get(rel=cuba.relationship), [])
            self.assertNotEqual(x.get(rel=cuba.relationship), [])
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(session._buffers, [
                [{w.uid: w, x.uid: x}, {c.uid: c}, dict()],
                [dict(), dict(), dict()]]
            )

            x = city.Citizen(session=default_session)
            x = c.add(x, rel=city.hasInhabitant)

            c = create_recycle(oclass=city.City,
                               kwargs={"name": "Karlsruhe"},
                               session=session, uid=a.uid,
                               fix_neighbors=True)
            self.assertEqual(x.get(rel=cuba.relationship), [])

    def test_create_from_cuds_object(self):
        """Test copying cuds_objects to different session."""
        default_session = CoreSession()
        Cuds._session = default_session
        a = city.City(name="Freiburg")
        self.assertIs(a.session, default_session)
        with TestWrapperSession() as session:
            w = city.CityWrapper(session=session)
            with EngineContext(session):
                b = create_from_cuds_object(a, session)
            self.assertEqual(b.name, "Freiburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid, w.uid})
            self.assertIs(session._registry.get(b.uid), b)
            self.assertEqual(session._buffers, [
                [{w.uid: w}, dict(), dict()],
                [{b.uid: b}, dict(), dict()]])

            b.name = "Emmendingen"
            x = city.Citizen(age=54, name="Franz", session=default_session)
            b.add(x, rel=city.hasInhabitant)
            y = city.Citizen(age=21, name="Rolf", session=default_session)
            a.add(y, rel=city.hasInhabitant)

            c = create_from_cuds_object(a, session)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Freiburg")
            self.assertEqual(len(c.get(rel=cuba.relationship)), 1)
            self.assertEqual(c._neighbors[city.hasInhabitant],
                             {y.uid: [city.Citizen]})
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid, y.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(session._buffers, [
                [{x.uid: x, w.uid: w}, {c.uid: c}, dict()],
                [dict(), dict(), dict()]])

    def test_change_oclass(self):
        """Check utility method to change oclass."""
        c = city.City(name="Freiburg")
        p1 = city.Citizen(name="Tim")
        p2 = city.Citizen(name="Tom")
        c.add(p1, p2, rel=city.hasInhabitant)
        change_oclass(c, city.PopulatedPlace, {
            "name": "Umkirch"
        })
        self.assertEqual(c.oclass, city.PopulatedPlace)
        self.assertEqual(p1._neighbors[city.INVERSE_OF_hasInhabitant],
                         {c.uid: [city.PopulatedPlace]})
        self.assertEqual(p2._neighbors[city.INVERSE_OF_hasInhabitant],
                         {c.uid: [city.PopulatedPlace]})

    def test_check_arguments(self):
        """Test checking of arguments."""
        check_arguments(str, "hello", "bye")
        check_arguments((int, float), 1, 1.2, 5.9, 2)
        check_arguments(Cuds, city.City(name="Freiburg"))
        self.assertRaises(TypeError, check_arguments, str, 12)
        self.assertRaises(TypeError, check_arguments, (int, float), 1.2, "h")
        self.assertRaises(TypeError, check_arguments,
                          Cuds, city.City)

    def test_find_cuds_object(self):
        """Test to find cuds objects by some criterion."""
        def find_maria(x):
            return hasattr(x, "name") and x.name == "Maria"

        def find_freiburg(x):
            return hasattr(x, "name") and x.name == "Freiburg"

        def find_non_leaves(x):
            return len(x.get()) != 0

        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertIs(find_cuds_object(
            find_maria, c, cuba.activeRelationship, False), p3)
        self.assertIs(find_cuds_object(
            find_maria, c, cuba.passiveRelationship, False), None)
        self.assertEqual(find_cuds_object(
            find_maria, c, cuba.passiveRelationship, True), list())
        all_found = find_cuds_object(
            find_maria, c, cuba.activeRelationship, True)
        self.assertIs(all_found[0], p3)
        self.assertEqual(len(all_found), 1)
        self.assertIs(find_cuds_object(
            find_freiburg, c, cuba.activeRelationship, False), c)
        all_found = find_cuds_object(
            find_non_leaves, c, cuba.activeRelationship, True)
        self.assertEqual(len(all_found), 6)
        self.assertEqual(set(all_found), {c, p1, p2, n1, n2, s1})
        all_found = find_cuds_object(
            find_non_leaves, c, cuba.activeRelationship, True,
            max_depth=1)
        self.assertEqual(len(all_found), 5)
        self.assertEqual(set(all_found), {c, p1, p2, n1, n2})

    def test_find_cuds_object_by_uid(self):
        """Test to find a cuds object by uid in given subtree."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertIs(find_cuds_object_by_uid(
            c.uid, c, cuba.activeRelationship), c)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, c, cuba.activeRelationship), p1)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, c, cuba.activeRelationship), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, c, cuba.activeRelationship), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, c, cuba.activeRelationship), n1)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, c, cuba.activeRelationship), n2)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, c, cuba.activeRelationship), s1)
        self.assertIs(find_cuds_object_by_uid(
            c.uid, c, city.hasInhabitant), c)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, c, city.hasInhabitant), p1)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, c, city.hasInhabitant), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, c, city.hasInhabitant), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, c, city.hasInhabitant), None)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, c, city.hasInhabitant), None)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, c, city.hasInhabitant), None)
        self.assertIs(find_cuds_object_by_uid(
            c.uid, n1, cuba.activeRelationship), None)
        self.assertIs(find_cuds_object_by_uid(
            p1.uid, n1, cuba.activeRelationship), None)
        self.assertIs(find_cuds_object_by_uid(
            p2.uid, n1, cuba.activeRelationship), p2)
        self.assertIs(find_cuds_object_by_uid(
            p3.uid, n1, cuba.activeRelationship), p3)
        self.assertIs(find_cuds_object_by_uid(
            n1.uid, n1, cuba.activeRelationship), n1)
        self.assertIs(find_cuds_object_by_uid(
            n2.uid, n1, cuba.activeRelationship), None)
        self.assertIs(find_cuds_object_by_uid(
            s1.uid, n1, cuba.activeRelationship), s1)

    def test_find_cuds_objects_by_oclass(self):
        """Test find by cuba key."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(find_cuds_objects_by_oclass(
            city.City, c, cuba.activeRelationship),
            [c])
        found = find_cuds_objects_by_oclass(
            city.Citizen,
            c, cuba.activeRelationship)
        self.assertEqual(len(found), 3)
        self.assertEqual(set(found), {p1, p2, p3})
        found = find_cuds_objects_by_oclass(
            city.Neighborhood, c,
            cuba.activeRelationship)
        self.assertEqual(set(found), {n1, n2})
        self.assertEqual(len(found), 2)
        self.assertEqual(find_cuds_objects_by_oclass(
            city.Street, c, cuba.activeRelationship),
            [s1])
        found = find_cuds_objects_by_oclass(cuba.Entity,
                                            c, cuba.relationship)
        self.assertEqual(set(found), {c, p1, p2, p3, n1, n2, s1})

    def test_find_cuds_objects_by_attribute(self):
        """Test the find_cuds_objects_by_attribute method."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        self.assertEqual(
            find_cuds_objects_by_attribute("name", "Maria", c,
                                           cuba.relationship), [p3]
        )
        found = find_cuds_objects_by_attribute("age", 25, c,
                                               cuba.relationship)
        self.assertEqual(len(found), 3)
        self.assertEqual(set(found), {p1, p2, p3})
        found = find_cuds_objects_by_attribute(
            "age", 25, c, cuba.passiveRelationship
        )
        self.assertEqual(found, [])

    def test_find_relationships(self):
        """Test find by relationships."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        found = find_relationships(city.INVERSE_OF_hasInhabitant, c,
                                   cuba.relationship, False)
        self.assertEqual(set(found), {p1, p2, p3})
        self.assertEqual(len(found), 3)
        found = find_relationships(city.isPartOf, c,
                                   cuba.relationship, True)
        self.assertEqual(set(found), {p3, n1, n2, s1})
        self.assertEqual(len(found), 4)
        found = find_relationships(city.isPartOf, c,
                                   cuba.relationship, False)
        self.assertEqual(set(found), {n1, n2, s1})

    def test_remove_cuds_object(self):
        """Test removing cuds from datastructure."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        remove_cuds_object(p3)
        self.assertEqual(p3.get(rel=cuba.relationship), [])
        self.assertNotIn(p3, c.get(rel=cuba.relationship))
        self.assertNotIn(p3, p1.get(rel=cuba.relationship))
        self.assertNotIn(p3, p2.get(rel=cuba.relationship))
        self.assertNotIn(p3, n1.get(rel=cuba.relationship))
        self.assertNotIn(p3, n2.get(rel=cuba.relationship))
        self.assertNotIn(p3, s1.get(rel=cuba.relationship))

    def test_get_relationships_between(self):
        """Test the get_the_relationship_between two cuds entities."""
        c = city.City(name="Freiburg")
        p = city.Citizen(name="Peter")
        self.assertEqual(get_relationships_between(c, p), set())
        self.assertEqual(get_relationships_between(p, c), set())
        c.add(p, rel=city.hasInhabitant)
        self.assertEqual(get_relationships_between(c, p),
                         {city.hasInhabitant})
        self.assertEqual(get_relationships_between(p, c),
                         {city.INVERSE_OF_hasInhabitant})
        c.add(p, rel=city.hasWorker)
        self.assertEqual(get_relationships_between(c, p),
                         {city.hasInhabitant,
                          city.hasWorker})
        self.assertEqual(get_relationships_between(p, c),
                         {city.INVERSE_OF_hasInhabitant,
                          city.worksIn})

    def test_get_neighbor_diff(self):
        """Test get_neighbor_diff method."""
        c1 = city.City(name="Paris")
        c2 = city.City(name="Berlin")
        c3 = city.City(name="London")
        n1 = city.Neighborhood(name="Zähringen")
        n2 = city.Neighborhood(name="Herdern")
        s1 = city.Street(name="Waldkircher Straße")
        s2 = city.Street(name="Habsburger Straße")
        s3 = city.Street(name="Lange Straße")

        n1.add(c1, c2, rel=city.isPartOf)
        n2.add(c2, c3, rel=city.isPartOf)
        n1.add(s1, s2)
        n2.add(s2, s3)

        self.assertEqual(
            set(get_neighbor_diff(n1, n2)),
            {(c1.uid, city.isPartOf), (s1.uid, city.hasPart)}
        )

        self.assertEqual(
            set(get_neighbor_diff(n2, n1)),
            {(c3.uid, city.isPartOf), (s3.uid, city.hasPart)}
        )

        self.assertEqual(
            set(get_neighbor_diff(n1, None)),
            {(c1.uid, city.isPartOf), (s1.uid, city.hasPart),
             (c2.uid, city.isPartOf), (s2.uid, city.hasPart)}
        )

        self.assertEqual(
            set(get_neighbor_diff(None, n2)),
            set()
        )

    def test_pretty_print(self):
        """Test printing cuds objects in a human readable way."""
        c, p1, p2, p3, n1, n2, s1 = get_test_city()
        px = city.Person()
        c.add(px, rel=city.encloses)
        f = io.StringIO()
        pretty_print(c, file=f)
        self.maxDiff = 5000
        self.assertEqual(f.getvalue(), "\n".join([
            "- Cuds object named <Freiburg>:",
            "  uuid: %s" % c.uid,
            "  type: city.City",
            "  superclasses: city.City, city.GeographicalPlace, "
            + "city.PopulatedPlace, cuba.Entity",
            "  values: coordinates: [1 2]",
            "  description: ",
            "    To Be Determined",
            "",
            "   |_Relationship city.encloses:",
            "   | -  city.Person cuds object named <John Smith>:",
            "   |    uuid: %s" % px.uid,
            "   |    age: 25",
            "   |_Relationship city.hasInhabitant:",
            "   | -  city.Citizen cuds object named <Carlos>:",
            "   | .  uuid: %s" % p2.uid,
            "   | .  age: 25",
            "   | .   |_Relationship city.hasChild:",
            "   | .     -  city.Citizen cuds object named <Maria>:",
            "   | .        uuid: %s" % p3.uid,
            "   | .        age: 25",
            "   | -  city.Citizen cuds object named <Maria>:",
            "   | .  uuid: %s" % p3.uid,
            "   | .  (already printed)",
            "   | -  city.Citizen cuds object named <Rainer>:",
            "   |    uuid: %s" % p1.uid,
            "   |    age: 25",
            "   |     |_Relationship city.hasChild:",
            "   |       -  city.Citizen cuds object named <Maria>:",
            "   |          uuid: %s" % p3.uid,
            "   |          (already printed)",
            "   |_Relationship city.hasPart:",
            "     -  city.Neighborhood cuds object named <St. Georgen>:",
            "     .  uuid: %s" % n2.uid,
            "     .  coordinates: [3 4]",
            "     .   |_Relationship city.hasPart:",
            "     .     -  city.Street cuds object named <Lange Straße>:",
            "     .        uuid: %s" % s1.uid,
            "     .        coordinates: [4 5]",
            "     .         |_Relationship city.hasInhabitant:",
            "     .           -  city.Citizen cuds object named <Carlos>:",
            "     .           .  uuid: %s" % p2.uid,
            "     .           .  (already printed)",
            "     .           -  city.Citizen cuds object named <Maria>:",
            "     .              uuid: %s" % p3.uid,
            "     .              (already printed)",
            "     -  city.Neighborhood cuds object named <Zähringen>:",
            "        uuid: %s" % n1.uid,
            "        coordinates: [2 3]",
            "         |_Relationship city.hasPart:",
            "           -  city.Street cuds object named <Lange Straße>:",
            "              uuid: %s" % s1.uid,
            "              (already printed)",
            ""]))

    def test_delete_cuds_object_recursively(self):
        """Test the delete_cuds_object_recursively function."""
        with TestWrapperSession() as session:
            wrapper = city.CityWrapper(session=session)
            a = city.City(name='freiburg', session=session)
            b = city.Citizen(name='peter', session=session)
            branch(
                wrapper,
                branch(a, b, rel=city.hasInhabitant)
            )
            self.maxDiff = None
            session._reset_buffers(BufferContext.USER)
            delete_cuds_object_recursively(a)
            self.assertEqual(session._buffers, [
                [{}, {wrapper.uid: wrapper}, {a.uid: a, b.uid: b}],
                [{}, {}, {}],
            ])
            self.assertEqual(wrapper.get(rel=cuba.relationship), [])
            self.assertEqual(a.get(rel=cuba.relationship), [])
            self.assertEqual(b.get(rel=cuba.relationship), [])


if __name__ == "__main__":
    unittest.main()
