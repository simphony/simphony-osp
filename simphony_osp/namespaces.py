"""You can import the installed namespaces from this module."""

from simphony_osp.core.namespaces import __dir__ as _ns_dir
from simphony_osp.core.namespaces import __getattr__ as _ns_getattr


def __getattr__(name: str):
    return _ns_getattr(name)


__dir__ = _ns_dir

__all__ = _ns_dir()
