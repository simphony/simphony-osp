"""The TransportSession implements the transport layer.

It consists of a
client and a server. The server runs on the remote part and delegates each
request to the session it wraps.
"""

import inspect
import json
import logging
import os

from osp.core.session.buffers import BufferContext
from osp.core.session.transport.communication_engine import (
    CommunicationEngineServer,
)
from osp.core.session.transport.transport_utils import (
    HANDSHAKE_COMMAND,
    INITIALIZE_COMMAND,
    LOAD_COMMAND,
    deserialize,
    deserialize_buffers,
    serialize_buffers,
)
from osp.core.session.wrapper_session import WrapperSession

logger = logging.getLogger(__name__)


class TransportSessionServer:
    """The TransportSession implements the transport layer.

    It consists of a
    client and a server. The server runs on the remote part and delegates each
    request to the session it wraps.
    """

    def __init__(
        self,
        session_cls,
        host,
        port,
        session_kwargs=None,
        file_destination=None,
        server_kwargs=None,
    ):
        """Construct the server.

        Args:
            session_cls (Type[Session]): The Session class to manage.
            host (str): The hostname.
            port (int): The port.
            session_kwargs (Dict[str, Any]): Keyword arguments for the session.
                If None given, the user is allowed to specify them.
            file_destination (str): Destination of the uploaded files.
            server_kwargs (Dict[tr, Any]): Will be passed to
                websockets.connect. E.g. it is possible to pass an SSL context
                with the ssl keyword.
        """
        self.com_facility = CommunicationEngineServer(
            host=host,
            port=port,
            handle_request=self.handle_request,
            handle_disconnect=self.handle_disconnect,
            **(server_kwargs or dict())
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
        """Start the server."""
        self.com_facility.startListening()

    def handle_disconnect(self, connection_id):
        """Handle the disconnect of a user. Close and delete his session.

        Args:
            connection_id (Hashable): The connection that has disconnected.
        """
        if connection_id in self.session_objs:
            self.session_objs[connection_id].close()
            del self.session_objs[connection_id]
        else:
            logger.warning(
                "User %s disconnected that was not associated with "
                "a session" % connection_id
            )

    def handle_request(
        self, command, data, connection_id, temp_directory=None
    ):
        """Handle requests from the client.

        Args:
            command (str): Kind of request / The command to execute.
            data (str): The data sent by the client.

        Returns:
            str: The response for the client.
        """
        try:
            if command == HANDSHAKE_COMMAND:
                return self._handshake(data, connection_id)
            elif command == INITIALIZE_COMMAND:
                return self._init_session(data, connection_id)
            elif command == LOAD_COMMAND:
                return self._load_from_session(
                    data, connection_id, temp_directory
                )
            elif (
                not command.startswith("_")
                and connection_id in self.session_objs
                and hasattr(self.session_objs[connection_id], command)
                and not hasattr(WrapperSession, command)
                and callable(
                    getattr(self.session_objs[connection_id], command)
                )
            ):
                return self._run_command(
                    data, command, connection_id, temp_directory
                )
        except Exception as e:
            logger.error(str(e), exc_info=1)
            return ("ERROR: %s: %s" % (type(e).__name__, e), [])
        return ("ERROR: Invalid command", [])

    def _run_command(self, data, command, connection_id, temp_directory=None):
        """Run a method of the session.

        Args:
            data (str): The data of the client.
            command (str): The method to execute.

        Returns:
            str: The buffers after the execution of the command, serialized.
        """
        session = self.session_objs[connection_id]
        arguments = deserialize_buffers(
            session,
            buffer_context=BufferContext.USER,
            data=data,
            temp_directory=temp_directory,
            target_directory=self._file_destination,
        )
        result = getattr(session, command)(
            *arguments["args"], **arguments["kwargs"]
        )
        additional = {"result": result} if result else dict()
        return serialize_buffers(
            session,
            buffer_context=BufferContext.ENGINE,
            additional_items=additional,
        )

    def _load_from_session(self, data, connection_id, temp_directory=None):
        """Load cuds_objects from the session.

        Args:
            data (str): The uids to load as json encoded list.

        Returns:
            str: The resulting cuds_objects, serialized.
        """
        session = self.session_objs[connection_id]
        uids = deserialize_buffers(
            session,
            buffer_context=None,
            data=data,
            temp_directory=temp_directory,
            target_directory=self._file_destination,
        )["uids"]
        cuds_objects = list(session.load(*uids))
        additional = {"result": cuds_objects}
        return serialize_buffers(
            session,
            buffer_context=BufferContext.ENGINE,
            additional_items=additional,
        )

    def _init_session(self, data, connection_id):
        """Start a new session.

        Args:
            data (str): The data sent by the user:
                serialized dict containing args, kwargs and root of new
                    session.
            connection_id (Hashable): The connection_id for the connection
                that requests to start a new session

        Returns:
            str: The buffers after the initialization, serialized.
        """
        data = json.loads(data)
        if connection_id in self.session_objs:
            self.session_objs[connection_id].close()
        user_kwargs = dict()
        argspec = inspect.getfullargspec(self.session_cls.__init__)
        args = argspec.kwonlyargs + argspec.args
        if "connection_id" in args:
            user_kwargs["connection_id"] = connection_id
        if "auth" in args:
            user_kwargs["auth"] = data["auth"]
        if self._session_kwargs and (data["args"] or data["kwargs"]):
            raise ValueError(
                "This remote session cannot be parameterized by "
                "the user. Only provide host and port and no "
                "further arguments."
            )
        elif self._session_kwargs:
            session = self.session_cls(**self._session_kwargs, **user_kwargs)
        else:
            session = self.session_cls(
                *data["args"], **data["kwargs"], **user_kwargs
            )
        self.com_facility._file_hashes[connection_id].update(data["hashes"])
        self.session_objs[connection_id] = session
        deserialize(
            data["root"], session=session, buffer_context=BufferContext.USER
        )
        return serialize_buffers(session, buffer_context=BufferContext.ENGINE)

    def _handshake(self, username, connection_id):
        return (
            json.dumps(
                {
                    "result": self.session_cls.handshake(
                        username=username, connection_id=connection_id
                    )
                }
            ),
            [],
        )
