from osp.core.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY
import sys

thismodule = sys.modules[__name__]


for name, namespace in ONTOLOGY_NAMESPACE_REGISTRY._namespaces.items():
    setattr(thismodule, name, namespace)


user_defined_default_rel = None
installed_default_rel = ONTOLOGY_NAMESPACE_REGISTRY.default_rel

def get_default_rel():
    return (
        user_defined_default_rel
        or ONTOLOGY_NAMESPACE_REGISTRY.default_rel
        or installed_default_rel
    )

def set_default_rel(rel):
    user_defined_default_rel = rel
