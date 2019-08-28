# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import inspect
from cuds.metatools.ontology_datatypes import convert_from, convert_to
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA
from cuds.classes.core.session.wrapper_session import WrapperSession
from cuds.classes.core.session.transport.communication_engine \
    import CommunicationEngineClient, CommunicationEngineServer

INITIALIZE_COMMAND = "_init"
LOAD_COMMAND = "_load"


class TransportSessionServer():
    def __init__(self, session_obj, host, port):
        self.com_facility = CommunicationEngineServer(
            host, port, self.handle_request
        )
        self.session_obj = session_obj
        self.session_obj._forbid_buffer_reset_by = "engine"

    def startListening(self):
        self.com_facility.startListening()

    def handle_request(self, path, data):
        if path == INITIALIZE_COMMAND:
            assert self.session_obj.root is None, "Session has already been initialized!"
            data = json.loads(data)
            entity = deserialize(data, self.session_obj)
            entity.session = self.session_obj
            self.session_obj.store(entity)
            del self.session_obj._added[entity.uid]
            self.session_obj._updated[entity.uid] = entity
            return serialize_buffers(self.session_obj)
        elif path == LOAD_COMMAND:
            uids = json.loads(data)
            uids = [convert_to(x, "UUID") for x in uids]
            return {"added": list(self.session_obj.load(*uids))}
        elif not path.startswith("_") and \
                hasattr(self.session_obj, path) and \
                callable(getattr(self.session_obj, path)):
            deserialize_buffers(self.session_obj, data)
            getattr(self.session_obj, path)()
            return serialize_buffers(self.session_obj)


class TransportSessionClient(WrapperSession):
    def __init__(self, session_cls, host, port):
        super().__init__(
            engine=CommunicationEngineClient(host, port, self._receive)
        )
        self.session_cls = session_cls

    # OVERRIDE
    def load(self, *uids):
        missing_uids = [str(uid) for uid in uids if uid not in self._registry]
        if missing_uids:
            self._engine.send(LOAD_COMMAND,
                              missing_uids)
        yield from super().load(*uids)

    # OVERRIDE
    def store(self, entity):
        if self.root is None:
            self.root = entity.uid
            self._engine.send(INITIALIZE_COMMAND,
                              json.dumps(serialize(entity)))
        super().store(entity)

    def _send(self, command):
        data = serialize_buffers(self)
        self._engine.send(command, data)

    def _receive(self, data):
        deserialize_buffers(self, data)
        self._reset_buffers(changed_by="engine")

    def __getattr__(self, attr):
        if not attr.startswith("_") and \
                hasattr(self.session_cls, attr) and \
                callable(getattr(self.session_cls, attr)):
            return lambda: self._send(attr)
        else:
            raise AttributeError("Unknown attribute %s" % attr)

    def __str__(self):
        return "TransportSessionClient connected to %s on %s:%s" % (
            self.session_cls, self.host, self.port
        )


def serialize_buffers(session_obj):
    result = {
        "added": [serialize(x) for x in session_obj._added.values()],
        "updated": [serialize(x) for x in session_obj._updated.values()],
        "deleted": [serialize(x) for x in session_obj._deleted.values()]
    }
    session_obj._reset_buffers(changed_by="user")
    return json.dumps(result)


def deserialize_buffers(session_obj, data):
    data = json.loads(data)
    added = [deserialize(x, session_obj) for x in data["added"]]
    updated = [deserialize(x, session_obj) for x in data["updated"]]
    deleted = [deserialize(x, session_obj) for x in data["deleted"]]
    session_obj._added = {x.uid: x for x in added}
    session_obj._updated = {x.uid: x for x in updated}
    session_obj._deleted = {x.uid: x for x in deleted}


def buffers_to_registry(session_obj):
    for entity in session_obj._added.values():
        entity.session = session_obj
        session_obj.store(entity)
    for entity in session_obj._updated.values():
        old_entity = next(session_obj.load(entity.uid))
        for attribute in entity.get_attributes(skip=["session", "uid"]):
            setattr(old_entity, attribute, getattr(entity, attribute))
        for rel, obj_dict in entity.items():
            old_entity[rel] = obj_dict
    for entity in session_obj._updated.values():
        if entity.uid in session_obj._registry:
            del session_obj._registry[entity.uid]


def serialize(entity):
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


def deserialize(json_obj, session_obj):
    cuba_key = CUBA(json_obj["cuba_key"])
    attributes = json_obj["attributes"]
    relationships = json_obj["relationships"]
    entity_cls = CUBA_MAPPING[cuba_key]
    if "session" in inspect.getfullargspec(entity_cls.__init__).args:
        attributes["session"] = session_obj
    entity = entity_cls(**attributes)

    for rel_cuba, obj_dict in relationships.items():
        rel = CUBA_MAPPING[CUBA(rel_cuba)]
        entity[rel] = dict()
        for uid, cuba_key in obj_dict.items():
            uid = convert_to(uid, "UUID")
            cuba_key = CUBA(cuba_key)
            entity[rel][uid] = cuba_key
    return entity
