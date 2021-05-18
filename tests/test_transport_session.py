"""This file contains tests for the transport session."""
import unittest2 as unittest
import uuid
import json
import rdflib
from rdflib.compare import isomorphic
from copy import deepcopy
from osp.core.session.buffers import BufferContext, EngineContext, \
    BufferType
from osp.core.utils.wrapper_development import create_recycle
from osp.core.session.wrapper_session import consumes_buffers
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer
from osp.core.session.transport.transport_utils import (
    deserialize, serializable, deserialize_buffers,
    serialize_buffers, LOAD_COMMAND, INITIALIZE_COMMAND, import_rdf
)
from osp.core.utils.wrapper_development import create_from_cuds_object
from rdflib_jsonld.parser import to_rdf as json_to_rdf

try:
    from .test_session_city import TestWrapperSession
except ImportError:
    from test_session_city import TestWrapperSession

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
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
}]

CUDS_LIST_NON_PARTITIONED = {
    '@graph': [{
        '@id': PRFX + '7b',
        '@type': 'city:Citizen',
        'city:name': 'Peter',
        'city:age': 23,
        'city:INVERSE_OF_hasInhabitant': {
            '@id': PRFX + '01'},
        'city:hasChild': [
            {'@id': PRFX + '02'},
            {'@id': PRFX + '03'}]
    }, {
        '@id': PRFX + '01',
        '@type': 'city:City', 'city:coordinates': {
            '@type': 'cuba:_datatypes/VECTOR-INT-2', '@value': '[0, 0]'},
        'city:name': 'Freiburg',
        'city:hasInhabitant': {'@id': PRFX + '7b'}
    }, {
        '@id': PRFX + '02',
        '@type': 'city:Person',
        'city:age': 25,
        'city:name': 'John Smith',
        'city:isChildOf': {'@id': PRFX + '7b'}
    }, {
        '@id': PRFX + '03',
        '@type': 'city:Person',
        'city:age': 25,
        'city:name': 'John Smith',
        'city:isChildOf': {'@id': PRFX + '7b'}
    }],
    '@context': {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'xsd': 'http://www.w3.org/2001/XMLSchema#',
        'owl': 'http://www.w3.org/2002/07/owl#',
        'cuba': 'http://www.osp-core.com/cuba#',
        'city': 'http://www.osp-core.com/city#',
        'cuds': 'http://www.osp-core.com/cuds#'
    }
}


CUDS_LIST_PARTITIONED = [[
    {"@id": PRFX + "02",
     "@type": ["http://www.osp-core.com/city#Person"]},
    {"@id": PRFX + "01",
     "@type": ["http://www.osp-core.com/city#City"]},
    {"@id": PRFX + "03",
     "@type": ["http://www.osp-core.com/city#Person"]},
    {"@id": PRFX + "7b",
     "http://www.osp-core.com/city#name": [{"@value": "Peter"}],
     "http://www.osp-core.com/city#age": [{
         "@type": "http://www.w3.org/2001/XMLSchema#integer", "@value": "23"}],
     "@type": ["http://www.osp-core.com/city#Citizen"],
     "http://www.osp-core.com/city#INVERSE_OF_hasInhabitant": [
         {"@id": PRFX + "01"}],
     "http://www.osp-core.com/city#hasChild": [
         {"@id": PRFX + "02"},
         {"@id": PRFX + "03"}]}
], [
    {"@id": PRFX + "01",
     "http://www.osp-core.com/city#name": [{"@value": "Freiburg"}],
     "@type": ["http://www.osp-core.com/city#City"],
     "http://www.osp-core.com/city#coordinates": [{
         "@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2",
         "@value": "[0, 0]"}],
     "http://www.osp-core.com/city#hasInhabitant": [
         {"@id": PRFX + "7b"}]},
    {"@id": PRFX + "7b",
     "@type": ["http://www.osp-core.com/city#Citizen"]}
], [
    {"@id": PRFX + "02",
     "@type": ["http://www.osp-core.com/city#Person"],
     "http://www.osp-core.com/city#name": [{"@value": "John Smith"}],
     "http://www.osp-core.com/city#age": [{
         "@type": "http://www.w3.org/2001/XMLSchema#integer", "@value": "25"}],
     "http://www.osp-core.com/city#isChildOf": [{"@id": PRFX + "7b"}]},
    {"@id": PRFX + "7b",
     "@type": ["http://www.osp-core.com/city#Citizen"]}
], [
    {"@id": PRFX + "03",
     "@type": ["http://www.osp-core.com/city#Person"],
     "http://www.osp-core.com/city#name": [{"@value": "John Smith"}],
     "http://www.osp-core.com/city#age": [{
         "@type": "http://www.w3.org/2001/XMLSchema#integer", "@value": "25"}],
     "http://www.osp-core.com/city#isChildOf": [{"@id": PRFX + "7b"}]},
    {"@id": PRFX + "7b",
     "@type": ["http://www.osp-core.com/city#Citizen"]}
]]


