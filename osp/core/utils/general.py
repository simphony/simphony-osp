"""A collection of utility method for osp-core.

These are potantially useful for every user of SimPhoNy.
"""

from typing import Optional
import logging
import requests
import json
from rdflib import OWL, RDF, RDFS, URIRef, Literal, Graph
import uuid
from osp.core.namespaces import cuba
from rdflib_jsonld.parser import to_rdf as json_to_rdf
from osp.core.ontology.datatypes import convert_from

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds#"
logger = logging.getLogger(__name__)


def branch(cuds_object, *args, rel=None):
    """Like Cuds.add(), but returns the element you add to.

    This makes it easier to create large CUDS structures.

    Args:
        cuds_object (Cuds): the object to add to.
        args (Cuds): object(s) to add
        rel (OntologyRelationship): class of the relationship between the
            objects.

    Raises:
        ValueError: adding an element already there.

    Returns:
        Cuds: The first argument.
    """
    cuds_object.add(*args, rel=rel)
    return cuds_object


def delete_cuds_object_recursively(cuds_object, rel=cuba.activeRelationship,
                                   max_depth=float("inf")):
    """Delete a cuds object  and all the object inside of the container of it.

    Args:
        cuds_object (Cuds): The CUDS object to recursively delete.
        rel (OntologyRelationship, optional): The relationship used for
            traversal. Defaults to cuba.activeRelationship.
        max_depth (int, optional):The maximum depth of the recursion.
            Defaults to float("inf"). Defaults to float("inf").
    """
    from osp.core.utils.simple_search import find_cuds_object
    cuds_objects = find_cuds_object(criterion=lambda x: True,
                                    root=cuds_object,
                                    rel=rel,
                                    find_all=True,
                                    max_depth=max_depth)
    for obj in cuds_objects:
        obj.session.delete_cuds_object(obj)


def serialize_rdf_graph(path, format="xml", session=None,
                        skip_custom_datatypes=False, skip_ontology=True,
                        skip_wrapper=True):
    """Serialize an RDF graph and take care of custom datatypes."""
    graph = get_rdf_graph(session, skip_custom_datatypes, skip_ontology)
    result = Graph()
    for s, p, o in graph:
        if isinstance(o, Literal):
            o = Literal(convert_from(o.toPython(), o.datatype),
                        datatype=o.datatype, lang=o.language)
        if not session or not skip_wrapper \
                or iri_from_uid(session.root) not in {s, o}:
            result.add((s, p, o))
    for prefix, iri in graph.namespaces():
        result.bind(prefix, iri)
    result.serialize(path, format)


def get_rdf_graph(session=None, skip_custom_datatypes=False,
                  skip_ontology=True):
    """Get the RDF Graph from a session.

    If no session is given, the core session will be used.

    Args:
        session (Session, optional): The session to compute the RDF Graph of.
            Defaults to None.
        skip_custom_datatypes (bool): Whether triples concerining custom
            datatypes should be skipped in export.
        skip_ontology (bool): Whether to have the ontology triples in the
            result graph.

    Returns:
        Graph: The resulting rdf Graph
    """
    from osp.core.session.session import Session
    if session is not None:
        if not isinstance(session, Session):
            raise TypeError(
                f"Invalid argument: {session}."
                f"Function can only be called on (sub)classes of {Session}."""
            )
    from osp.core.cuds import Cuds
    from osp.core.ontology.namespace_registry import namespace_registry
    session = session or Cuds._session
    result = session._get_full_graph()
    if not skip_ontology:
        result = result | namespace_registry._graph
        # The union includes namespace bindings.
    else:
        # Still bind the installed namespaces
        for prefix, iri in namespace_registry._graph.namespaces():
            result.bind(prefix, iri)
    if skip_custom_datatypes:
        return result - get_custom_datatype_triples()
    return result


def iri_from_uid(uid):
    """Transform an uid to an IRI.

    Args:
        uid (Union[UUID, URIRef]): The UUID to transform.

    Returns:
        URIRef: The IRI of the CUDS object with the given UUID.
    """
    if type(uid) is uuid.UUID:
        return URIRef(CUDS_IRI_PREFIX + str(uid))
    else:
        return uid


