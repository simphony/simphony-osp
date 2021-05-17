"""A collection of utility method for osp-core.

These are potentially useful for every user of SimPhoNy.
"""

from typing import Optional, Union, TextIO
import logging
import requests
import io
import pathlib
import json
import uuid
from rdflib import OWL, RDF, RDFS, URIRef, Literal, Graph
from rdflib_jsonld.parser import to_rdf as json_to_rdf
from osp.core.namespaces import cuba
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.datatypes import convert_from

__all__ = ['branch', 'get_relationships_between',
           'delete_cuds_object_recursively',
           'import_', 'export', 'post',
           'get_rdf_graph']

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds#"
logger = logging.getLogger(__name__)

# Private utilities (not user-facing)


def serialize_rdf_graph(format="xml", session=None,
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
    return result.serialize(format=format, encoding='UTF-8').decode('UTF-8')


def serialize_cuds_object_json(cuds_object, rel=cuba.activeRelationship,
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


def serialize_cuds_object_triples(cuds_object,
                                  rel=cuba.activeRelationship,
                                  max_depth=float("inf"),
                                  format: str = 'ttl'):
    """Serialize a CUDS object as triples.

    Args:
        cuds_object (Cuds): the cuds object to serialize.
        rel (OntologyRelationship): the ontology relationship to use as
            containment relationship.
        max_depth (float): the maximum depth to search for children CUDS
            objects.
        format (str): the format of the serialized triples.

    Returns:
        str: The CUDS object serialized as a RDF file.
    """
    from osp.core.ontology.namespace_registry import namespace_registry
    from osp.core.utils import find_cuds_object
    cuds_objects = find_cuds_object(criterion=lambda _: True,
                                    root=cuds_object,
                                    rel=rel,
                                    find_all=True,
                                    max_depth=max_depth)
    graph = Graph()
    for prefix, iri in namespace_registry._graph.namespaces():
        graph.bind(prefix, iri)
    for triple in (cuds.get_triples() for cuds in cuds_objects):
        graph.add(triple)
    return graph.serialize(format=format, encoding='UTF-8').decode('UTF-8')


def deserialize_cuds_object(json_doc, session=None, buffer_context=None):
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
        path (str): Contents of the rdf file to import.
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

# User-facing utilities


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
    cuds_objects = find_cuds_object(criterion=lambda x: True, root=cuds_object,
                                    rel=rel,
                                    find_all=True,
                                    max_depth=max_depth)
    for obj in cuds_objects:
        obj.session.delete_cuds_object(obj)


def import_(path: Optional[str] = None,
            file: Union[str, dict, TextIO] = None,
            session=None,
            format: str = None):
    """Imports CUDS in various formats.

    The supported formats types are:
    - (json) Serialized CUDS as json.
    - (xml) CUDS serialized as RDF triples in xml format.
    - (ttl) CUDS serialized as RDF triples in ttl format.

    Args:
        path (str, optional): path of the file to import.
        file (Union[str, dict, TextIO], optional): instead of giving a path, it
            is possible to give "the file" to the function directly. It can
            receive a string representing the contents of a file, a dictionary
            representing a json file, or a generic file-like object (opened
            in text mode).
        session (Session): the session in which the imported data will be
            stored.
        format (str, optional): the format of the content to import. See the
            supported file formats above.

    Returns (List[Cuds]): a list of cuds objects.

    """
    if not any(bool(x) for x in (path, file)):
        raise ValueError('Specify a path or a file (a file-like object, '
                         'a string, or a json document dictionary) '
                         'to read from.')
    elif sum(bool(x) for x in (path, file)) > 1:
        raise ValueError('Specify either a path or a file (a file-like object,'
                         ' a string, or a json document dictionary) '
                         'to read from.')
    elif format not in ('json', 'xml', 'ttl'):
        raise ValueError(f'Unsupported format {format}. The supported formats '
                         f'are: {", ".join(("json", "xml", "ttl"))}. '
                         f'Please check the docstring of this function for '
                         f'more information.')

    if path:
        if not pathlib.is_file(path):
            raise Exception(f'{path} is not a file.')
        with open(path, 'r') as file:
            contents = file.read()
            file_like = False
    elif file:
        if type(file) in (str, dict):
            if type(file) is dict and format != 'json':
                raise TypeError('Not a json document.')
            contents = file
            file_like = False
        else:
            if '__read__' not in file.__dir__():
                raise TypeError(f'{file} is not a file-like object.')
            contents = file
            file_like = True

    from osp.core.session import core_session
    session = session or core_session
    if format == 'json':
        results = deserialize_cuds_object(contents, session=session,
                                          buffer_context=None)
    elif format in ('xml', 'ttl'):
        results = import_rdf_file(contents if file_like
                                  else io.StringIO(contents),
                                  format=format, session=session,
                                  buffer_context=None)
    return results


def export(item,
           path: Optional[str],
           format: str = None,
           rel: OntologyRelationship = cuba.activeRelationship,
           max_depth: float = float("inf")) -> Union[str, None]:
    """Exports CUDS objects in a variety of formats.

    Args:
        item (Union[Cuds, Session]): the cuds object to serialize, or a session
            to serialize all of its CUDS objects.
        path (str, optional): a path to save the CUDS objects. If no path is
            specified, a string with the results will be
            returned instead.
        format(str): the target format.
        rel (OntologyRelationship): the ontology relationship to use as
            containment relationship when exporting
            CUDS.
        max_depth (float): maximum depth to search for children CUDS.
    """
    from osp.core.cuds import Cuds
    from osp.core.session import Session
    if not isinstance(item, (Cuds, Session)):
        raise ValueError('Specify either a CUDS object or a session to '
                         'be exported.')
    if format not in ('json', 'xml', 'ttl'):
        raise ValueError(f'Unsupported format {format}. The supported formats '
                         f'are: {", ".join(("json", "xml", "ttl"))}. '
                         f'Please check the docstring of this function for '
                         f'more information.')

    if type(item) is Cuds:
        if format == 'json':
            result = serialize_cuds_object_json(item, rel=rel,
                                                max_depth=max_depth,
                                                json_dumps=True)
        else:
            result = serialize_cuds_object_triples(item, rel=rel,
                                                   max_depth=max_depth,
                                                   format=format)
    elif type(item) is Session:
        result = serialize_rdf_graph(format=format, session=item,
                                     skip_custom_datatypes=False,
                                     skip_ontology=True,
                                     skip_wrapper=True)

    if path:
        if pathlib.Path(path).is_dir():
            raise ValueError(f'{path} is a directory.')
        with open(path, 'w+') as file:
            file.write(result)
        return None
    else:
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
    serialized = serialize_cuds_object_json(cuds_object, max_depth=max_depth,
                                            rel=rel)
    return requests.post(url=url,
                         data=serialized,
                         headers={"content_type": "application/json"})


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
    from osp.core.ontology.namespace_registry import namespace_registry
    from osp.core.cuds import Cuds
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
