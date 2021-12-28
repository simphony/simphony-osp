"""Lets interfaces be used in a user-friendly way.

It scans the installed interfaces and adds their names to __dir__.

When the name of an interface requested, the returned object is a
`_WrapperSpawner` class, which is a `Wrapper` class from
osp.core.session.wrapper that has a default interface set. The `Wrapper`
class is in fact a subclass of the session, that assigns a predefined
store for the session's graph when initialized.
"""

import importlib as _importlib
import os as _os
import pkgutil as _pkgutil
from typing import Type as _Type

from osp.core.interfaces.interface import Interface as _Interface
from osp.core.wrapper import WrapperSpawner as _Wrapper

_self = __import__(__name__)

# Get all installed interfaces.
_interfaces = dict()
for _module_info in _pkgutil.iter_modules(
        (_os.path.join(_path, 'interfaces') for _path in _self.__path__),
        f'{_self.__name__}.interfaces.'):
    _module = _importlib.import_module(_module_info.name)

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
    try:
        class _WrapperSpawner(_Wrapper):

            @classmethod
            def _get_interface(cls) -> _Type[_Interface]:
                return _interfaces[name]

        return _WrapperSpawner

    except KeyError as e:
        raise AttributeError from e


def __dir__():
    return list(_interfaces.keys())
