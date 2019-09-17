# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import uuid
from cuds.utils import create_for_session
from cuds.classes.core.cuds import Cuds
from cuds.metatools.ontology_datatypes import convert_from, convert_to
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA

INITIALIZE_COMMAND = "_init"
LOAD_COMMAND = "_load"


def serialize(session_obj, consume_buffers=True, additional_items=None):
    """Serialize the buffers and additional items.

    :param session_obj: Serialize the buffers of this session object.
    :type session_obj: Session
    :param consume_buffers: Whether to consume and serialize the buffers
    :type consume_buffers: bool
    :param additional_items: Additional items to be added
        to the serialized json object, defaults to None
    :type additional_items: Dict[str, Any], optional
    :return: The serialized buffers
    :rtype: str
    """
    result = {
        "added": serializable(session_obj._added.values()),
        "updated": serializable(session_obj._updated.values()),
        "deleted": serializable(session_obj._deleted.values()),
    } if consume_buffers else dict()

    if hasattr(session_obj, "_expired"):
        result["expired"] = serializable(session_obj._expired)

    if additional_items is not None:
        result.update({k: serializable(v)
                       for k, v in additional_items.items()})
    if consume_buffers:
        session_obj._reset_buffers(changed_by="user")
    return json.dumps(result)


def deserialize_buffers(session_obj, data, reset_afterwards=False):
    """Deserialize serialized buffers, add them to the session and push them
    to the registry of the given session object.
    Returns the deserialization of everything but the buffers.

    :param session_obj: The session object to load the buffers into.
    :type session_obj: Session
    :param data: Serialized buffers
    :type data: str
    :return: Everything in data, that were not part of the buffers.
    :rtype: Dict[str, Any]
    """
    data = json.loads(data)

    if "expired" in data and hasattr(session_obj, "_expired"):
        session_obj._expired |= set(deserialize(data["expired"], session_obj))

    deserialized = {k: deserialize(v, session_obj) for k, v in data.items()}
    deleted = deserialized["deleted"] if "deleted" in deserialized else []

    if reset_afterwards:
        reset_buffers_after_deserialize(session_obj, deserialized)
    else:
        session_obj._deleted.update({x.uid: x for x in deleted})

    for entity in deleted:
        if entity.uid in session_obj._registry:
            del session_obj._registry[entity.uid]
    return {k: v for k, v in deserialized.items()
            if k not in ["added", "updated", "deleted", "expired"]}


def reset_buffers_after_deserialize(session_obj, deserialized):
    """Reset the buffers after deserialization.

    :param session_obj: The session object
    :type session_obj: Session
    :param deserialized: The deserialized data
    :type deserialized: Any
    """
    added = []
    for k, v in deserialized.items():
        if k != "deleted":
            if isinstance(v, Cuds):
                added.append(v)
            added += [x for x in v if isinstance(x, Cuds)]

    for uid in [x.uid for x in added]:
        if uid in session_obj._added:
            del session_obj._added[uid]
        if uid in session_obj._updated:
            del session_obj._updated[uid]


def deserialize(json_obj, session):
    """Deserialize a json object, instantiate the Cuds object in there.

    :param json_obj: The json object do deserialize.
    :type json_obj: Union[Dict, List, str, None]
    :param session: When creating a cuds object, use this session.
    :type session: Session
    :raises ValueError: The json object could not be deserialized.
    :return: The deserialized object
    :rtype: Union[Cuds, UUID, List[Cuds], List[UUID], None]
    """
    if json_obj is None:
        return None
    if isinstance(json_obj, (str, int, float)):
        return json_obj
    if isinstance(json_obj, list):
        return [deserialize(x, session) for x in json_obj]
    if isinstance(json_obj, dict) \
            and "cuba_key" in json_obj \
            and "attributes" in json_obj \
            and "relationships" in json_obj:
        return _to_cuds(json_obj, session)
    if isinstance(json_obj, dict) \
            and set(["UUID"]) == set(json_obj.keys()):
        return convert_to(json_obj["UUID"], "UUID")
    if isinstance(json_obj, dict) \
            and set(["CUBA-KEY"]) == set(json_obj.keys()):
        return CUBA(json_obj["CUBA-KEY"])
    if isinstance(json_obj, dict):
        return {k: deserialize(v, session) for k, v in json_obj.items()}
    raise ValueError("Could not deserialize %s." % json_obj)


def serializable(obj):
    """Make and entity, a list od entities,
    a uid or a list od uids json serializable.

    :param obj: The object to make serializable.
    :type obj: Union[Cuds, UUID, List[Cuds], List[UUID], None]
    :raises ValueError: Given object could not be made serializable
    :return: The serializable object.
    :rtype: Union[Dict, List, str, None]
    """
    if obj is None:
        return obj
    if isinstance(obj, (str, int, float)):
        return obj
    if isinstance(obj, uuid.UUID):
        return {"UUID": convert_from(obj, "UUID")}
    if isinstance(obj, CUBA):
        return {"CUBA-KEY": obj.value}
    if isinstance(obj, Cuds):
        return _serializable(obj)
    if isinstance(obj, dict):
        return {k: serializable(v) for k, v in obj.items()}
    try:
        return [serializable(x) for x in obj]
    except TypeError as e:
        raise ValueError("Could not serialize %s." % obj) \
            from e


def _serializable(entity):
    """Make an entity json serializable.

    :return: The entity to make serializable.
    :rtype: Cuds
    """
    result = {"cuba_key": str(entity.cuba_key.value),
              "attributes": dict(),
              "relationships": dict()}
    datatypes = entity.get_datatypes()
    attributes = entity.get_attributes(skip=["session"])
    for attribute in attributes:
        result["attributes"][attribute] = convert_from(
            getattr(entity, attribute),
            datatypes[attribute]
        )
    for rel in entity:
        result["relationships"][rel.cuba_key.value] = {
            convert_from(uid, "UUID"): str(cuba_key.value)
            for uid, cuba_key in entity[rel].items()
        }
    return result


def _to_cuds(json_obj, session):
    """Transform a json serializable dict to a cuds object

    :param json_obj: The json object to convert to a Cuds object
    :type json_obj: Dict[str, Any]
    :return: The resulting cuds object.
    :rtype: Cuds
    """
    cuba_key = CUBA(json_obj["cuba_key"])
    attributes = json_obj["attributes"]
    relationships = json_obj["relationships"]
    entity_cls = CUBA_MAPPING[cuba_key]
    entity = create_for_session(entity_cls, attributes, session)

    for rel_cuba, obj_dict in relationships.items():
        rel = CUBA_MAPPING[CUBA(rel_cuba)]
        entity[rel] = dict()
        for uid, cuba_key in obj_dict.items():
            uid = convert_to(uid, "UUID")
            cuba_key = CUBA(cuba_key)
            entity[rel][uid] = cuba_key
    return entity
