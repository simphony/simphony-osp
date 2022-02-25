"""Lets interfaces be used in a user-friendly way.

It scans the installed interfaces and adds their names to __dir__.

When the name of an interface requested, the returned object is a
`_WrapperSpawner` class, which is subclass of the `Wrapper` class from
osp.core.wrapper that has as default interface the one requested by the user.
"""

import importlib as _importlib
import logging as _logging
import os as _os
import pkgutil as _package_utils
from typing import Type as _Type

from simphony_osp.core.interfaces.interface import Interface as _Interface
from simphony_osp.core.wrapper import WrapperSpawner as _Wrapper

_logger = _logging.getLogger(__name__)

_self = __import__(__name__)

# Get all installed interfaces.
_interfaces = dict()
for _module_info in _package_utils.iter_modules(
        (_os.path.join(_path, 'interfaces') for _path in _self.__path__),
        f'{_self.__name__}.interfaces.'):
    try:
        _module = _importlib.import_module(_module_info.name)
    except ImportError:
        _logger.warning(f'Failed to import {_module_info.name}.')

    # Find interfaces in modules.
    try:
        _names = _module.__dict__['__all__']
    except KeyError:
        _names = [_k for _k in _module.__dict__ if not _k.startswith('_')]

    for _name in _names:
        _x = getattr(_module, _name)
        try:
            if issubclass(_x, _Interface):
                _interfaces[_module_info.name.split('.')[-1]] = _x
            break
        except TypeError:
            pass


# Get a wrapper.
def __getattr__(name: str):
    if name not in _interfaces:
        raise AttributeError(name)

    class _WrapperSpawner(_Wrapper):

        @classmethod
        def _get_interface(cls) -> _Type[_Interface]:
            return _interfaces[name]

    return _WrapperSpawner


def __dir__():
    return list(_interfaces.keys())
