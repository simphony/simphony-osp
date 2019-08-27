# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
from cuds.metatools.ontology_datatypes import convert_from, convert_to
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA
from cuds.classes.core.session.wrapper_session import WrapperSession
from cuds.classes.core.session.transport.communication_engine \
    import CommunicationEngineClient, CommunicationEngineServer


class TransportSessionServer():
    def __init__(self, session_obj, host, port):
        self.com_facility = CommunicationEngineServer(
            host, port, self.handle_request
        )
        self.session_obj = session_obj

    def startListening(self):
        self.com_facility.startListening()

    def handle_request(self, path, data):
        # TODO update registry
        self.session_obj._added = deserialize(data["added"])
        self.session_obj._updated = deserialize(data["updated"])
        self.session_obj._deleted = deserialize[data["deleted"]]
        if not path.startswith("_") and \
                hasattr(self.session_obj, path) and \
                callable(getattr(self.session_obj, path)):
            getattr(self.session_obj, path)()
            # TODO avoid buffer reset
            # TODO send updated objects back
            # TODO update registry
            # TODO reset buffers


class TransportSessionClient(WrapperSession):
    def __init__(self, session_cls, host, port):
        super().__init__(
            engine=CommunicationEngineClient(host, port, self._receive)
        )
        self.session_cls = session_cls

    def _send(self, command):
        data = dict()
        data["added"] = self._apply_added()
        data["updated"] = self._apply_updated()
        data["deleted"] = self._apply_deleted()
        self._engine.send(command, data)

    def _receive(self, data):
        # TODO update registry
        # TODO reset buffers
        pass

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

    def _apply_added(self):
        return [serialize(x) for x in self._added.values()]

    def _apply_updated(self):
        return [serialize(x) for x in self._updated.values()]

    def _apply_deleted(self):
        return [serialize(x) for x in self._deleted.values()]


def update_registry(added, updated, deleted, session_obj):
    pass


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
    return json.dumps(result)


def deserialize(json_string):
    json_obj = json.loads(json_string)
    cuba_key = CUBA(json_obj["cuba_key"])
    attributes = json_obj["attributes"]
    relationships = json_obj["relationships"]
    entity_cls = CUBA_MAPPING[cuba_key]
    entity = entity_cls(**attributes)

    for rel_cuba, obj_dict in relationships.items():
        rel = CUBA_MAPPING[CUBA(rel_cuba)]
        entity[rel] = dict()
        for uid, cuba_key in obj_dict.items():
            uid = convert_to(uid, "UUID")
            cuba_key = CUBA(cuba_key)
            entity[rel][uid] = cuba_key
    return entity
