"""A collection of utility method for osp-core.

These are potantially useful for every user of SimPhoNy.
"""

import requests
import json
import rdflib
import uuid
from osp.core.namespaces import cuba

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds/#"


def branch(cuds_object, *args, rel=None):
    """Like Cuds.add(), but returns the element you add to.

    This makes it easier to create large CUDS structures.

    :param cuds_object: the object to add to
    :type cuds_object: Cuds
    :param args: object(s) to add
    :type args: Cuds
    :param rel: class of the relationship between the objects
    :type rel: OntologyRelationship
    :return: The first argument
    :rtype: Cuds
    :raises ValueError: adding an element already there
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


def get_rdf_graph(session=None, skip_custom_datatypes=False):
    """EXPERIMENTAL.

    Get the RDF Graph from a session.
    If no session is, the core session will be used.

    Args:
        session (Session, optional): The session to compute the RDF Graph of.
            Defaults to None.
        skip_custom_datatypes (bool): Whether triples concerining custom
            datatypes should be skipped in export.

    Returns:
        rdflib.Graph: The resulting rdf Graph
    """
    from osp.core.session.session import Session
    if session is not None:
        if not isinstance(session, Session):
            raise TypeError(
                f"Invalid argument: {session}."
                f"Function can only be called on (sub)classes of {Session}."""
            )
    from osp.core.cuds import Cuds
    from osp.core.namespaces import _namespace_registry
    session = session or Cuds._session
    cuds_graph = rdflib.Graph()
    for triple in session.get_triples():
        cuds_graph.add(triple)
    result = cuds_graph + _namespace_registry._graph
    if skip_custom_datatypes:
        return result - get_custom_datatype_triples()
    return result


def iri_from_uid(uid):
    """Transform a UUID to an IRI.

    Args:
        uid (UUID): The UUID to transform.

    Returns:
        URIRef: The IRI of the CUDS object with the given UUID.
    """
    return rdflib.URIRef(CUDS_IRI_PREFIX + str(uid))


def uid_from_iri(iri):
    """Transform an IRI to a UUID.

    Args:
        uid (UUID): The UUID to transform.

    Returns:
        URIRef: The IRI of the CUDS object with the given UUID.
    """
    return uuid.UUID(hex=str(iri)[len(CUDS_IRI_PREFIX):])


def get_custom_datatypes():
    """Get the set of all custom datatypes used in the ontology.

    Custom datatypes are non standard ones, defined in the CUBA namespace.

    Returns:
        Set[rdflib.IRI]: The set of IRI of custom datatypes.
    """
    from osp.core.ontology.cuba import rdflib_cuba
    from osp.core.namespaces import _namespace_registry
    pattern = (None, rdflib.RDF.type, rdflib.RDFS.Datatype)
    result = set()
    for s, p, o in _namespace_registry._graph.triples(pattern):
        if s in rdflib_cuba:
            result.add(s)
    return result


def get_custom_datatype_triples():
    """Get the set of triples in the ontology that include custom datatypes.

    Custom datatypes are non standard ones, defined in the CUBA namespace.

    Returns:
        rdflib.Graph: A graph containing all the triples concerning custom
            datatypes.
    """
    custom_datatypes = get_custom_datatypes()
    from osp.core.namespaces import _namespace_registry
    result = rdflib.Graph()
    for d in custom_datatypes:
        result.add((d, rdflib.RDF.type, rdflib.RDFS.Datatype))
        pattern = (None, rdflib.RDFS.range, d)
        for s, p, o in _namespace_registry._graph.triples(pattern):
            result.add((s, p, o))
    return result


def post(url, cuds_object, max_depth=float("inf")):
    """Will send the given CUDS object to the given URL.

    Will also send the CUDS object in the container recursively.

    Args:
        url (string): The URL to send the CUDS object to
        cuds_object (Cuds): The CUDS to send
        max_depth (int, optional): The maximum depth to send CUDS objects
            recursively. Defaults to float("inf").

    Returns:
        [type]: [description]
    """
    from osp.core.utils import find_cuds_object
    from osp.core.session.transport.transport_utils import serializable
    cuds_objects = find_cuds_object(criterion=lambda x: True,
                                    root=cuds_object,
                                    rel=cuba.activeRelationship,
                                    find_all=True,
                                    max_depth=max_depth)
    serialized = json.dumps(serializable(cuds_objects))
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
    cuds_objects = find_cuds_object(criterion=lambda x: True,
                                    root=cuds_object,
                                    rel=rel,
                                    find_all=True,
                                    max_depth=max_depth)
    result = serializable(cuds_objects)
    if json_dumps:
        return json.dumps(result)
    return result


def deserialize(json_doc, session=None, buffer_context=None,
                only_return_first_element=True):
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
        only_return_first_element (bool): When the json doc is a list,
            whether to return only the first element. The reason
            for this is that the result of serializing a single cuds
            object using `serialize()` is a list. Having this flag set to True,
            the result of deserializing this list will be the input
            CUDS object of serialize, as expected.

    Returns:
        Any: The deserialized data. Can be CUDS.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.transport.transport_utils import deserialize \
        as _deserialize
    from osp.core.session.buffers import BufferContext
    if isinstance(json_doc, str):
        json_doc = json.loads(json_doc)
    session = session or Cuds._session
    buffer_context = buffer_context or BufferContext.USER
    deserialized = _deserialize(
        json_obj=json_doc,
        session=session,
        buffer_context=buffer_context
    )
    if isinstance(deserialized, list) and only_return_first_element:
        return deserialized[0]
    return deserialized


def remove_cuds_object(cuds_object):
    """Remove a cuds_object from the datastructure.

    Removes the relationships to all neighbors.
    To delete it from the registry you must call the
    sessions prune method afterwards.

    :param cuds_object: The cuds_object to remove.
    """
    # Method does not allow deletion of the root element of a container
    for elem in cuds_object.iter(rel=cuba.relationship):
        cuds_object.remove(elem.uid, rel=cuba.relationship)


def get_relationships_between(subj, obj):
    """Get the set of relationships between two cuds objects.

    :param subj: The subject
    :type subj: Cuds
    :param obj: The object
    :type obj: Cuds
    :return: The set of relationships between subject and object.
    :rtype: Set[Type[Relationship]]
    """
    result = set()
    for rel, obj_uids in subj._neighbors.items():
        if obj.uid in obj_uids:
            result.add(rel)
    return result
