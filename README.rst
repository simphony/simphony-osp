[![Coverage report](https://gitlab.com/gitlab-org/gitlab-ce/badges/master/coverage.svg?job=coverage)](http://gitlab-org.gitlab.io/gitlab-ce/coverage-ruby)

core-osp
========
Native implementation of the core cuds object and the class generation by the SimPhoNy team at Fraunhofer IWM.
Builds up on the previous version, simphony-common (SimPhoNy, EU FP7 Project (Nr. 604005) www.simphony-project.eu)

Requirements
------------
- enum34
- PyYaml

*To run cuds2dot, graphviz must be installed in the system::

    sudo apt-get install graphviz

Installation
------------
The package requires python 2.7.x, installation is based on setuptools::

    # build and install
    python setup.py install

or::

    # build for in-place development
    python setup.py develop

Testing
-------
Testing is included in setuptools::

    # run tests automatically
    python setup.py test

They can also be ran manually::

    # manually run tests
    python -m testing.api_test

Documentation
-------------
TODO

Directory structure
-------------------
- cuds -- files necessary for the creation and usage of the cuds.
  - classes -- python classes required for using the cuds.
    - core -- common low level classes and utility code.
    - generated -- generated native cuds implementations.
  - metatools -- class generator and template file.
  - ontology -- ontological representation of the cuds.
    - tools -- scripts that work on the ontology files
- doc -- documentation related files.
- examples -- examples of usage. Can be run with::

        python -m examples.api_example

- testing -- unittesting of the code.

Data structure
--------------
Each cuds object is represented as a registry (dictionary).

Each entry will contain the elements contained by said object with the same CUBA key.

These will be again in a registry, this time by UID.

For example::

    a_cuds_object := {
        'CUBA_key1': {'uid1': cuds_object1, 'uid2': cuds_object2},
        'CUBA_key2': {'uid3': cuds_object3},
        'CUBA_key3': {'uid4': cuds_object4, 'uid5': cuds_object5, 'uid6': cuds_object6}
    }