def uid_from_iri(iri):
    """Transform an IRI to an uid.

    Args:
        iri (URIRef): The IRI to transform.

    Returns:
        URIRef: The IRI of the CUDS object with the given uid.
    """
    if iri.startswith(CUDS_IRI_PREFIX):
        try:
            return uuid.UUID(hex=str(iri)[len(CUDS_IRI_PREFIX):])
        except ValueError as e:
            raise ValueError(f"Unable to transform {iri} to uid.") \
                from e
    else:
        return iri


def uid_from_general_iri(iri, graph, _visited=frozenset()):
    """Get a UUID from a general (not containing a UUID) IRI.

    Args:
        iri (UriRef): The IRI to convert to UUID.
        graph (Graph): The rdflib Graph to look for different IRIs for the
            same individual.
        _visited (Frozenset): Used for recursive calls.

    Returns:
        Tuple[UUID, URIRef]: The UUID and an IRI containing this UUID.
    """
    if str(iri).startswith(CUDS_IRI_PREFIX):
        return uid_from_iri(iri), iri

    for _, _, x in graph.triples((iri, OWL.sameAs, None)):
        if x not in _visited:
            return uid_from_general_iri(x, graph, _visited | {iri})
    for x, _, _ in graph.triples((None, OWL.sameAs, iri)):
        if x not in _visited:
            return uid_from_general_iri(x, graph, _visited | {iri})
    uid = uuid.uuid4()
    new_iri = iri_from_uid(uid)
    graph.add((iri, OWL.sameAs, new_iri))
    return uid, new_iri


def get_custom_datatypes():
    """Get the set of all custom datatypes used in the ontology.

    Custom datatypes are non standard ones, defined in the CUBA namespace.

    Returns:
        Set[IRI]: The set of IRI of custom datatypes.
    """
    from osp.core.ontology.cuba import rdflib_cuba
    from osp.core.ontology.namespace_registry import namespace_registry
    pattern = (None, RDF.type, RDFS.Datatype)
    result = set()
    for s, p, o in namespace_registry._graph.triples(pattern):
        if s in rdflib_cuba:
            result.add(s)
    return result


def get_custom_datatype_triples():
    """Get the set of triples in the ontology that include custom datatypes.

    Custom datatypes are non standard ones, defined in the CUBA namespace.

    Returns:
        Graph: A graph containing all the triples concerning custom
            datatypes.
    """
    custom_datatypes = get_custom_datatypes()
    from osp.core.ontology.namespace_registry import namespace_registry
    result = Graph()
    for d in custom_datatypes:
        result.add((d, RDF.type, RDFS.Datatype))
        pattern = (None, RDFS.range, d)
        for s, p, o in namespace_registry._graph.triples(pattern):
            result.add((s, p, o))
    return result


def post(url, cuds_object, rel=cuba.activeRelationship,
         max_depth=float("inf")):
    """Will send the given CUDS object to the given URL.

    Will also send the CUDS object in the container recursively.

    Args:
        url (string): The URL to send the CUDS object to
        cuds_object (Cuds): The CUDS to send
        max_depth (int, optional): The maximum depth to send CUDS objects
            recursively. Defaults to float("inf").

    Returns:
        Server response
    """
    serialized = serialize(cuds_object, max_depth=max_depth, rel=rel)
    return requests.post(url=url,
                         data=serialized,
                         headers={"content_type": "application/json"})


def serialize(cuds_object, rel=cuba.activeRelationship,
              max_depth=float("inf"), json_dumps=True):
    """Serialize a cuds objects and all of its contents recursively.

    Args:
        cuds_object (Cuds): The cuds object to serialize
        rel (OntologyRelationship, optional): The relationships to follow when
            serializing recursively. Defaults to cuba.activeRelationship.
        max_depth (int, optional): The maximum recursion depth.
            Defaults to float("inf").
        json_dumps (bool, optional): Whether to dump it to the registry.
            Defaults to True.

    Returns:
        Union[str, List]: The serialized cuds object.
    """
    from osp.core.session.transport.transport_utils import serializable
    from osp.core.utils import find_cuds_object
    cuds_objects = find_cuds_object(criterion=lambda _: True,
                                    root=cuds_object,
                                    rel=rel,
                                    find_all=True,
                                    max_depth=max_depth)
    result = serializable(cuds_objects, partition_cuds=False, mark_first=True)
    if json_dumps:
        return json.dumps(result)
    return result


