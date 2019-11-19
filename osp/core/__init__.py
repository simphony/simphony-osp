from osp.core.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY
from osp.core.ontology.parser import Parser
import sys

thismodule = sys.modules[__name__]


for name, namespace in ONTOLOGY_NAMESPACE_REGISTRY._namespaces.items():
    setattr(thismodule, name, namespace)


user_defined_default_rel = None
installed_default_rel = ONTOLOGY_NAMESPACE_REGISTRY.default_rel


def get_default_rel():
    global user_defined_default_rel, installed_default_rel, \
        ONTOLOGY_NAMESPACE_REGISTRY

    result = (
        user_defined_default_rel
        or ONTOLOGY_NAMESPACE_REGISTRY.default_rel
        or installed_default_rel
    )
    user_defined_default_rel = result
    return result


def set_default_rel(rel):
    global user_defined_default_rel
    user_defined_default_rel = rel


def get_entity(entity_name):
    namespace, name = entity_name.split(".")
    return ONTOLOGY_NAMESPACE_REGISTRY[namespace][name]


def install_current_ontology():
    ONTOLOGY_NAMESPACE_REGISTRY.install()
