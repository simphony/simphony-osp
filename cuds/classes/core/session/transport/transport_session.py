# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import inspect
from cuds.utils import create_for_session
from cuds.classes.core.cuds import Cuds
from cuds.metatools.ontology_datatypes import convert_from, convert_to
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA
from cuds.classes.core.session.storage_wrapper_session \
    import StorageWrapperSession
from cuds.classes.core.session.transport.communication_engine \
    import CommunicationEngineClient, CommunicationEngineServer

INITIALIZE_COMMAND = "_init"
LOAD_COMMAND = "_load"


class TransportSessionServer():
    """The TransportSession implements the transport layer. It consists of a
    client and a server. The server runs on the remote part and delegates each
    request to the session it wraps."""

    def __init__(self, session_cls, host, port):
        """Construct the server.

        :param session_cls: The Session class to manage.
        :type session_cls: Type[Session]
        :param host: The hostname.
        :type host: str
        :param port: The port.
        :type port: int
        """
        self.com_facility = CommunicationEngineServer(
            host=host,
            port=port,
            handle_request=self.handle_request,
            handle_disconnect=self.handle_disconnect
        )
        self.session_cls = session_cls
        self.session_objs = dict()

    def startListening(self, forever=True):
        """Start the server"""
        self.com_facility.startListening(forever)

    def handle_disconnect(self, user):
        """A user has disconnected. Close and delete his session

        :param user: The user that has disconnected.
        :type user: Hashable
        """
        if user in self.session_objs:
            self.session_objs[user].close()
            del self.session_objs[user]

    def handle_request(self, command, data, user):
        """Handle requests from the client.

        :param command: Kind of request / The command to execute.
        :type command: str
        :param data: The data sent by the client.
        :type data: str
        :return: The response for the client.
        :rtype: str
        """
        if command == INITIALIZE_COMMAND:
            return self._init_session(data, user)
        elif command == LOAD_COMMAND:
            return self._load_from_session(data, user)
        elif not command.startswith("_") and \
                user in self.session_objs and \
                hasattr(self.session_objs[user], command) and \
                not hasattr(StorageWrapperSession, command) and \
                callable(getattr(self.session_objs[user], command)):
            try:
                return self._run_command(data, command, user)
            except Exception as e:
                return "ERROR: %s: %s" % (type(e).__name__, e)
        return "ERROR: Invalid command"

    def _run_command(self, data, command, user):
        """Run a method of the session.

        :param data: The data of the client.
        :type data: str
        :param command: The method to execute.
        :type command: str
        :return: The buffers after the execution of the command, serialized.
        :rtype: str
        """
        session = self.session_objs[user]
        arguments = deserialize_buffers(session, data)
        getattr(session, command)(*arguments["args"], **arguments["kwargs"])
        return serialize_buffers(session)

    def _load_from_session(self, data, user):
        """Load entities from the session.

        :param data: The uids to load as json encoded list.
        :type data: str
        :return: The resulting entities, serialized.
        :rtype: str
        """
        session = self.session_objs[user]
        uids = json.loads(data)
        uids = [convert_to(x, "UUID") for x in uids]
        entities = session.load(*uids)
        serialized = [serializable(x) for x in entities]
        return json.dumps({"added": serialized,
                           "deleted": [],
                           "updated": []})

    def _init_session(self, data, user):
        """Start a new session.

        :param data: The data sent by the user:
            serialized dict containing args, kwargs and root of new session.
        :type data: str
        :param user: The user who requests to start a new session
        :type user: Hashable
        :return: The buffers after the initialization, serialized.
        :rtype: str
        """
        data = json.loads(data)
        if user in self.session_objs:
            self.session_objs[user].close()
        data["kwargs"]["forbid_buffer_reset_by"] = "engine"
        session = self.session_cls(*data["args"],
                                   **data["kwargs"])
        self.session_objs[user] = session
        root = to_cuds(data["root"], session=session)
        session.store(root)
        del session._added[root.uid]
        session._updated[root.uid] = root
        return serialize_buffers(session)