def deserialize(json_doc, session=None, buffer_context=None):
    """Deserialize the given json objects (to CUDS).

    Will add the CUDS objects to the buffers.

    Args:
        json_doc (Union[str, dict]): the json document to load.
            Either string or already loaded json object.
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.
        buffer_context (BufferContext): Whether to add the objects to the
            buffers of the user or the engine. Default is equivalent of
            the user creating the CUDS objects by hand.

    Returns:
        Cuds: The deserialized Cuds.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.transport.transport_utils import import_rdf
    from osp.core.session.buffers import BufferContext
    from osp.core.ontology.cuba import rdflib_cuba
    if isinstance(json_doc, str):
        json_doc = json.loads(json_doc)
    session = session or Cuds._session
    buffer_context = buffer_context or BufferContext.USER
    g = json_to_rdf(json_doc, Graph())
    # only return first
    first = g.value(rdflib_cuba._serialization, RDF.first)
    first_uid = None
    if first:  # return the element marked as first later
        first_uid = uuid.UUID(hex=first)
        g.remove((rdflib_cuba._serialization, RDF.first, None))
    deserialized = import_rdf(
        graph=g,
        session=session,
        buffer_context=buffer_context,
        return_uid=first_uid
    )
    return deserialized


def import_rdf_file(path, format="xml", session=None, buffer_context=None):
    """Import rdf from file.

    Args:
        path (str): Path to the rdf file to import.
        format (str, optional): The file format of the file. Defaults to "xml".
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.
        buffer_context (BufferContext, optional): Whether to add the objects
            to the buffers of the user or the engine. Default is equivalent of
            the user creating the CUDS objects by hand.. Defaults to None.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.transport.transport_utils import import_rdf
    from osp.core.session.buffers import BufferContext
    g = Graph()
    g.parse(path, format=format)
    test_triples = [
        (None, RDF.type, OWL.Class),
        (None, RDF.type, OWL.DatatypeProperty),
        (None, RDF.type, OWL.ObjectProperty)
    ]
    if any(t in g for t in test_triples):
        raise ValueError("Data contains class or property definitions. "
                         "Please install ontologies using pico and use the "
                         "rdf import only for individuals!")
    onto_iri = g.value(None, RDF.type, OWL.Ontology)
    if onto_iri:
        g.remove((onto_iri, None, None))
    session = session or Cuds._session
    buffer_context = buffer_context or BufferContext.USER
    deserialized = import_rdf(
        graph=g,
        session=session,
        buffer_context=buffer_context
    )
    return deserialized


def remove_cuds_object(cuds_object):
    """Remove a cuds_object from the datastructure.

    Removes the relationships to all neighbors.
    To delete it from the registry you must call the
    sessions prune method afterwards.

    Args:
        cuds_object (Cuds): The cuds_object to remove.
    """
    # Method does not allow deletion of the root element of a container
    for elem in cuds_object.iter(rel=cuba.relationship):
        cuds_object.remove(elem.uid, rel=cuba.relationship)


def get_relationships_between(subj, obj):
    """Get the set of relationships between two cuds objects.

    Args:
        subj (Cuds): The subject
        obj (Cuds): The object

    Returns:
        Set[OntologyRelationship]: The set of relationships between subject
            and object.
    """
    result = set()
    for rel, obj_uids in subj._neighbors.items():
        if obj.uid in obj_uids:
            result.add(rel)
    return result


def sparql(query_string: str, session: Optional = None):
    """Performs a SPARQL query on a session (if supported by the session).

    Args:
        query_string (str): A string with the SPARQL query to perform.
        session (Session, optional): The session on which the SPARQL query
            will be performed. If no session is specified, then the current
            default session is used. This means that, when no session is
            specified, inside session `with` statements, the query will be
            performed on the session associated with such statement, while
            outside, it will be performed on the OSP-core default session,
            the core session.

    Returns:
        SparqlResult: A SparqlResult object, which can be iterated to obtain
            the output rows. Then for each `row`, the value for each query
            variable can be retrieved as follows: `row['variable']`.

    Raises:
        NotImplementedError: when the session does not support SPARQL queries.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.core_session import CoreSession
    session = session or Cuds._session
    try:
        return session.sparql(query_string)
    except AttributeError or NotImplementedError:
        raise NotImplementedError(f'The session {session} does not support'
                                  f' SPARQL queries.')
