__path__ = __import__('pkgutil').extend_path(__path__, __name__)

# Patch RDFLib <= 5.0.0. See osp-core issue https://github.com/simphony/osp-core/issues/558 (the drive letter from the
# path is stripped on Windows by the graph.Graph.serialize method of RDFLib <= 5.0.0).
import sys as _osp_sys
if _osp_sys.platform == 'win32':
    import os as _osp_os
    import ctypes as _osp_ctypes
    import ctypes.wintypes as _osp_wintypes
    from urllib.parse import urlparse as _osp_urlparse
    import rdflib as _osp_rdflib


    def _compare_version_leq(version, other_version):
        """Compares two software version strings.

        Receives two software version strings which are just numbers separated by dots and determines whether the first one
        is less or equal than the second one.

        Args:
            version (str): first version string (number separated by dots).
            other_version (str) : second version string (number separated by dots).

        Returns:
            bool: whether the first version string is less or equal than the second one.
        """
        version = version.split('.')
        other_version = other_version.split('.')
        for i in range(0, min(len(version), len(other_version))):
            if version[i] < other_version[i]:
                return True
            elif version[i] > other_version[i]:
                return False
        else:
            if len(other_version) > len(version) and other_version[i + 1] > str(0):
                return False
            else:
                return True


    if _compare_version_leq(_osp_rdflib.__version__, '5.0.0'):
        # Then patch RDFLib with the following decorator.
        def _graph_serialize_fix_decorator(func):
            def graph_serialize(*args, **kwargs):
                if kwargs.get('destination') is not None and not hasattr(kwargs.get('destination'), 'write'):
                    # Bug causing case.
                    scheme, netloc, path, params, _query, fragment = _osp_urlparse(kwargs['destination'])
                    if _osp_urlparse(kwargs['destination']).path.startswith('\\'):  # The destination is a windows path.
                        # Call the win32 API to get the volume ID.
                        windows_func = _osp_ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW
                        windows_func.argtypes = _osp_wintypes.LPCWSTR, _osp_wintypes.LPWSTR, _osp_wintypes.DWORD
                        lpszVolumeMountPoint = _osp_wintypes.LPCWSTR(f'{scheme}:\\')
                        lpszVolumeName = _osp_ctypes.create_unicode_buffer(50)
                        cchBufferLength = _osp_wintypes.DWORD(50)
                        windows_func(lpszVolumeMountPoint, lpszVolumeName, cchBufferLength)
                        # Get a DOS_DEVICE_PATH, not affected by the drive letter stripping bug.
                        dos_device_path = _osp_os.path.join(lpszVolumeName.value.replace('?', '.')
                                                       or f'\\\\.\\Volume{{DRIVE_LETTER_{scheme}_NOT_ASSIGNED}}\\',
                                                       path)
                        kwargs['destination'] = dos_device_path
                func(*args, **kwargs)
            return graph_serialize
        _osp_rdflib.Graph.serialize = _graph_serialize_fix_decorator(_osp_rdflib.Graph.serialize)