ROOT_DICT = [{
    '@id': PRFX + "01",
    '@type': ['http://www.osp-core.com/city#City']
}, {
    '@id': PRFX + "2b",
    '@type': ['http://www.osp-core.com/city#CityWrapper'],
    'http://www.osp-core.com/city#hasPart': [
        {'@id': PRFX + "01"}],
}]

SERIALIZED_BUFFERS = {
    "added": [[
        {"@id": PRFX + "7b",
         "@type": ["http://www.osp-core.com/city#CityWrapper"]},
        {"@id": PRFX + "02",
         "http://www.osp-core.com/city#isPartOf": [
             {"@id": PRFX + "7b"}],
         "http://www.osp-core.com/city#coordinates": [
             {"@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2",
              "@value": "[0, 0]"}],  # TODO correct serialization of vector
         "http://www.osp-core.com/city#name": [{"@value": "Paris"}],
         "@type": ["http://www.osp-core.com/city#City"]}
    ]], "updated": [[
        {"@id": PRFX + "7b",
         "http://www.osp-core.com/city#hasPart": [{
             "@id": PRFX + "02"}],
         "@type": ["http://www.osp-core.com/city#CityWrapper"]},
        {"@id": PRFX + "02",
         "@type": ["http://www.osp-core.com/city#City"]}
    ]], "deleted": [[
        {"@id": PRFX + "01",
         "@type": ["http://www.osp-core.com/city#City"]}
    ]], "expired": [], "args": [42], "kwargs": {"name": "London"}}

SERIALIZED_BUFFERS_EXPIRED = deepcopy(SERIALIZED_BUFFERS)
SERIALIZED_BUFFERS_EXPIRED["expired"] = [
    {"UID": "00000000-0000-0000-0000-000000000003"}
]

SERIALIZED_BUFFERS2 = {
    "added": [[
        {"@id": PRFX + "2a",
         "http://www.osp-core.com/city#coordinates": [
             {"@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2",
              "@value": "[0, 0]"}],
         "http://www.osp-core.com/city#name": [{"@value": "London"}],
         "@type": ["http://www.osp-core.com/city#City"]}]],
    "updated": [], "deleted": [], "expired": []
}

