![pipeline_badge](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/badges/cuds-2.0/pipeline.svg)
![coverage_badge](https://gitlab.cc-asp.fraunhofer.de/simphony/osp-core/badges/cuds-2.0/coverage.svg)

# Core-OSP
Native implementation of the core cuds object and the class generation by the SimPhoNy team at Fraunhofer IWM.
Builds up on the previous version, simphony-common (SimPhoNy, EU FP7 Project (Nr. 604005) www.simphony-project.eu)

Copyright (c) 2018, Adham Hashibon and Materials Informatics Team at Fraunhofer IWM.
All rights reserved.
Redistribution and use are limited to the scope agreed with the end user.
No parts of this software may be used outside of this context.
No redistribution is allowed without explicit written permission.

## Requirements
- PyYaml (on Windows, use https://stackoverflow.com/a/33673823)

\*To run cuds2dot, `graphviz` must be installed in the system:
```
    sudo apt-get install graphviz
```
If you want to visualise the graph in a more interactive way than just the png, `xdot` can be used:
```
    sudo apt-get install xdot
```
## Installation
The package requires python 3 (tested for 3.7), installation is based on setuptools:
```
    # build and install
    python3 setup.py install

    # using toy ontology
    python3 setup.py install -t
```
or:
```
    # build for in-place development
    python3 setup.py develop
```

## Testing
Testing is included in setuptools:
```
    # run tests automatically
    python3 setup.py test
```

They can also be run manually:
```
    # manually run tests
    python3 -m cuds.testing.test_api
```

## Entry points
There is an entry point for the *cuds2dot* tool for graph generation. Use `cuds2dot -h` for help.

The *class generator* can also be run with different ontologies and/or template files.
The idea is that the users can define their own ontology and compare with the stable one.
The new one will not be added to the python site-packages, and can be imported through relative paths.

If the generated classes are to be added to python for easier importing, the output folder can be set to `site-packages`:
```python
    import site
    print(site.getsitepackages())[0] + "/cuds/classes/generated")
```

## Directory structure
- cuds -- files necessary for the creation and usage of the cuds.
  - classes -- python classes required for using the cuds.
    - core -- common low level classes and utility code.
    - generated -- generated native cuds implementations.
  - metatools -- class generator and template file.
  - ontology -- ontological representation of the cuds.
    - tools -- scripts that work on the ontology files
  - testing -- unittesting of the code.
- doc -- documentation related files.
- examples -- examples of usage.

## Data structure
Each cuds object is represented as a registry (dictionary).

Each entry will enclose the elements contained by said object with the same CUBA key.

These will be again in a registry, this time by UID.

For example:
```json
    a_cuds_object = {

        "CUBA_key1": {"uid1": cuds_object1, "uid2": cuds_object2},
        "CUBA_key2": {"uid3": cuds_object3},
        "CUBA_key3": {"uid4": cuds_object4, "uid5": cuds_object5, "uid6": cuds_object6}

    }
```
