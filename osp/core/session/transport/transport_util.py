# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import uuid
from osp.core import get_entity
from osp.core.utils import create_recycle
from osp.core.ontology.datatypes import convert_from, convert_to
from osp.core.ontology.entity import OntologyEntity
from osp.core.neighbour_dict import NeighbourDictTarget
from osp.core.session.buffers import get_buffer_context_mngr

INITIALISE_COMMAND = "_init"
LOAD_COMMAND = "_load"


def serialize_buffers(session_obj, buffer_context, additional_items=None):
    """Serialize the buffers and additional items.

    :param session_obj: Serialize the buffers of this session object.
    :type session_obj: Session
    :param buffer_context: Which buffers to serialize
    :type buffer_context: BufferContext
    :param additional_items: Additional items to be added
        to the serialized json object, defaults to None
    :type additional_items: Dict[str, Any], optional
    :return: The serialized buffers
    :rtype: str
    """
    result = dict()
    if buffer_context is not None:
        added, updated, deleted = session_obj._buffers[buffer_context]
        result = {
            "added": serializable(added.values()),
            "updated": serializable(updated.values()),
            "deleted": serializable(deleted.values()),
        }

    result["expired"] = serializable(session_obj._expired)

    if additional_items is not None:
        result.update({k: serializable(v)
                       for k, v in additional_items.items()})
    if buffer_context is not None:
        session_obj._reset_buffers(buffer_context)
    return json.dumps(result)


def deserialize_buffers(session_obj, buffer_context, data):
    """Deserialize serialized buffers, add them to the session and push them
    to the registry of the given session object.
    Returns the deserialization of everything but the buffers.

    :param session_obj: The session object to load the buffers into.
    :type session_obj: Session
    :param buffer_context: add the deserialized cuds objects to the
        selected buffers
    :type buffer_context: BufferContext
    :param data: Serialized buffers
    :type data: str
    :return: Everything in data, that were not part of the buffers.
    :rtype: Dict[str, Any]
    """
    with get_buffer_context_mngr(session_obj, buffer_context):
        data = json.loads(data)

        if "expired" in data:
            session_obj.expire(
                *set(deserialize(json_obj=data["expired"],
                                 session=session_obj,
                                 buffer_context=buffer_context))
            )

        deserialized = {k: deserialize(json_obj=v,
                                       session=session_obj,
                                       buffer_context=buffer_context)
                        for k, v in data.items()}
        deleted = deserialized["deleted"] if "deleted" in deserialized else []

        for x in deleted:
            session_obj._notify_delete(x)

        for cuds_object in deleted:
            if cuds_object.uid in session_obj._registry:
                del session_obj._registry[cuds_object.uid]
        return {k: v for k, v in deserialized.items()
                if k not in ["added", "updated", "deleted", "expired"]}


def deserialize(json_obj, session, buffer_context):
    """Deserialize a json object, instantiate the Cuds object in there.

    :param json_obj: The json object do deserialize.
    :type json_obj: Union[Dict, List, str, None]
    :param session: When creating a cuds_object, use this session.
    :type session: Session
    :param buffer_context: add the deserialized cuds objects to the
        selected buffers
    :type buffer_context: BufferContext
    :raises ValueError: The json object could not be deserialized.
    :return: The deserialized object
    :rtype: Union[Cuds, UUID, List[Cuds], List[UUID], None]
    """
    if json_obj is None:
        return None
    if isinstance(json_obj, (str, int, float)):
        return json_obj
    if isinstance(json_obj, list):
        return [deserialize(x, session, buffer_context) for x in json_obj]
    if isinstance(json_obj, dict) \
            and "oclass" in json_obj \
            and "uid" in json_obj \
            and "attributes" in json_obj \
            and "relationships" in json_obj:
        return _to_cuds_object(json_obj, session, buffer_context)
    if isinstance(json_obj, dict) \
            and set(["UUID"]) == set(json_obj.keys()):
        return convert_to(json_obj["UUID"], "UUID")
    if isinstance(json_obj, dict) \
            and set(["ENTITY"]) == set(json_obj.keys()):
        return get_entity(json_obj["ENTITY"])
    if isinstance(json_obj, dict):
        return {k: deserialize(v, session, buffer_context)
                for k, v in json_obj.items()}
    raise ValueError("Could not deserialize %s." % json_obj)


def serializable(obj):
    """Make a cuds_object, a list of cuds_objects,
    a uid or a list od uids json serializable.

    :param obj: The object to make serializable.
    :type obj: Union[Cuds, UUID, List[Cuds], List[UUID], None]
    :raises ValueError: Given object could not be made serializable
    :return: The serializable object.
    :rtype: Union[Dict, List, str, None]
    """
    from osp.core.cuds import Cuds
    if obj is None:
        return obj
    if isinstance(obj, (str, int, float)):
        return obj
    if isinstance(obj, uuid.UUID):
        return {"UUID": convert_from(obj, "UUID")}
    if isinstance(obj, OntologyEntity):
        return {"ENTITY": str(obj)}
    if isinstance(obj, Cuds):
        return _serializable(obj)
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    try:
        return [serializable(x) for x in obj]
    except TypeError as e:
        raise ValueError("Could not serialize %s." % obj) \
            from e


def _serializable(cuds_object):
    """Make a cuds_object json serializable.

    :return: The cuds_object to make serializable.
    :rtype: Cuds
    """
    result = {"oclass": str(cuds_object.oclass),
              "uid": convert_from(cuds_object.uid, "UUID"),
              "attributes": dict(),
              "relationships": dict()}
    attributes = cuds_object.oclass.attributes
    for attribute in attributes:
        result["attributes"][attribute.argname] = convert_from(
            getattr(cuds_object, attribute.argname),
            attribute.datatype
        )
    for rel in cuds_object._neighbours:
        result["relationships"][str(rel)] = {
            convert_from(uid, "UUID"): str(oclass)
            for uid, oclass in cuds_object._neighbours[rel].items()
        }
    return result


def _to_cuds_object(json_obj, session, buffer_context):
    """Transform a json serializable dict to a cuds_object

    :param json_obj: The json object to convert to a Cuds object
    :type json_obj: Dict[str, Any]
    :param session: The session to add the cuds object to.
    :type session: Session
    :param buffer_context: add the deserialized cuds objects to the
        selected buffers
    :type buffer_context: BufferContext
    :return: The resulting cuds_object.
    :rtype: Cuds
    """
    if buffer_context is None:
        raise ValueError("Not allowed to deserialize CUDS object "
                         "with undefined buffer_context")
    with get_buffer_context_mngr(session, buffer_context):
        oclass = get_entity(json_obj["oclass"])
        attributes = json_obj["attributes"]
        relationships = json_obj["relationships"]
        cuds_object = create_recycle(oclass=oclass,
                                     kwargs=attributes,
                                     session=session,
                                     uid=json_obj["uid"],
                                     fix_neighbours=False)

        for rel_name, obj_dict in relationships.items():
            rel = get_entity(rel_name)
            cuds_object._neighbours[rel] = NeighbourDictTarget(
                dictionary={}, cuds_object=cuds_object, rel=rel
            )
            for uid, target_name in obj_dict.items():
                uid = convert_to(uid, "UUID")
                target_oclass = get_entity(target_name)
                cuds_object._neighbours[rel][uid] = target_oclass
        return cuds_object