SERIALIZED_BUFFERS3 = {
    "added": [[
        {"@id": PRFX + "01",
         "@type": ["http://www.osp-core.com/city#City"]},
        {"@id": PRFX + "02",
         "http://www.osp-core.com/city#age": [
             {"@type": "http://www.w3.org/2001/XMLSchema#integer",
              "@value": "12"}],
         "http://www.osp-core.com/city#INVERSE_OF_hasInhabitant": [
             {"@id": PRFX + "01"}],
         "http://www.osp-core.com/city#name": [{"@value": "Peter"}],
         "@type": ["http://www.osp-core.com/city#Citizen"]}]],
    "updated": [[
        {"@id": PRFX + "02",
         "@type": ["http://www.osp-core.com/city#Citizen"]},
        {"@id": PRFX + "01",
         "http://www.osp-core.com/city#hasInhabitant": [
             {"@id": PRFX + "02"}],
         "http://www.osp-core.com/city#isPartOf": [
             {"@id": PRFX + "03"}],
         "@type": ["http://www.osp-core.com/city#City"],
         "http://www.osp-core.com/city#name": [{"@value": "Freiburg"}],
         "http://www.osp-core.com/city#coordinates": [
             {"@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2",
              "@value": "[0, 0]"}]},
        {"@id": PRFX + "03",
         "@type": ["http://www.osp-core.com/city#CityWrapper"]}]],
    "deleted": [], "expired": [], "result": [[
        {"@id": PRFX + "02",
         "@type": ["http://www.osp-core.com/city#Citizen"]},
        {"@id": PRFX + "01",
         "http://www.osp-core.com/city#name": [{"@value": "Freiburg"}],
         "http://www.osp-core.com/city#hasInhabitant": [
             {"@id": PRFX + "02"}],
         "http://www.osp-core.com/city#coordinates": [
             {"@type": "http://www.osp-core.com/cuba#_datatypes/VECTOR-INT-2",
              "@value": "[0, 0]"}],
         "@type": ["http://www.osp-core.com/city#City"],
         "http://www.osp-core.com/city#isPartOf": [
             {"@id": PRFX + "03"}]},
        {"@id": PRFX + "03",
         "@type": ["http://www.osp-core.com/city#CityWrapper"]}
    ], [
        {"@id": PRFX + "01",
         "@type": ["http://www.osp-core.com/city#City"]},
        {"@id": PRFX + "03",
         "http://www.osp-core.com/city#hasPart": [
             {"@id": PRFX + "01"}],
         "@type": ["http://www.osp-core.com/city#CityWrapper"]}
    ]]}


INIT_DATA = {
    "args": [], "kwargs": {},
    "root": [{
        "@id": PRFX + "01",
        "@type": ["http://www.osp-core.com/city#CityWrapper"]}],
    "hashes": {}, "auth": None}


def jsonLdEqual(a, b):
    """Check if to JSON documents containing JSON LD are equal."""
    if (
        a and isinstance(a, list) and isinstance(a[0], dict)
            and "@id" in a[0]
    ) or (
        a and isinstance(a, dict) and "@graph" in a
    ):
        return isomorphic(json_to_rdf(a, rdflib.Graph()),
                          json_to_rdf(b, rdflib.Graph()))
    elif (
        a and isinstance(a, list) and isinstance(a[0], list)
            and isinstance(a[0][0], dict) and "@id" in a[0][0]
    ) or (
        a and isinstance(a, list) and isinstance(a[0], dict)
            and "@graph" in a[0]
    ):
        graph_a, graph_b = rdflib.Graph(), rdflib.Graph()
        for x in a:
            json_to_rdf(x, graph_a)
        for x in b:
            json_to_rdf(x, graph_b)
        return isomorphic(graph_a, graph_b)
    elif isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return all(jsonLdEqual(a[k], b[k]) for k in a.keys())
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return all(jsonLdEqual(aa, bb) for aa, bb in zip(a, b))
    else:
        return a == b


def assertJsonLdEqual(test_case, a, b):
    """Check if to JSON documents containing JSON LD are equal."""
    test_case.assertTrue(jsonLdEqual(a, b))


