__path__ = __import__("pkgutil").extend_path(__path__, __name__)

# Patch RDFLib <= 5.0.0. See osp-core issue
# https://github.com/simphony/osp-core/issues/558 (the drive letter from the
# path is stripped on Windows by the graph.Graph.serialize method of
# RDFLib <= 5.0.0).
import sys as _osp_sys

from osp.core.pico import CompareOperations as _CompareOperations
from osp.core.pico import compare_version as _compare_version

if _osp_sys.platform == "win32":
    import ctypes as _osp_ctypes
    import ctypes.wintypes as _osp_wintypes
    import os as _osp_os
    from urllib.parse import urlparse as _osp_urlparse

    import rdflib as _osp_rdflib

    if _compare_version(
        _osp_rdflib.__version__, "5.0.0", operation=_CompareOperations.leq
    ):
        # Then patch RDFLib with the following decorator.
        def _graph_serialize_fix_decorator(func):
            def graph_serialize(*args, **kwargs):
                if kwargs.get("destination") is not None and not hasattr(
                    kwargs.get("destination"), "write"
                ):
                    # Bug causing case.
                    (
                        scheme,
                        netloc,
                        path,
                        params,
                        _query,
                        fragment,
                    ) = _osp_urlparse(kwargs["destination"])
                    # If the destination is a windows path.
                    if _osp_urlparse(kwargs["destination"]).path.startswith(
                        "\\"
                    ):
                        # Call the win32 API to get the volume ID.
                        windows_func = (
                            _osp_ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW
                        )
                        windows_func.argtypes = (
                            _osp_wintypes.LPCWSTR,
                            _osp_wintypes.LPWSTR,
                            _osp_wintypes.DWORD,
                        )
                        lpszVolumeMountPoint = _osp_wintypes.LPCWSTR(
                            f"{scheme}:\\"
                        )
                        lpszVolumeName = _osp_ctypes.create_unicode_buffer(50)
                        cchBufferLength = _osp_wintypes.DWORD(50)
                        windows_func(
                            lpszVolumeMountPoint,
                            lpszVolumeName,
                            cchBufferLength,
                        )
                        # Get a DOS_DEVICE_PATH, not affected by the drive
                        # letter stripping bug.
                        dos_device_path = _osp_os.path.join(
                            lpszVolumeName.value.replace("?", ".")
                            or f"\\\\.\\Volume{{DRIVE_LETTER_{scheme}_NOT_"
                            f"ASSIGNED}}\\",
                            path,
                        )
                        kwargs["destination"] = dos_device_path
                return func(*args, **kwargs)

            return graph_serialize

        _osp_rdflib.Graph.serialize = _graph_serialize_fix_decorator(
            _osp_rdflib.Graph.serialize
        )
