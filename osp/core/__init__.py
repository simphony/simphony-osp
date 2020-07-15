import sys
import logging

logging.getLogger("rdflib").setLevel(logging.WARNING)

# set up logging
logger = logging.getLogger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(levelname)s %(asctime)s [%(name)s]: %(message)s'
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
        "try the follwing: \n"
        "\t- If you want to import osp-core with the osp-core repo as cwd, "
        "please reinstall using `pip install -e <path/to/osp-core/repo>`. \n"
        "\t- Otherwise you can reinstall using "
        "`pip install <path/to/osp-core/repo>`."
    )


def __getattr__(name):
    import osp.core.namespaces
    if name != "load_tests":
        logger.warning(f"osp.core.{name} is deprecated. "
                       f"Use osp.core.namespaces.{name} instead.")
    return getattr(osp.core.namespaces, name)