class TestCommunicationEngineSharedFunctions(unittest.TestCase):
    """Test functions used in the both parts of the communication engine."""

    def setUp(self):
        """Reset the session."""
        from osp.core.cuds import Cuds
        from osp.core.session import CoreSession
        Cuds._session = CoreSession()

    def testDeserialize(self):
        """Test transformation from normal dictionary to cuds."""
        with TestWrapperSession() as session:
            city.CityWrapper(session=session)
            cuds_objects = deserialize(CUDS_LIST_PARTITIONED, session,
                                       BufferContext.USER)
            self.assertEqual(len(cuds_objects), 4)
            self.assertEqual(set(map(lambda x: x.oclass, cuds_objects)),
                             {city.Person, city.City, city.Citizen})
            self.assertEqual(set(map(lambda x: x.uid.int,
                                     cuds_objects)),
                             {1, 2, 3, 123})

        with TestWrapperSession() as session:
            city.CityWrapper(session=session)
            cuds_object = deserialize(CUDS_DICT, session, BufferContext.USER)
            self.assertEqual(cuds_object.uid.int, 123)
            self.assertEqual(cuds_object.name, "Peter")
            self.assertEqual(cuds_object.age, 23)
            self.assertEqual(cuds_object.oclass, city.Citizen)
            self.assertEqual(set(cuds_object._neighbors.keys()),
                             {city.INVERSE_OF_hasInhabitant,
                              city.hasChild})
            self.assertEqual(
                cuds_object._neighbors[city.INVERSE_OF_hasInhabitant],
                {uuid.UUID(int=1): [city.City]})
            self.assertEqual(cuds_object._neighbors[city.hasChild],
                             {uuid.UUID(int=2): [city.Person],
                              uuid.UUID(int=3): [city.Person]})

            invalid_oclass = deepcopy(CUDS_DICT)
            invalid_oclass[-1]["@type"] = ["http://invalid.com/invalid"]
            self.assertRaises(TypeError, deserialize,
                              invalid_oclass, session, BufferContext.USER)

            self.assertEqual(deserialize(
                None, session, BufferContext.USER), None)
            self.assertEqual(
                deserialize([None, None], session, BufferContext.USER),
                [None, None])
            self.assertEqual(
                deserialize({"UID": "00000000-0000-0000-0000-000000000001"},
                            session, BufferContext.USER), uuid.UUID(int=1))
            self.assertEqual(
                deserialize(
                    [{"UID": "00000000-0000-0000-0000-000000000001"},
                     {"UID": "00000000-0000-0000-0000-000000000002"}],
                    session, BufferContext.USER),
                [uuid.UUID(int=1), uuid.UUID(int=2)])
            self.assertEqual(
                deserialize({"ENTITY": "city.Citizen"},
                            session, BufferContext.USER),
                city.Citizen
            )
            self.assertEqual(
                deserialize(
                    [{"ENTITY": "city.Citizen"}, {"ENTITY": "city.City"}],
                    session, BufferContext.USER),
                [city.Citizen, city.City]
            )
            self.assertEqual(
                deserialize([1, 1.2, "hallo"], session, BufferContext.USER),
                [1, 1.2, "hallo"]
            )

    def test_import_rdf(self):
        """Test the import rdf functionality."""
        with TestWrapperSession() as session:
            w = city.CityWrapper(session=session)
            g = json_to_rdf(CUDS_LIST_NON_PARTITIONED, rdflib.Graph())
            cuds_objects = import_rdf(g, session, BufferContext.USER)
            self.assertEqual(len(cuds_objects), 4)
            self.assertEqual(set(map(lambda x: x.oclass, cuds_objects)),
                             {city.Person, city.City, city.Citizen})
            self.assertEqual(set(map(lambda x: x.uid.int,
                                     cuds_objects)),
                             {1, 2, 3, 123})
            self.assertEqual(set(session._buffers[0][0]), {
                uuid.UUID(int=1), uuid.UUID(int=2), uuid.UUID(int=3),
                uuid.UUID(int=123), w.uid
            })
            self.assertEqual(session._buffers[0][1:], [{}, {}])
            self.assertEqual(session._buffers[1], [{}, {}, {}])

    def test_serializable(self):
        """Test function to make Cuds objects json serializable."""
        p = city.Citizen(age=23,
                         name="Peter",
                         uid=uuid.UUID(int=123))
        c = city.City(name="Freiburg", uid=uuid.UUID(int=1))
        c1 = city.Person(uid=uuid.UUID(int=2))
        c2 = city.Person(uid=uuid.UUID(int=3))
        p.add(c, rel=city.INVERSE_OF_hasInhabitant)
        p.add(c1, c2, rel=city.hasChild)
        assertJsonLdEqual(self, CUDS_DICT, serializable(p))
        assertJsonLdEqual(self, [CUDS_DICT], serializable([p]))
        assertJsonLdEqual(self, CUDS_LIST_PARTITIONED,
                          serializable([p, c, c1, c2]))
        assertJsonLdEqual(self, CUDS_LIST_NON_PARTITIONED,
                          serializable([p, c, c1, c2], partition_cuds=False))
        assertJsonLdEqual(self, CUDS_DICT,
                          serializable([p], partition_cuds=False))
        assertJsonLdEqual(self, None, serializable(None))
        assertJsonLdEqual(self, [None, None], serializable([None, None]))
        assertJsonLdEqual(
            self, {"UID": "00000000-0000-0000-0000-000000000001"},
            serializable(uuid.UUID(int=1))
        )
        assertJsonLdEqual(self, [
            {"UID": "00000000-0000-0000-0000-000000000001"},
            {"UID": "00000000-0000-0000-0000-000000000002"}],
            serializable([uuid.UUID(int=1), uuid.UUID(int=2)]))
        assertJsonLdEqual(self, {"ENTITY": "city.Citizen"},
                          serializable(city.Citizen))
        assertJsonLdEqual(self, [
            {"ENTITY": "city.Citizen"}, {"ENTITY": "city.City"}],
            serializable([city.Citizen, city.City]))
        assertJsonLdEqual(self, [1, 1.2, "hallo"],
                          serializable([1, 1.2, "hallo"]))

    def test_deserialize_buffers(self):
        """Test de-serialization of buffers."""
        # buffer context user
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            p1 = city.Citizen(uid=uuid.UUID(int=3))
            p2 = city.Citizen(uid=uuid.UUID(int=4))
            c.add(p1, p2, rel=city.hasInhabitant)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)
            s1.expire(p2)

            additional = deserialize_buffers(
                s1,
                buffer_context=BufferContext.USER,
                data=json.dumps(SERIALIZED_BUFFERS_EXPIRED)
            )
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=123), uuid.UUID(int=2),
                              uuid.UUID(int=3), uuid.UUID(int=4)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1._neighbors[city.hasPart],
                             {cn.uid: [city.City]})
            self.assertEqual(set(ws1._neighbors.keys()), {city.hasPart})
            self.assertEqual(cn._neighbors[city.isPartOf],
                             {ws1.uid: [city.CityWrapper]})
            self.assertEqual(set(cn._neighbors.keys()), {city.isPartOf})
            self.assertEqual(s1._expired, {uuid.UUID(int=3), uuid.UUID(int=4)})
            self.assertEqual(s1._buffers, [
                [{cn.uid: cn}, {ws1.uid: ws1},
                 {c.uid: c}],
                [dict(), dict(), dict()]])

        self.setUp()

        # buffer context engine
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            p1 = city.Citizen(uid=uuid.UUID(int=3))
            p2 = city.Citizen(uid=uuid.UUID(int=4))
            c.add(p1, p2, rel=city.hasInhabitant)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)
            s1.expire(p2)

            additional = deserialize_buffers(
                s1, buffer_context=BufferContext.ENGINE,
                data=json.dumps(SERIALIZED_BUFFERS_EXPIRED)
            )
            self.assertEqual(additional, {"args": [42],
                                          "kwargs": {"name": "London"}})
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [{cn.uid: cn}, {ws1.uid: ws1},
                 {c.uid: c}]])
            self.assertEqual(set(s1._registry.keys()),
                             {uuid.UUID(int=123), uuid.UUID(int=2),
                              uuid.UUID(int=3), uuid.UUID(int=4)})
            cn = ws1.get(uuid.UUID(int=2))
            self.assertEqual(cn.name, "Paris")
            self.assertEqual(ws1._neighbors[city.hasPart],
                             {cn.uid: [city.City]})
            self.assertEqual(set(ws1._neighbors.keys()), {city.hasPart})
            self.assertEqual(cn._neighbors[city.isPartOf],
                             {ws1.uid: [city.CityWrapper]})
            self.assertEqual(set(cn._neighbors.keys()), {city.isPartOf})
            self.assertEqual(s1._expired, {uuid.UUID(int=3), uuid.UUID(int=4)})
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [dict(), dict(), dict()]])

    def test_serialize_buffers(self):
        """Test if serialization of buffers works."""
        # no expiration
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            cn = city.City(name="Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            self.assertEqual(
                ('{"expired": [], "args": [42], "kwargs": {"name": "London"}}',
                 []),
                serialize_buffers(s1, buffer_context=None, additional_items={
                    "args": [42], "kwargs": {"name": "London"}})
            )
            added, updated, deleted = s1._buffers[BufferContext.USER]
            self.assertEqual(added.keys(), {uuid.UUID(int=2)})
            self.assertEqual(updated.keys(), {uuid.UUID(int=123)})
            self.assertEqual(deleted.keys(), {uuid.UUID(int=1)})
            self.assertEqual(s1._buffers[BufferContext.ENGINE],
                             [dict(), dict(), dict()])
            self.maxDiff = None
            result = serialize_buffers(
                s1, buffer_context=BufferContext.USER,
                additional_items={
                    "args": [42], "kwargs": {"name": "London"}
                }
            )
            assertJsonLdEqual(self, json.loads(result[0]), SERIALIZED_BUFFERS)
            self.assertEqual(result[1], [])
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [dict(), dict(), dict()]
            ])
            s1._expired = {uuid.UUID(int=123), uuid.UUID(int=2)}

        # with expiration
        with TestWrapperSession() as s1:
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            cn = city.City(name="Paris", uid=2)
            ws1.add(cn)
            ws1.remove(c.uid)
            s1.prune()
            s1._expired = {uuid.UUID(int=3)}
            self.assertEqual(
                ('{"expired": [{"UID": '
                 '"00000000-0000-0000-0000-000000000003"}], '
                 '"args": [42], "kwargs": {"name": "London"}}', []),
                serialize_buffers(
                    s1,
                    buffer_context=None,
                    additional_items={"args": [42],
                                      "kwargs": {"name": "London"}})
            )
            added, updated, deleted = s1._buffers[BufferContext.USER]
            self.assertEqual(added.keys(), {uuid.UUID(int=2)})
            self.assertEqual(updated.keys(), {uuid.UUID(int=123)})
            self.assertEqual(deleted.keys(), {uuid.UUID(int=1)})
            self.assertEqual(s1._buffers[BufferContext.ENGINE],
                             [dict(), dict(), dict()])

            self.maxDiff = 3000
            result = serialize_buffers(
                s1,
                buffer_context=BufferContext.USER,
                additional_items={"args": [42],
                                  "kwargs": {"name": "London"}})
            assertJsonLdEqual(
                self,
                SERIALIZED_BUFFERS_EXPIRED,
                json.loads(result[0])
            )
            self.assertEqual(
                [],
                result[1]
            )
            self.assertEqual(s1._buffers, [
                [dict(), dict(), dict()],
                [dict(), dict(), dict()]
            ])
            s1._expired = {uuid.UUID(int=123), uuid.UUID(int=2)}


