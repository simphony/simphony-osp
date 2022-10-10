"""An example showing how to use `pico` to manage ontologies.

> SimPhoNy works with data that is based on ontologies. In particular, all
> information is represented in terms of ontology individuals that belong to
> specific ontology classes, have specific attributes and can be connected to
> other individuals through relationships. Classes, attributes and
> relationships are defined in the ontologies. Therefore, in order for SimPhoNy
> to be able to properly interpret the data, such ontologies need to be made
> available to it. For that purpose, SimPhoNy includes an ontology management
> tool called pico.

> Ontologies can be added to SimPhoNy by installing ontology packages, which
> are YAML configuration files that, in addition to pointing to the actual
> ontology files, also define extra metadata.
-- [Installing ontologies (pico) - SimPhoNy documentation](https://simphony.readthedocs.io/en/v4.0.0rc4/usage/ontologies/pico.html)
"""

from simphony_osp.tools.pico import install, namespaces, packages, uninstall

install(
    "city",  # ontology package included with SimPhoNy
    "foaf",  # ontology package included with SimPhoNy
    "dcat",  # ontology package included with SimPhoNy
    # 'path/to/ontology_package.yml'  # when not included with SimPhoNy
)

print(list(packages()))
print({namespace.name: namespace.iri for namespace in namespaces()})

uninstall("city", "foaf", "dcat")

print(list(packages()))
print(list(namespaces()))
