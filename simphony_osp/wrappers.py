"""Wrappers are interfaces between the SimPhoNy OSP and other software.

This module lets the user access the SimPhoNy wrappers that are installed.

On the `setup.py` file of each wrapper, the wrapper class is registered with
the [entry point](https://setuptools.pypa.io/en/latest/userguide/entry_point
.html#advertising-behavior) `simphony_osp.wrappers`. This module loads all
the classes registered with this entry point and makes them accessible
within its namespace. It also makes them discoverable through IPython tab
completion.
"""

import sys
from typing import Type

from simphony_osp.interfaces.interface import Interface
from simphony_osp.session.wrapper import WrapperSpawner as Wrapper

if sys.version_info < (3, 8):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points

# Retrieve all wrappers from package entry points.
package_entry_points = entry_points()
if sys.version_info >= (3, 10) or sys.version_info < (3, 8):
    wrappers = package_entry_points.select(group="simphony_osp.wrappers")
else:
    wrappers = package_entry_points.get("simphony_osp.wrappers", tuple())
del package_entry_points
wrappers = {entry_point.name: entry_point.load() for entry_point in wrappers}


def __getattr__(name: str):
    """Retrieve a wrapper.

    The wrapper is an object that the user can call to spawn a
    wrapper ontology entity.

    Args:
        name: Name of the wrapper. The name of a wrapper is the name chosen
            by the developer for the entry point.
    """
    if name not in wrappers:
        raise AttributeError(name)

    class WrapperSpawner(Wrapper):
        """Adds a method to retrieve the Interface class of a wrapper.

        Internally, SimPhoNy calls the class that the wrapper developer
        implements "Interface" class. The "Wrapper" class from which this
        one inherits just provides a way for the user to start using a wrapper.

        This specific "WrapperSpawner" class just defines the abstract method
        "_get_interface" that the "Wrapper" class requires.
        """

        @classmethod
        def _get_interface(cls) -> Type[Interface]:
            return wrappers[name]

    return WrapperSpawner


def __dir__():
    return list(wrappers.keys())