class MockEngine():
    """A mock engine used for testing."""

    def __init__(self, on_send=None):
        """Initialize the MckEngine.

        Args:
            on_send (Callable[str, str, Any], optional): A function to call
                when send() is called.. Defaults to None.
        """
        self.on_send = on_send
        self.uri = None

    def send(self, command, data, files=None):
        """Save data and command, call on_send method.

        Args:
            command (str): The command to execute on the server side.
            data (str): The data to send
            files (List[str], optional): Paths to uploaded files.
                Defaults to None.

        Returns:
            Any: The results of the on_send method.
        """
        self._sent_command = command
        self._sent_data = data
        if self.on_send:
            return self.on_send(command, data)

    def close(self):
        """Close the Mock engine."""
        pass


class TestCommunicationEngineClient(unittest.TestCase):
    """Tests for the client side of communication engine."""

    def test_load(self):
        """Test loading from server."""
        client = TransportSessionClient(TestWrapperSession, None)
        client.root = 1
        c1 = create_recycle(
            oclass=city.City,
            kwargs={"name": "Freiburg"},
            uid=1,
            session=client,
            fix_neighbors=False
        )
        c2 = city.City(name="London", uid=2)
        c3 = create_recycle(
            oclass=city.City,
            kwargs={"name": "Paris"},
            uid=3,
            session=client,
            fix_neighbors=False
        )
        client._reset_buffers(BufferContext.USER)
        client.expire(c3.uid)

        def on_send(command, data):
            with EngineContext(client):
                create_from_cuds_object(c2, client)
                return [c2, None]

        client._engine = MockEngine(on_send)
        result = list(client.load(uuid.UUID(int=1),
                                  uuid.UUID(int=2),
                                  uuid.UUID(int=3)))
        self.assertEqual(client._engine._sent_command, LOAD_COMMAND)
        self.assertEqual(
            client._engine._sent_data,
            '{"expired": '
            '[{"UID": "00000000-0000-0000-0000-000000000003"}], '
            '"uids": '
            '[{"UID": "00000000-0000-0000-0000-000000000002"}, '
            '{"UID": "00000000-0000-0000-0000-000000000003"}]}')
        self.assertEqual(result, [c1, c2, None])
        self.assertEqual(set(client._registry.keys()), {c1.uid,
                                                        c2.uid})
        self.assertEqual(client._buffers, [
            [dict(), dict(), dict()],
            [dict(), dict(), dict()]
        ])
        client.close()

    def test_store(self):
        """Test storing of cuds_object."""
        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()

        # first item
        c1 = create_recycle(oclass=city.CityWrapper,
                            kwargs={},
                            uid=1,
                            session=client,
                            fix_neighbors=False)  # store will be called here
        self.assertEqual(client._engine._sent_command, INITIALIZE_COMMAND)
        assertJsonLdEqual(self, json.loads(client._engine._sent_data),
                          INIT_DATA)
        self.assertEqual(set(client._registry.keys()), {c1.uid})

        # second item
        client._engine._sent_data = None
        client._engine._sent_command = None
        c2 = create_recycle(
            oclass=city.City,
            kwargs={"name": "Freiburg"},
            uid=2,
            session=client,
            fix_neighbors=False
        )
        self.assertEqual(client._engine._sent_command, None)
        self.assertEqual(client._engine._sent_data, None)
        self.assertEqual(set(client._registry.keys()), {c1.uid,
                                                        c2.uid})
        client.close()

    def test_send(self):
        """Test sending data to the server."""
        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()
        client._send("command", True, "hello", bye="bye")
        self.assertEqual(client._engine._sent_command, "command")
        self.assertEqual(client._engine._sent_data, (
            '{"added": [], "updated": [], "deleted": [], "expired": [], '
            '"args": ["hello"], "kwargs": {"bye": "bye"}}'))
        client.close()

    def test_receive(self):
        """Test the receive method."""
        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()
        w = city.CityWrapper(session=client)
        self.assertRaises(RuntimeError, client._receive, "ERROR: Error!", None)
        client._receive(json.dumps(SERIALIZED_BUFFERS2), None)
        self.assertEqual(set(client._registry.keys()), {uuid.UUID(int=42),
                                                        w.uid})
        self.assertEqual(client._buffers[BufferContext.USER],
                         [dict(), dict(), dict()])
        self.assertEqual(
            list(map(dict.keys, client._buffers[BufferContext.ENGINE])),
            [set([uuid.UUID(int=42)]), set(), set()]
        )
        client.close()

    def test_getattr(self):
        """Test the __getatt__ magic method."""
        def command(*args, **kwargs):
            pass
        TestWrapperSession.command = consumes_buffers(command)

        client = TransportSessionClient(TestWrapperSession, None)
        client._engine = MockEngine()
        client.command("arg1", "arg2", kwarg="kwarg")
        self.assertEqual(client._engine._sent_command, "command")
        self.assertEqual(client._engine._sent_data, (
            '{"added": [], "updated": [], "deleted": [], "expired": [], '
            '"args": ["arg1", "arg2"], "kwargs": {"kwarg": "kwarg"}}'))
        self.assertRaises(AttributeError, getattr, client, "run")
        client.close()


