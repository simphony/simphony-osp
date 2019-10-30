from osp.core.ontology.namespace_registry import ONTOLOGY_NAMESPACE_REGISTRY
import sys

thismodule = sys.modules[__name__]


for name, namespace in ONTOLOGY_NAMESPACE_REGISTRY._namespaces.items():
    setattr(thismodule, name, namespace)
