![](https://github.com/simphony/osp-core/workflows/CI/badge.svg)

# OSP core

Native implementation of the core cuds object and the class generation
by the SimPhoNy team at Fraunhofer IWM. Builds up on the previous
version, simphony-common (SimPhoNy, EU FP7 Project (Nr. 604005)
www.simphony-project.eu)

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

The package requires python 3.7 or higher, installation is based on
setuptools:

```sh
# build and install (recommended)
pip install .

# alternative
python3 setup.py install
```

or:

```sh
# build for in-place development (recommended)
pip install -e .


# alternative
python3 setup.py develop
```

## Installation of ontologies

After you installed osp-core you can install your ontology namespaces. We provide the tool `pico`
(**p**ico **i**nstalls **c**uds **o**ntologies) for that purpose. The following command
installs the example city ontology namespace:

```sh
pico install city

# If you have issues using pico directly, you can use
python -m osp.core.pico install city
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

We provide the tool `ontology2dot` to visualize your ontologies. You can visualize installed namespaces together with non-installed yaml files (requires Graphviz https://graphviz.gitlab.io/):

```sh
ontology2dot <installed-namespace-1> ... <installed-namespace-n> <path/to/ontology-1.yml> ... <path/to/ontology-m.yml>

# Alternative
python -m osp.core.tools.ontology2dot <installed-namespace-1> ... <installed-namespace-n> <path/to/ontology-1.yml> ... <path/to/ontology-m.yml>
```

You can use parameter `-g` to group the namespaces. Use `-o` to change the filename of the resulting png file.

## Testing

Testing is done using tox (`pip install tox`):

```sh
# run tests automatically in different environments
tox

# run tests in your current environment (you must manually install unittest2, responses for that)
python -m unittest -v
```

## Documentation

Our documentation is located at <https://simphony.readthedocs.io>.

If you want to build the documentation locally, refer to our [documentation repostitory](https://github.com/simphony/docs).

### Examples

Further examples can be found in the /examples folder. There the usage of wrappers is explained.

## Troubleshooting

If installation fails, try to install the dependencies one by one before installing osp-core.
The dependencies are listed at the top of this readme file.

On Windows, unittests can fail when you use a virtual environment.
For testing the transport layer, we start a transport layer server using pythons subprocess package.
It can happen, that the started subprocess does not pick up the correct virtual environment, causing the server to crash and the corresponding tests to fail.
From our experience, this will not happen if you use the virtual environements of conda.

### Directory structure

- osp/core -- The source code
  - tools -- various tools to work with osp-core.
  - ontology -- the parser and generation of the entities and classes.
    - yml -- The supplied ontology files
  - session -- Different abstract classes for wrappers.
- examples -- examples of usage.
- tests -- unittesting of the code