class TransportSessionClient(StorageWrapperSession):
    """The TransportSession implements the transport layer. It consists of a
    client and a server. The client is a WrapperSession, that wraps another
    session that runs on the server. Each request will be sent to the server"""

    def __init__(self, session_cls, host, port, *args, **kwargs):
        """Construct the client of the transport session.

        :param session_cls: The session class to wrap.
        :type session_cls: Type[Session]
        :param host: The hostname.
        :type host: str
        :param port: The port.
        :type port: int
        """
        super().__init__(
            engine=CommunicationEngineClient(host, port, self._receive),
            forbid_buffer_reset_by=None
        )
        self.session_cls = session_cls
        self.args = args
        self.kwargs = kwargs

    # OVERRIDE
    def _load_cuds(self, uids):
        self._engine.send(LOAD_COMMAND, json.dumps(list(map(str, uids))))
        yield from super().load(*uids)

    # OVERRIDE
    def store(self, entity):
        # Initialize the server, when the first entity is stored.
        if self.root is None:
            data = {
                "args": self.args,
                "kwargs": self.kwargs,
                "root": serializable(entity)
            }
            super().store(entity)
            self._engine.send(INITIALIZE_COMMAND,
                              json.dumps(data))
            return
        super().store(entity)

    # OVERRIDE
    def close(self):
        self._engine.close()

    def _send(self, command, *args, **kwargs):
        """Send the buffers and a command to the server.

        :param command: The command to execute on the server
        :type command: str
        """
        arguments = {"args": args, "kwargs": kwargs}
        data = serialize_buffers(self, arguments)
        self._engine.send(command, data)

    def _receive(self, data):
        """Process the response of the server.

        :param data: Receive changes made by the server (serialized buffers).
        :type data: str
        :raises RuntimeError: Error occurred on the server side
        """
        if data.startswith("ERROR: "):
            raise RuntimeError("Error on Server side: %s" % data[7:])
        deserialize_buffers(self, data)
        self._reset_buffers(changed_by="engine")

    # OVERRIDE
    def __getattr__(self, attr):
        # Send each method call to the server.
        if not attr.startswith("_") and \
                hasattr(self.session_cls, attr) and \
                callable(getattr(self.session_cls, attr)):
            return lambda *args, **kwargs: self._send(attr, *args, **kwargs)
        else:
            raise AttributeError("Unknown attribute %s" % attr)

    # OVERRIDE
    def __str__(self):
        return "TransportSessionClient connected to %s on %s:%s" % (
            self.session_cls, self.host, self.port
        )


def serialize_buffers(session_obj, additional_items=None):
    """Serialize the buffers of a session using json.

    :param session_obj: Serialize the buffers of this session object.
    :type session_obj: Session
    :param additional_items: Additional items to be added
        to the serialized json object, defaults to None
    :type additional_items: Dict[str, Any], optional
    :return: The serialized buffers
    :rtype: str
    """
    result = {
        "added": [serializable(x) for x in session_obj._added.values()],
        "updated": [serializable(x) for x in session_obj._updated.values()],
        "deleted": [serializable(x) for x in session_obj._deleted.values()],
    }
    if additional_items is not None:
        result.update(additional_items)
    session_obj._reset_buffers(changed_by="user")
    return json.dumps(result)


def deserialize_buffers(session_obj, data):
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
    added = [to_cuds(x, session_obj) for x in data["added"]]
    updated = [to_cuds(x, session_obj) for x in data["updated"]]
    deleted = [to_cuds(x, session_obj) for x in data["deleted"]]
    session_obj._added = {x.uid: x for x in added}
    session_obj._updated = {x.uid: x for x in updated}
    session_obj._deleted = {x.uid: x for x in deleted}
    buffers_to_registry(session_obj)
    return {k: v for k, v in data.items()
            if k not in ["added", "updated", "deleted"]}


def buffers_to_registry(session_obj):
    """Push the buffers to the registry.

    :param session_obj: Push the buffers of this session object to the
        registry of this session object.
    :type session_obj: Type[Session]
    """
    for entity in session_obj._added.values():
        session_obj.store(entity)

    # do not replace to prevent users working with old objects
    for entity in session_obj._updated.values():
        try:
            old_entity = next(session_obj.load(entity.uid))
        except StopIteration:
            raise RuntimeError("Could not update entity with uid "
                               "%s on server. Not present." % entity.uid)
        for attribute in entity.get_attributes(skip=["session", "uid"]):
            setattr(old_entity, attribute, getattr(entity, attribute))
        for rel, obj_dict in entity.items():
            old_entity[rel] = obj_dict
    for entity in session_obj._deleted.values():
        if entity.uid in session_obj._registry:
            del session_obj._registry[entity.uid]


def serializable(entity):
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


def to_cuds(json_obj, session):
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
