# SimPhoNy

The SimPhoNy Open Simulation Platform is a framework that aims to achieve
interoperability between software such as simulation engines, databases and
data repositories using a knowledge graph as the common language. It is focused
on the domain of materials science.

SimPhoNy enables:
- Visualization and exploration of
  [OWL ontologies](https://www.w3.org/TR/2012/REC-owl2-primer-20121211/) and
  [RDFS Vocabularies](https://www.w3.org/TR/rdf-schema/)
- _Wrappers_: interfaces between ontologies and software products or digital
  objects
- Manipulation of ontology-based data: work with ontology individuals,
  transfer them among different software products using the wrappers, and query
  the knowledge graph

⚠️ You are reading the README file for a _release candidate_ version of
SimPhoNy. This version has not yet been thoroughly tested, and its
functionality is not yet fully documented. Unless you are explicitly looking to
try this version, please head to the
[`master` branch](https://github.com/simphony/osp-core) of this repository to
find the README file for the latest stable release of SimPhoNy.

## Installation

SimPhoNy is available on PyPI, so it can be installed using pip

`pip install simphony-osp`

Detailed installation instructions can be found
[here](https://simphony.readthedocs.io/en/latest/installation.html).

## Documentation

To learn how to use SimPhoNy, check out our documentation, which is located at
<https://simphony.readthedocs.io>.

In addition, basic usage examples to
quickly get started are available in the
[`examples` folder](https://github.com/simphony/osp-core/tree/release/4/dev/examples).

If you want to build the documentation locally, refer to our [documentation repostitory](https://github.com/simphony/docs).

## Contributing

If you wish to contribute to SimPhoNy, please read the
[contributing guidelines](https://github.com/simphony/osp-core/blob/release/4/dev/CONTRIBUTING.md).

## Acknowledgements

The SimPhoNy Python package originates from the European Project [SimPhoNy](https://www.simphony-project.eu/) (Project Nr. 604005). We would like to acknowledge and thank our project partners, especially [Enthought, Inc](https://www.enthought.com/), [Centre Internacional de Mètodes Numèrics a l'Enginyeria (CIMNE)](https://cimne.com/) and the [University of Jyväskylä](https://www.jyu.fi/en), for their important contributions to some of the core concepts of SimPhoNy, which were originally demonstrated under the project https://github.com/simphony/simphony-common.
