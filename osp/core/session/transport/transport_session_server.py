# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import json
import logging
from osp.core.session.buffers import BufferContext
from osp.core.session.wrapper_session import WrapperSession
from osp.core.session.transport.communication_engine \
    import CommunicationEngineServer
from osp.core.session.transport.transport_utils import (
    INITIALISE_COMMAND, LOAD_COMMAND, deserialize, deserialize_buffers,
    serializable, serialize_buffers
)

logger = logging.getLogger(__name__)


class TransportSessionServer():
    """The TransportSession implements the transport layer. It consists of a
    client and a server. The server runs on the remote part and delegates each
    request to the session it wraps."""

    def __init__(self, session_cls, host, port,
                 session_kwargs=None, file_destination=None):
        """Construct the server.

        :param session_cls: The Session class to manage.
        :type session_cls: Type[Session]
        :param host: The hostname.
        :type host: str
        :param port: The port.
        :type port: int
        :param session_kwargs: Keyword arguments for the session.
            If None given, the user is allowed to specify them.
        :type session_kwargs: Dict[str, Any]
        :param file_destination: Destination of the uploaded files.
        :type session_kwargs: str
        """
        self.com_facility = CommunicationEngineServer(
            host=host,
            port=port,
            handle_request=self.handle_request,
            handle_disconnect=self.handle_disconnect
        )
        self.session_cls = session_cls
        self.session_objs = dict()
        self._session_kwargs = session_kwargs
        self._file_destination = file_destination
        if not (
            self._file_destination is None
            or os.path.exists(self._file_destination)
        ):
            os.mkdir(self._file_destination)

    def startListening(self):
        """Start the server"""
        self.com_facility.startListening()

    def handle_disconnect(self, user):
        """A user has disconnected. Close and delete his session

        :param user: The user that has disconnected.
        :type user: Hashable
        """
        if user in self.session_objs:
            self.session_objs[user].close()
            del self.session_objs[user]

    def handle_request(self, command, data, user, temp_directory=None):
        """Handle requests from the client.

        :param command: Kind of request / The command to execute.
        :type command: str
        :param data: The data sent by the client.
        :type data: str
        :return: The response for the client.
        :rtype: str
        """
        try:
            if command == INITIALISE_COMMAND:
                return self._init_session(data, user)
            elif command == LOAD_COMMAND:
                return self._load_from_session(data, user, temp_directory)
            elif (
                not command.startswith("_")
                and user in self.session_objs
                and hasattr(self.session_objs[user], command)
                and not hasattr(WrapperSession, command)
                and callable(getattr(self.session_objs[user], command))
            ):
                return self._run_command(data, command, user, temp_directory)
        except Exception as e:
            logger.error(str(e), exc_info=1)
            return ("ERROR: %s: %s" % (type(e).__name__, e), [])
        return ("ERROR: Invalid command", [])

    def _run_command(self, data, command, user, temp_directory=None):
        """Run a method of the session.

        :param data: The data of the client.
        :type data: str
        :param command: The method to execute.
        :type command: str
        :return: The buffers after the execution of the command, serialized.
        :rtype: str
        """
        session = self.session_objs[user]
        arguments = deserialize_buffers(
            session,
            buffer_context=BufferContext.USER,
            data=data,
            temp_directory=temp_directory,
            target_directory=self._file_destination
        )
        result = getattr(session, command)(*arguments["args"],
                                           **arguments["kwargs"])
        additional = {"result": result} if result else dict()
        return serialize_buffers(session, buffer_context=BufferContext.ENGINE,
                                 additional_items=additional)

    def _load_from_session(self, data, user, temp_directory=None):
        """Load cuds_objects from the session.

        :param data: The uids to load as json encoded list.
        :type data: str
        :return: The resulting cuds_objects, serialized.
        :rtype: str
        """
        session = self.session_objs[user]
        uids = deserialize_buffers(
            session,
            buffer_context=None,
            data=data,
            temp_directory=temp_directory,
            target_directory=self._file_destination
        )["uids"]
        cuds_objects = session.load(*uids)
        additional = {"result": [serializable(x) for x in cuds_objects]}
        return serialize_buffers(session, buffer_context=BufferContext.ENGINE,
                                 additional_items=additional)

    def _init_session(self, data, user):
        """Start a new session.

        :param data: The data sent by the user:
            serialized dict containing args, kwargs and root of new session.
        :type data: str
        :param user: The user who requests to start a new session
        :type user: Hashable
        :return: The buffers after the initialisation, serialized.
        :rtype: str
        """
        data = json.loads(data)
        if user in self.session_objs:
            self.session_objs[user].close()
        if self._session_kwargs and (data["args"] or data["kwargs"]):
            raise ValueError("This remote session cannot be parameterized by "
                             "the user. Only provide host and port and no "
                             "further arguments.")
        elif self._session_kwargs:
            session = self.session_cls(**self._session_kwargs)
        else:
            session = self.session_cls(*data["args"],
                                       **data["kwargs"])
        self.com_facility._file_hashes[user].update(data["hashes"])
        self.session_objs[user] = session
        deserialize(data["root"], session=session,
                    buffer_context=BufferContext.USER)
        return serialize_buffers(session, buffer_context=BufferContext.ENGINE)
