"""The TransportSession implements the transport layer.

It consists of a
client and a server. The client is a WrapperSession, that wraps another
session that runs on the server. Each request will be sent to the server
"""

import json
import logging
import os
import tempfile
import urllib.parse

from osp.core.namespaces import cuba
from osp.core.session.buffers import BufferContext, BufferType
from osp.core.session.transport.communication_engine import (
    CommunicationEngineClient,
)
from osp.core.session.transport.transport_utils import (
    HANDSHAKE_COMMAND,
    INITIALIZE_COMMAND,
    LOAD_COMMAND,
    deserialize_buffers,
    get_hash_dir,
    serializable,
    serialize_buffers,
)
from osp.core.session.wrapper_session import (
    WrapperSession,
    check_consumes_buffers,
)

logger = logging.getLogger(__name__)


class TransportSessionClient(WrapperSession):
    """The TransportSession implements the transport layer.

    It consists of a
    client and a server. The client is a WrapperSession, that wraps another
    session that runs on the server. Each request will be sent to the server
    """

    def __init__(
        self,
        session_cls,
        uri,
        file_destination=None,
        connect_kwargs=None,
        file_uid=False,
        *args,
        **kwargs
    ):
        """Construct the client of the transport session.

        Args:
            session_cls (Session): The session class to wrap.
            uri (str): WebSocket URI.
            file_destination (path): Where to put the uploaded files.
            file_uid (bool): Whether to prepend the files with the uid of
                their associated CUDS object.
            connect_kwargs (dict[str, Any]): Will be passed to
                websockets.connect. E.g. it is possible to pass an SSL context
                with the ssl keyword.
            kwargs (dict[str, Any]): Will be passed to the creation of the
                session object.
        """
        self.session_cls = session_cls
        self.args = args
        self.kwargs = kwargs
        self.file_uid = file_uid
        uri, username, password = self._parse_uri(uri)
        if file_destination is None:
            self.__local_temp_dir = tempfile.TemporaryDirectory()
            self._file_destination = self.__local_temp_dir.name
        else:
            self.__local_temp_dir = None
            self._file_destination = file_destination
            if not os.path.exists(self._file_destination):
                os.mkdir(self._file_destination)
        super().__init__(
            engine=CommunicationEngineClient(
                uri=uri,
                handle_response=self._receive,
                **(connect_kwargs or dict())
            )
        )
        self.auth = None
        if uri is not None:
            handshake = self._engine.send(HANDSHAKE_COMMAND, username or "")
            self.auth = self.session_cls.compute_auth(
                username, password, handshake
            )

    # OVERRIDE
    def _store(self, cuds_object):
        # Initialize the server, when the first cuds_object is stored.
        if self.root is None:
            data = {
                "args": self.args,
                "kwargs": self.kwargs,
                "root": serializable(cuds_object),
                "hashes": get_hash_dir(self._file_destination),
                "auth": self.auth,
            }
            super()._store(cuds_object)
            self._engine.send(INITIALIZE_COMMAND, json.dumps(data))
            if not cuds_object.is_a(cuba.Wrapper):
                logger.debug(
                    "Remove %s from added buffer in context %s of "
                    "session %s" % (cuds_object, self._current_context, self)
                )
                del self._buffers[self._current_context][BufferType.ADDED][
                    cuds_object.uid
                ]
            return
        super()._store(cuds_object)

    # OVERRIDE
    def close(self):
        """Remove the temporary directory and close the connection."""
        if self.__local_temp_dir:
            self.__local_temp_dir.cleanup()
        self._engine.close()

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        expired = expired or self._expired
        data, files = serialize_buffers(
            self,
            buffer_context=None,
            additional_items={"uids": uids, "expired": expired},
            target_directory=self._file_destination,
            file_cuds_uid=self.file_uid,
        )
        yield from self._engine.send(LOAD_COMMAND, data, files)

    def _send(self, command, consume_buffers, *args, **kwargs):
        """Send the buffers and a command to the server.

        Args:
            command (str): The command to send
            consume_buffers (bool): Whether to send and consume the buffers
            args (Serializable): The arguments of the command.
            kwargs (Serializable): The keyword arguments of the command.

        Returns:
            Serializable: The command's result.
        """
        arguments = {"args": args, "kwargs": kwargs}
        buffer_context = BufferContext.USER if consume_buffers else None
        data, files = serialize_buffers(
            self,
            buffer_context=buffer_context,
            additional_items=arguments,
            target_directory=self._file_destination,
            file_cuds_uid=self.file_uid,
        )
        return self._engine.send(command, data, files)

    def _receive(self, data, temp_directory):
        """Process the response of the server.

        Args:
            data (str): Receive changes made by the server
                (serialized buffers).

        Raises:
            RuntimeError: Error occurred on the server side
        """
        if data.startswith("ERROR: "):
            raise RuntimeError("Error on Server side: %s" % data[7:])
        remainder = deserialize_buffers(
            self,
            buffer_context=BufferContext.ENGINE,
            data=data,
            temp_directory=temp_directory,
            target_directory=self._file_destination,
            file_cuds_uid=self.file_uid,
        )
        result = None
        if remainder and "expired" in remainder:
            self.expire(set(remainder["expired"]))
        if remainder and "result" in remainder:
            result = remainder["result"]
        return result

    def _parse_uri(self, uri):
        """Parse the given uri and return uri, username, password.

        Args:
            uri (str): The URI to parse
        """
        if uri is None:
            return None, None, None
        parsed = urllib.parse.urlparse(uri)
        username = parsed.username
        password = parsed.password
        parsed = list(parsed)
        if username or password:
            parsed[1] = parsed[1].split("@")[1]
        uri = urllib.parse.urlunparse(parsed)
        return uri, username, password

    # OVERRIDE
    def __getattr__(self, attr):
        """Forward attribute calls to backend server.

        Args:
            attr (str): The attribute to get.

        Raises:
            AttributeError: The session in the backend doesn't have the
                attribute.

        Returns:
            Callable: A Method that will trigger a request to the server.
        """
        # Send each method call to the server.
        if (
            not attr.startswith("_")
            and hasattr(self.session_cls, attr)
            and callable(getattr(self.session_cls, attr))
        ):
            consume_buffers = check_consumes_buffers(
                getattr(self.session_cls, attr)
            )
            return lambda *args, **kwargs: self._send(
                attr, consume_buffers, *args, **kwargs
            )
        else:
            raise AttributeError("Unknown attribute %s" % attr)

    # OVERRIDE
    def __str__(self):
        """Convert the object to string."""
        return "TransportSessionClient connected to %s on %s" % (
            self.session_cls,
            self._engine.uri,
        )
