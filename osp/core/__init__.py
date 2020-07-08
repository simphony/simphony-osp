import sys
import logging

logging.getLogger("rdflib").setLevel(logging.WARNING)

from osp.core.packageinfo import VERSION as __version__

# set up logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(levelname)s [%(name)s]: %(message)s'
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logging.getLogger("osp.wrappers").addHandler(ch)


def __getattr__(name):
    import osp.core.namespaces
    if name != "load_tests":
        logger.warning(f"osp.core.{name} is deprecated. "
                    f"Use osp.core.namespaces.{name} instead.")
    return getattr(osp.core.namespaces, name)
