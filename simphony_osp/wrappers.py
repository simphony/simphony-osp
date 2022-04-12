"""Interfaces between the SimPhoNy OSP and other software."""

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
if sys.version_info >= (3, 10):
    wrappers = package_entry_points.select(group="simphony_osp.wrappers")
else:
    wrappers = package_entry_points.get("simphony_osp.wrappers", tuple())
del package_entry_points
wrappers = {entry_point.name: entry_point.load() for entry_point in wrappers}


def __getattr__(name: str):
    if name not in wrappers:
        raise AttributeError(name)

    class _WrapperSpawner(Wrapper):
        @classmethod
        def _get_interface(cls) -> Type[Interface]:
            return wrappers[name]

    return _WrapperSpawner


def __dir__():
    return list(wrappers.keys())
