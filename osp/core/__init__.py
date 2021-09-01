import logging as _logging
import sys as _sys

import rdflib as _rdflib

_logging.getLogger("rdflib").setLevel(_logging.WARNING)

# set up logging
_logger = _logging.getLogger(__name__)
_ch = _logging.StreamHandler()
_ch.setLevel(_logging.DEBUG)
_formatter = _logging.Formatter(
    '%(levelname)s %(asctime)s [%(name)s]: %(message)s'
)
_ch.setFormatter(_formatter)
_logger.addHandler(_ch)
_logging.getLogger("osp.wrappers").addHandler(_ch)

try:
    from osp.core.packageinfo import VERSION as __version__
except ModuleNotFoundError:
    __version__ = None
    _logger.critical(
        "Error determining version of osp-core. If you installed from source, "
        "try the following: \n"
        "\t- If you want to import osp-core with the osp-core repo as cwd, "
        "please reinstall using `pip install -e <path/to/osp-core/repo>`. \n"
        "\t- Otherwise you can reinstall using "
        "`pip install <path/to/osp-core/repo>`."
    )
