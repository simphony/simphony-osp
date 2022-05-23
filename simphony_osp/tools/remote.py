"""Tools aimed at remote interfaces."""

from typing import Optional, Type

from simphony_osp.interfaces.remote.server import InterfaceServer
from simphony_osp.session.wrapper import WrapperSpawner


def host(
    wrapper: Type[WrapperSpawner],
    *args,
    hostname: str,
    port: int,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs
):
    """Host a server based on a wrapper.

    Opens the specified wrapper and starts listening for clients. The
    clients can connect to the wrapper's session and perform actions.

    Args:
        wrapper: The wrapper to be used.
        *args: Positional arguments for the wrapper.
        hostname: Hostname where the server will listen.
        port: The port that the server will use to listen.
        username: A username for authenticating the client.
        password: A password for authenticating the client.
        **kwargs: Keyword arguments for the wrapper.
    """

    def _interface_generator(
        user: Optional[str] = None, pass_: Optional[str] = None
    ):
        if username and user != username:
            raise PermissionError
        if password and pass_ != pass_:
            raise PermissionError
        wrapper_object = wrapper(*args, **kwargs)
        interface = wrapper_object.driver.interface
        return interface

    interface_server = InterfaceServer(
        host=hostname, port=port, generate_interface=_interface_generator
    )

    interface_server.listen()
