import logging
from osp.core.namespaces import _namespace_registry
from osp.core.owl_ontology.owl_parser import Parser
from osp.core.owl_ontology.owl_installation import OntologyInstallationManager
logging.getLogger("osp.core").setLevel(logging.DEBUG)
p = Parser(_namespace_registry._graph)
p.parse("emmo.yml")
_namespace_registry.update_namespaces()

from osp.core.namespaces import material
print(material["atom", "en"])
print(material.EMMO_eb77076b_a104_42ac_a065_798b2d2809ad)
print(material["atom"] == material.EMMO_eb77076b_a104_42ac_a065_798b2d2809ad)
print(material.default_rel)

installer = OntologyInstallationManager()
installer.install("emmo.yml")
