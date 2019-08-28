# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import inspect
from cuds.classes.core.cuds import Cuds
from cuds.metatools.ontology_datatypes import convert_from, convert_to
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA
from cuds.classes.core.session.wrapper_session import WrapperSession
from cuds.classes.core.session.transport.communication_engine \
    import CommunicationEngineClient, CommunicationEngineServer

INITIALIZE_COMMAND = "_init"
LOAD_COMMAND = "_load"


class TransportSessionServer():
    def __init__(self, session_cls, host, port):
        self.com_facility = CommunicationEngineServer(
            host, port, self.handle_request
        )
        self.session_cls = session_cls
        self.session_obj = None

    def startListening(self):
        self.com_facility.startListening()

    def handle_request(self, path, data):
        if path == INITIALIZE_COMMAND:
            return self._init_session(data)
        elif path == LOAD_COMMAND:
            return self._load_from_session(data)
        elif not path.startswith("_") and \
                hasattr(self.session_obj, path) and \
                callable(getattr(self.session_obj, path)):
            try:
                return self._run_command(data, path)
            except Exception as e:
                return "ERROR: " + str(e)

    def _run_command(self, data, command):
        deserialize_buffers(self.session_obj, data)
        getattr(self.session_obj, command)()
        return serialize_buffers(self.session_obj)

    def _load_from_session(self, data):
        uids = json.loads(data)
        uids = [convert_to(x, "UUID") for x in uids]
        entities = self.session_obj.load(*uids)
        serialized = [serialize(x) for x in entities]
        return json.dumps({"added": serialized,
                           "deleted": [],
                           "updated": []})

    def _init_session(self, data):
        data = json.loads(data)
        if self.session_obj:
            self.session_obj.close()
        data["kwargs"]["forbid_buffer_reset_by"] = "engine"
        self.session_obj = self.session_cls(*data["args"],
                                            **data["kwargs"])

        root = deserialize(data["root"])
        root.session = self.session_obj
        self.session_obj.store(root)
        del self.session_obj._added[root.uid]
        self.session_obj._updated[root.uid] = root
        return serialize_buffers(self.session_obj)


class TransportSessionClient(WrapperSession):
    def __init__(self, session_cls, host, port, *args, **kwargs):
        super().__init__(
            engine=CommunicationEngineClient(host, port, self._receive),
            forbid_buffer_reset_by=None
        )
        self.session_cls = session_cls
        self.args = args
        self.kwargs = kwargs

    # OVERRIDE
    def load(self, *uids):
        missing_uids = [str(uid) for uid in uids if uid not in self._registry]
        if missing_uids:
            self._engine.send(LOAD_COMMAND,
                              json.dumps(missing_uids))
        yield from super().load(*uids)

    # OVERRIDE
    def store(self, entity):
        if self.root is None:
            data = {
                "args": self.args,
                "kwargs": self.kwargs,
                "root": serialize(entity)
            }
            super().store(entity)
            self._engine.send(INITIALIZE_COMMAND,
                              json.dumps(data))
            return
        super().store(entity)

    def _send(self, command):
        data = serialize_buffers(self)
        self._engine.send(command, data)

    def _receive(self, data):
        if data.startswith("ERROR: "):
            raise RuntimeError("Error on Server side: %s" % data[7:])
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
    added = [deserialize(x) for x in data["added"]]
    updated = [deserialize(x) for x in data["updated"]]
    deleted = [deserialize(x) for x in data["deleted"]]
    session_obj._added = {x.uid: x for x in added}
    session_obj._updated = {x.uid: x for x in updated}
    session_obj._deleted = {x.uid: x for x in deleted}
    buffers_to_registry(session_obj)


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
    for entity in session_obj._deleted.values():
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


def deserialize(json_obj):
    cuba_key = CUBA(json_obj["cuba_key"])
    attributes = json_obj["attributes"]
    relationships = json_obj["relationships"]
    entity_cls = CUBA_MAPPING[cuba_key]
    if "session" in inspect.getfullargspec(entity_cls.__init__).args:
        attributes["session"] = Cuds.session
    entity = entity_cls(**attributes)

    for rel_cuba, obj_dict in relationships.items():
        rel = CUBA_MAPPING[CUBA(rel_cuba)]
        entity[rel] = dict()
        for uid, cuba_key in obj_dict.items():
            uid = convert_to(uid, "UUID")
            cuba_key = CUBA(cuba_key)
            entity[rel][uid] = cuba_key
    return entity
