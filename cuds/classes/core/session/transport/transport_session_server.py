# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
import traceback
from cuds.classes.core.session.storage_wrapper_session \
    import StorageWrapperSession
from cuds.classes.core.session.transport.communication_engine \
    import CommunicationEngineServer
from cuds.classes.core.session.transport.transport_util import (
    INITIALIZE_COMMAND, LOAD_COMMAND, deserialize, deserialize_buffers,
    serializable, serialize
)


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
        session._uids_in_registry_after_last_buffer_reset = set([root.uid])
        del session._added[root.uid]
        session._updated[root.uid] = root
        return serialize(session)
