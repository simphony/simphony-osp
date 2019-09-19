# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import json
from cuds.classes.core.session.storage_wrapper_session \
    import StorageWrapperSession
from cuds.classes.core.session.wrapper_session import check_consumes_buffers
from cuds.classes.core.session.transport.communication_engine \
    import CommunicationEngineClient
from cuds.classes.core.session.transport.transport_util import (
    INITIALIZE_COMMAND, LOAD_COMMAND, deserialize_buffers,
    serializable, serialize
)


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
    def _load_from_backend(self, uids, expired=None):
        expired = expired or self._expired
        data = serialize(self, False, {"uids": uids, "expired": expired})
        yield from self._engine.send(LOAD_COMMAND, data)

    # OVERRIDE
    def store(self, cuds_object):
        # Initialize the server, when the first cuds_object is stored.
        if self.root is None:
            data = {
                "args": self.args,
                "kwargs": self.kwargs,
                "root": serializable(cuds_object)
            }
            super().store(cuds_object)
            self._engine.send(INITIALIZE_COMMAND,
                              json.dumps(data))
            return
        super().store(cuds_object)

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
