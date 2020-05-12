# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import requests
import json
import rdflib
from osp.core import CUBA


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
                                    rel=CUBA.ACTIVE_RELATIONSHIP,
                                    find_all=True,
                                    max_depth=max_depth)
    serialized = json.dumps(serializable(cuds_objects))
    return requests.post(url=url,
                         data=serialized,
                         headers={"content_type": "application/json"})


def deserialize(json_doc, session=None):
    """Deserialize the given json objects (to CUDS).
    Will add the CUDS objects to the buffers.

    Args:
        json_doc (Union[str, dict]): the json document to load.
            Either string or already loaded json object.
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.

    Returns:
        Any: The deserialized data. Can be CUDS.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.buffers import BufferContext
    from osp.core.session.transport.transport_utils import deserialize as x

    if isinstance(json_doc, str):
        json_doc = json.loads(json_doc)
    session = session or Cuds._session
    return x(
        json_obj=json_doc,
        session=session,  # The core session
        buffer_context=BufferContext.USER
    )


def remove_cuds_object(cuds_object):
    """
    Remove a cuds_object from the datastructure.
    Removes the relationships to all neighbours.
    To delete it from the registry you must call the
    sessions prune method afterwards.

    :param cuds_object: The cuds_object to remove.
    """
    # Method does not allow deletion of the root element of a container
    for elem in cuds_object.iter(rel=CUBA.RELATIONSHIP):
        cuds_object.remove(elem.uid, rel=CUBA.RELATIONSHIP)


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
    for rel, obj_uids in subj._neighbours.items():
        if obj.uid in obj_uids:
            result.add(rel)
    return result
