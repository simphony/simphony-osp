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

```sh
# install ontologies
python3 setup.py install -o <path/to/ontology.own-ontology.yml>
```

```sh
# reset installed ontologies
python3 setup.py install -r
```

or:

```sh
# build for in-place development
python3 setup.py develop
```

### Installation of OWL ontologies

See doc/working_with_emmo.md for working with the EMMO. \
See doc/conversion_owl_to_yaml.md if you want to work with any OWL ontology.

## Testing

Testing is done using tox (`pip install tox`):

```sh
# run tests automatically in different environments
tox

# run tests in your current environment
python -m unittest -v
```

## Documentation

### API

A standard, simple API has to be defined for the user to interact with OSP:

```python
  from osp.core import MY_NAMESPACE
  # from osp.core import my_namespace  # lowercase works as well!

  my_ontology_class = MY_NAMESPACE.MY_ONTOLOGY_CLASS
  # my_ontology_class = my_namespace.MyOntologyClass  # CamelCase works as well!
  my_cuds_object = MY_NAMESPACE.MY_ONTOLOGY_CLASS()
  my_relationship = MY_NAMESPACE.MY_RELATIONSHIP

  # These will also add the opposed relationship to the new contained cuds object
  my_cuds_object.add(*other_cuds, rel=my_relationship)
  my_cuds_object.add(yet_another_cuds)                           # Defaults to default relationship specified in ontology

  my_cuds_object.get()                                           # Returns the list of all the contained cuds objects
  my_cuds_object.get(rel=my_relationship)                        # Returns the list of the entities under that relationship
  my_cuds_object.get(*uids)                                      # Searches through all the relationships for the uids
  my_cuds_object.get(*uids, rel=my_relationship)                 # Faster, can filter through the relationship
  my_cuds_object.get(oclass=a_ontology_class)                    # Returns the list of all the cuds object of that class
  my_cuds_object.get(rel=my_relationship, oclass=a_ontology_class)   # Returns the list of all the entities of that class under the given relationship

  # These will trigger the update in the opposed relationship of the erased element
  my_cuds_object.remove()                                        # Removes all
  my_cuds_object.remove(*uids/cuds_objects)                      # Searches through all the relationships for the uids/objects to remove
  my_cuds_object.remove(*uids/cuds_objects, rel=my_relationship) # Faster, can filter through the relationship
  my_cuds_object.remove(rel=my_relationship)                     # Delete all elements under a relationship
  my_cuds_object.remove(oclass=a_ontology_class)                 # Delete all elements of a certain class
  my_cuds_object.remove(rel=my_relationship, oclass=my_ontology_class)   # Delete all elements of a certain class under the given relationship

  my_cuds_object.update(*cuds_objects)                           # Searches through all the relationships for the objects to update

  my_cuds_object.iter()                                          # Iterates through all
  my_cuds_object.iter(oclass=a_ontology_class)                   # Iterates filtering by the ontology class
  my_cuds_object.iter(rel=my_relationship)                       # Iterates filtering by the relationship
```

### Data structure

The cuds objects' neighbours are stored in a dictionary.
This contains all the relationships of the cuds object.

For example:

```py
{
    CUBA.REL1: {"obj-uid-001": CUBA.OBJ1, "obj-uid-002": CUBA.OBJ2},
    CUBA.REL2: {"obj-uid-003": CUBA.OBJ3, ...},
    ...
}
```

The related cuds object are referenced by their unique id, the uid.
Each cuds object corresponds to a session.
The session contains a registry that maps every uid to the corresponding cuds object.
Each wrapper has a corresponding session. The default session is an instance of CoreSession.

The attributes are fields of the cuds object:

```py
>>> from osp.core import CITY  # the namespace
>>> c = CITY.CITY(name="Freiburg")
>>> c.name
'Freiburg'
```

### Examples

Further examples can be found in the /examples folder. There the usage of wrappers is explained.

### Directory structure

- osp/core -- The source code
  - tools -- various tools to work with osp-core.
  - ontology -- the parser and generation of the entities and classes.
  - session -- Different abstract classes for wrappers.
- doc -- documentation related files.
- examples -- examples of usage.
- tests -- unittesting of the code

### Architecture

The main components, their sub-components, and the interactions between them are given in the following diagrams.

The structure of a pure python OSP case:
![Standalone CUDS](doc/standalone_cuds.svg)

The structure of a local wrapper:
![Local CUDS](doc/local_cuds.svg)

The structure of a wrapper with a back-end in a remote server:
![Distributed CUDS](doc/distributed_cuds.svg)
