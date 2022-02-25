"""Core module of the SimPhoNy OSP."""

import logging as _logging

# Load the tbox and set the default session when importing any submodule.
import simphony_osp.core.namespaces as _namespaces
assert _namespaces.cuba  # -> Do not complain about unused _namespaces flake8).

_logger = _logging.getLogger(__name__)
# _logging.getLogger("rdflib").setLevel(_logging.WARNING)

# set up logging
# _ch = _logging.StreamHandler()
# _ch.setLevel(_logging.DEBUG)
# _formatter = _logging.Formatter(
#     '%(levelname)s %(asctime)s [%(name)s]: %(message)s'
# )
# _ch.setFormatter(_formatter)
# _logger.addHandler(_ch)
# _logging.getLogger("osp.wrappers").addHandler(_ch)

try:
    from simphony_osp.core.packageinfo import VERSION as __version__
except ModuleNotFoundError:
    __version__ = None
    _logger.critical(
        "Error determining version of SimPhoNy. If you installed from source, "
        "try the following: \n"
        "\t- If you want to import SimPhoNy with the simphony-osp repo as "
        "cwd, please reinstall using `pip install -e "
        "<path/to/simphony-osp/repo>`. \n"
        "\t- Otherwise you can reinstall using "
        "`pip install <path/to/simphony-osp/repo>`."
    )
