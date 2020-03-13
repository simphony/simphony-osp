[![pipeline status](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/badges/master/pipeline.svg)](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/commits/master)
[![coverage report](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/badges/master/coverage.svg)](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/commits/master)

# OSP core

Native implementation of the core cuds object and the class generation
by the SimPhoNy team at Fraunhofer IWM. Builds up on the previous
version, simphony-common (SimPhoNy, EU FP7 Project (Nr. 604005)
www.simphony-project.eu)

Copyright (c) 2018, Adham Hashibon and Materials Informatics Team at
Fraunhofer IWM. All rights reserved. Redistribution and use are limited
to the scope agreed with the end user. No parts of this software may be
used outside of this context. No redistribution is allowed without
explicit written permission.

## Requirements

- PyYaml (on Windows, use <https://stackoverflow.com/a/33673823>) for parsing yaml files
- numpy for vector attributes of cuds
- websockets for the transport layer
- requests for sending CUDS to a server
- tox to run unittests
- unittest2 to run unittests
- pympler for the performance test
- responses for unittesting requests

## Installation

The package requires python 3.6 or higher (tested for 3.7), installation is based on
setuptools:

```sh
# build and install
python3 setup.py install
```

or:

```sh
# build for in-place development
python3 setup.py develop
```

## Installation of ontologies

After you installed osp-core you can install your ontology namespaces. We provide the tool `pico`
(**p**ico **i**nstalls **c**uds **o**ntologies) for that purpose. The following command
installs the example city ontology namespace:

```sh
pico install city
```

You can also install your own ontologies:

```sh
pico install path/to/your/ontology.yml
```

If you want to uninstall an ontology use the following command:

```sh
pico uninstall <namespace>  # e.g. city
```

If pico is not available after you install OSP core, try to restart your shell.

## Visualization of ontologies

We provide the tool `ontology2dot` to visualize your ontologies. You can visualize installed namespaces together with non-installed yaml files:

```sh
ontology2dot <installed-namespace-1> ... <installed-namespace-n> <path/to/ontology-1.yml> ... <path/to/ontology-m.yml>
```

You can use parameter `-g` to group the namespaces. Use `-o` to change the filename of the resulting png file.

## Testing

Testing is done using tox (`pip install tox`):

```sh
# run tests automatically in different environments
tox

# run tests in your current environment
python -m unittest -v
```

## Documentation

Our documentation is located at <https://simphony.pages.fraunhofer.de/documentation/latest/>.

If you want to build the documentation locally, refer to our [documentation repostitory](https://gitlab.cc-asp.fraunhofer.de/simphony/documentation).

### Examples

Further examples can be found in the /examples folder. There the usage of wrappers is explained.

### Directory structure

- osp/core -- The source code
  - tools -- various tools to work with osp-core.
  - ontology -- the parser and generation of the entities and classes.
    - yml -- The supplied ontology files
  - session -- Different abstract classes for wrappers.
- examples -- examples of usage.
- tests -- unittesting of the code