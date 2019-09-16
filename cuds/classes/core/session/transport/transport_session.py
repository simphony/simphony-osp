# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import inspect
import uuid
import traceback
from cuds.utils import create_for_session
from cuds.classes.core.cuds import Cuds
from cuds.metatools.ontology_datatypes import convert_from, convert_to
from cuds.classes.generated.cuba_mapping import CUBA_MAPPING
from cuds.classes.generated.cuba import CUBA
from cuds.classes.core.session.storage_wrapper_session \
    import StorageWrapperSession
from cuds.classes.core.session.wrapper_session import check_consumes_buffers
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
                traceback.print_exc()
                print(e)
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
        result = getattr(session, command)(*arguments["args"],
                                           **arguments["kwargs"])
        additional = dict()
        if result:
            additional["result"] = result
        if hasattr(session, "_expired"):
            additional["expired"] = session._expired
        return serialize(session, additional_items=additional)

    def _load_from_session(self, data, user):
        """Load entities from the session.

        :param data: The uids to load as json encoded list.
        :type data: str
        :return: The resulting entities, serialized.
        :rtype: str
        """
        session = self.session_objs[user]
        uids = deserialize_buffers(session, data)["uids"]
        entities = session.load(*uids)
        serialized = [serializable(x) for x in entities]
        return json.dumps({"result": serialized,
                           "added": [],
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
        root = deserialize(data["root"], session=session)
        session.store(root)
        del session._added[root.uid]
        session._updated[root.uid] = root
        return serialize(session)


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
    def _load_cuds(self, uids, expired=None):
        expired = expired or self._expired
        data = serialize(self, False, {"uids": uids, "expired": expired})
        yield from self._engine.send(LOAD_COMMAND, data)

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

    def _send(self, command, consume_buffers, *args, **kwargs):
        """Send the buffers and a command to the server.

        :param command: The command to send
        :type command: str
        :param consume_buffers: Whether to send and consume the buffers
        :type consume_buffers: bool
        :param args: The arguments of the command.
        :type args: Serializable
        :param kwargs: The keyword arguments of the command.
        :type kwargs: Serializable.
        :return: The command's result.
        :rtype: Serializable
        """
        arguments = {"args": args, "kwargs": kwargs}
        data = serialize(self, consume_buffers, arguments)
        return self._engine.send(command, data)

    def _receive(self, data):
        """Process the response of the server.

        :param data: Receive changes made by the server (serialized buffers).
        :type data: str
        :raises RuntimeError: Error occurred on the server side
        """
        if data.startswith("ERROR: "):
            raise RuntimeError("Error on Server side: %s" % data[7:])
        remainder = deserialize_buffers(self, data, reset_afterwards=True)
        result = None
        if remainder and "expired" in remainder:
            self._expired |= set(remainder["expired"])
        if remainder and "result" in remainder:
            result = remainder["result"]
        return result

    # OVERRIDE
    def __getattr__(self, attr):
        # Send each method call to the server.
        if not attr.startswith("_") and \
                hasattr(self.session_cls, attr) and \
                callable(getattr(self.session_cls, attr)):
            consume_buffers = check_consumes_buffers(getattr(self.session_cls,
                                                             attr))
            return lambda *args, **kwargs: self._send(attr,
                                                      consume_buffers,
                                                      *args, **kwargs)
        else:
            raise AttributeError("Unknown attribute %s" % attr)

    # OVERRIDE
    def __str__(self):
        return "TransportSessionClient connected to %s on %s:%s" % (
            self.session_cls, self.host, self.port
        )


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

    if "added" in data:
        added = deserialize(data["added"], session_obj)
        updated = deserialize(data["updated"], session_obj)
        deleted = deserialize(data["deleted"], session_obj)

        if reset_afterwards:
            for uid in [x.uid for x in added + updated]:
                if uid in session_obj._added:
                    del session_obj._added[uid]
                if uid in session_obj._updated:
                    del session_obj._updated[uid]
        else:
            session_obj._deleted.update({x.uid: x for x in deleted})

        for entity in deleted:
            if entity.uid in session_obj._registry:
                del session_obj._registry[entity.uid]
    # TODO also reset stuff buffers after call below
    return {k: deserialize(v, session_obj) for k, v in data.items()
            if k not in ["added", "updated", "deleted", "expired"]}


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