class TestCommunicationEngineServer(unittest.TestCase):
    """Test the server side of the communication engine."""

    def setUp(self):
        """Reset the session."""
        from osp.core.cuds import Cuds
        from osp.core.session import CoreSession
        Cuds._session = CoreSession()

    def test_handle_disconnect(self):
        """Test the behavior when a user disconnects."""
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession() as s1:
            closed = False

            def close():
                nonlocal closed
                closed = True
            s1.close = close
            server.session_objs = {"1": s1, "2": 123}
            server.handle_disconnect("1")
            self.assertTrue(closed)
            self.assertEqual(server.session_objs, {"2": 123})

    def test_run_command(self):
        """Test to run a command."""
        correct = False

        # command to be executed
        def command(s, uid, name):
            nonlocal correct
            added = s._buffers[BufferContext.USER][BufferType.ADDED]
            correct = set(added.keys()) == {uuid.UUID(int=2)} and \
                added[uuid.UUID(int=2)].name == "Paris"
            s._reset_buffers(BufferContext.USER)

            added = s._buffers[BufferContext.ENGINE][BufferType.ADDED]
            added[uuid.UUID(int=uid)] = city.City(name=name, uid=uid)

        TestWrapperSession.command = consumes_buffers(command)
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession() as s1:

            # initialize buffers
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            # test the method
            server.session_objs = {"1": s1, "2": 123}
            result = server._run_command(json.dumps(SERIALIZED_BUFFERS),
                                         "command", "1")
            self.assertTrue(correct)
            self.assertEqual(json.loads(result[0]), SERIALIZED_BUFFERS2)
            self.assertEqual(result[1], [])

    def test_load_from_session(self):
        """Test loading from the remote side."""
        c = city.City(name="Freiburg", uid=1)
        with TestWrapperSession() as s1:
            w = city.CityWrapper(session=s1, uid=3)
            cw = w.add(c)

            with EngineContext(s1):
                p = city.Citizen(name="Peter", age=12, uid=2)
                cw.add(p, rel=city.hasInhabitant)
                server = TransportSessionServer(TestWrapperSession, None, None)
                server.session_objs["user"] = s1
                s1._expired |= {c.uid, w.uid}
                result = server._load_from_session(
                    '{"uids": [{"UID": 1}, '
                    '{"UID": 3}]}', "user")
            self.maxDiff = None
            assertJsonLdEqual(self, json.loads(result[0]), SERIALIZED_BUFFERS3)
            self.assertEqual(result[1], [])

    def test_init_session(self):
        """Test the initialization of the session on the remote side."""
        server = TransportSessionServer(TestWrapperSession, None, None)
        data = json.dumps({
            "args": [],
            "kwargs": {},
            "root": ROOT_DICT,
            "hashes": {"test.py": "123"}
        })
        server.com_facility._file_hashes = {"user1": {}}
        server._init_session(data, connection_id="user1")
        self.assertEqual(server.session_objs["user1"].root, uuid.UUID(int=43))
        self.assertEqual(len(server.session_objs.keys()), 1)

        data = json.dumps({
            "args": ["invalid"],
            "kwargs": {},
            "root": CUDS_DICT
        })
        self.assertRaises(TypeError, server._init_session, data,
                          connection_id="user1")

    def test_handle_request(self):
        """Test if error message is returned when invalid command is given."""
        def command(s, age, name):
            raise RuntimeError("Something went wrong: %s, %s" % (age, name))
        TestWrapperSession.command = command
        server = TransportSessionServer(TestWrapperSession, None, None)
        with TestWrapperSession() as s1:
            # initialize buffers
            ws1 = city.CityWrapper(session=s1, uid=123)
            c = city.City(name="Freiburg", uid=1)
            ws1.add(c)
            s1._reset_buffers(BufferContext.USER)

            # test
            server.session_objs["user1"] = s1
            self.assertEqual(server.handle_request(
                command="run", data=SERIALIZED_BUFFERS, connection_id="user1",
                temp_directory=None), ("ERROR: Invalid command", []))
            self.assertEqual(server.handle_request(
                command="command", data=json.dumps(SERIALIZED_BUFFERS),
                connection_id="user1",
                temp_directory=None),
                ("ERROR: RuntimeError: Something went wrong: 42, London", []))


if __name__ == '__main__':
    unittest.main()
