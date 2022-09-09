"""Tools aimed at remote interfaces."""

from typing import Iterable, Optional, Type, Union

from simphony_osp.interfaces.remote.server import InterfaceServer
from simphony_osp.session.wrapper import WrapperSpawner


def host(
    wrapper: Type[WrapperSpawner],
    configuration_string: str = "",
    create: bool = False,
    hostname: str = "127.0.0.1",
    port: int = 6537,
    username: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs: Union[
        str,
        int,
        float,
        bool,
        None,
        Iterable[Union[str, int, float, bool, None]],
    ]
):
    """Host a server based on a wrapper.

    Opens the specified wrapper and starts listening for clients. The
    clients can connect to the wrapper's session and perform actions.

    Args:
        wrapper: The wrapper to be used.
        configuration_string: The configuration string of the wrapper.
        create: The value of the argument `create` for the wrapper.
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
        session = wrapper(configuration_string, create, **kwargs)
        interface = session.driver.interface
        return interface

    interface_server = InterfaceServer(
        host=hostname, port=port, generate_interface=_interface_generator
    )

    interface_server.listen()
