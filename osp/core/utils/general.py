import requests
import json
import rdflib
from osp.core.namespaces import cuba
from osp.core.session.buffers import BufferContext


def branch(cuds_object, *args, rel=None):
    """
    Like Cuds.add(), but returns the element you add to.
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


def get_rdf_graph(session=None):
    """EXPERIMENTAL
    Get the RDF Graph from a session.
    If no session is, the core session will be used.

    Args:
        session (Session, optional): The session to compute the RDF Graph of.
            Defaults to None.

    Returns:
        rdflib.Graph: The resulting rdf Graph
    """
    from osp.core.cuds import Cuds
    from osp.core import ONTOLOGY_NAMESPACE_REGISTRY
    session = session or Cuds._session
    graph = rdflib.Graph()
    for triple in session.get_triples():
        graph.add(triple)
    for namespace in ONTOLOGY_NAMESPACE_REGISTRY:
        for entity in namespace:
            for triple in entity.get_triples():
                graph.add(triple)
    return graph


def post(url, cuds_object, max_depth=float("inf")):
    """Will send the given CUDS object to the given URL. Will also send
    the CUDS object in the container recursively.

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


def deserialize(json_doc, session=None, buffer_context=BufferContext.USER):
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
        Any: The deserialized data. Can be CUDS.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.transport.transport_utils import deserialize \
        as _deserialize
    if isinstance(json_doc, str):
        json_doc = json.loads(json_doc)
    session = session or Cuds._session
    return _deserialize(
        json_obj=json_doc,
        session=session,
        buffer_context=buffer_context
    )


def remove_cuds_object(cuds_object):
    """
    Remove a cuds_object from the datastructure.
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
