import logging
import sys

import rdflib

import osp.core.namespaces
from osp.core.ontology.namespace_registry import (
    namespace_registry as _namespace_registry,
)

logging.getLogger("rdflib").setLevel(logging.WARNING)

try:
    getattr(rdflib, "SKOS")
except AttributeError:
    rdflib.SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")

# set up logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "%(levelname)s %(asctime)s [%(name)s]: %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logging.getLogger("osp.wrappers").addHandler(ch)

try:
    from osp.core.packageinfo import VERSION as __version__
except ModuleNotFoundError:
    __version__ = None
    logger.critical(
        "Error determining version of osp-core. If you installed from source, "
        "try the following: \n"
        "\t- If you want to import osp-core with the osp-core repo as cwd, "
        "please reinstall using `pip install -e <path/to/osp-core/repo>`. \n"
        "\t- Otherwise you can reinstall using "
        "`pip install <path/to/osp-core/repo>`."
    )


def __getattr__(name):
    if name != "load_tests":
        logger.warning(
            f"osp.core.{name} is deprecated. "
            f"Use osp.core.namespaces.{name} instead."
        )
    return getattr(osp.core.namespaces, name)


if (sys.version_info.major, sys.version_info.minor) <= (3, 6):
    logger.info("We recommend using a python version of at least 3.7")
    logger.info(
        f"osp.core.<namespace> is deprecated. "
        f"Use osp.core.namespaces.<namespace> instead."
    )
    _namespace_registry.update_namespaces(
        modules=[sys.modules[__name__], namespaces]
    )
