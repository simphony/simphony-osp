"""SimPhoNy OSP module."""

import simphony_osp.namespaces as namespaces
from simphony_osp.core.wrappers import __dir__ as _wrappers_dir
from simphony_osp.core.wrappers import __getattr__ as _wrappers_getattr

__path__ = __import__('pkgutil').extend_path(__path__, __name__)

self = __import__(__name__)


def __getattr__(name: str):
    return _wrappers_getattr(name)


def __dir__():
    return _wrappers_dir() + ['namespaces']


__all__ = _wrappers_dir() + ['namespaces']
