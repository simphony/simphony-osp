# How to convert an OWL ontology to YAML

OSP-core requires an ontology in YAML format for installation.
This document explains how an ontology in OWL format can be
converted to YAML.

## Prerequisites

- We use owlready2 for the conversion. Therefore, the ontology
must be in one of the following formats: RDF/XML, OWL/XML, NTriples.
- Make sure you ran the reasoner and exported the inferred axioms.
- OSP core must be installed

## Conversion

This section will explain in detail how you can convert an OWL ontology
to YAML. We will use the EMMO as an example.
The document doc/working_with_emmo.md explains how you can get the EMMO.

1. The script for the conversion is called owl2yml. Call it with the -h option
   to print help:

   ```sh
   $ owl2yml -h
   usage: owl2yml [-h] --namespace NAMESPACE [--conversion_options_file CONVERSION_OPTIONS_FILE] [--version VERSION] [--output-file OUTPUT_FILE] input-file

   Convert an ontology in OWL format to an ontology in YAML format.

   positional arguments:
     input-file            The path to the input owl file

   optional arguments:
     -h, --help            show this help message and exit
     --namespace NAMESPACE, -n NAMESPACE
                           The namespace for the resulting YAML file in UPPERCASE
     --conversion_options_file CONVERSION_OPTIONS_FILE, -c CONVERSION_OPTIONS_FILE
                           Path to a file explaining how the ontology should be transformed, s.t. it is compatible with osp-core
     --version VERSION, -v VERSION
                           The version string for the resulting YAML file
     --output-file OUTPUT_FILE, -o OUTPUT_FILE
                           Where the output file should be saved
   ```

2. You have to specify the owl input file and the namespace,
   with which the entities in the owl file should be accessible in OSP core:

   ```sh
   $ owl2yml -n MY_NAMESPACE path/to/owlfile.owl
   ```

3. Optionally, you can specify a version string:

   ```sh
   $ owl2yml -n MY_NAMESPACE path/to/owlfile.owl -v 0.0.1
   ```

4. Optionally, you can specify where the resulting yaml file should be stored:

   ```sh
   $ owl2yml -n MY_NAMESPACE ../../owlfile.owl -o result.yml
   ```

5. It is recommended that you extend the ontology,
   such that it is easier to use with OSP core.
   For that you have to create a yaml file in
   the following format:

   ```yml
   ---
   default_rel: <iri_of_default_relationship>
   active_relationships: [list_of_iris]
   insert_entities:
     VALUE:
       subclass_of:
       - CUBA.ATTRIBUTE
       datatype: FLOAT
   update_entities:
     NUMBER:
       attributes:
       - MY_NAMESPACE.VALUE
   ```

   - For EMMO, this file is provided and located in `osp/core/tools/conversion_options/emmo.conversion_options.yml`

   - You can specify a default relationship with the `default_rel` keyword.
     You have to provide the IRI of the relationship.
     In OSP core, when you add one CUDS objects to another without specifying a relationship, this relationship will be used.

   - CUDS objects are containers conceptually.
     Therefore, you need to specify which relationships encode a containment in a CUDS objects.
     We call these relationships `active relationships`.
     Let's say you have a relationship `contains` in the ontology.
     You want to specify that every cuds object related to cuds object A with `contains` should be in the container of A.
     Then `contains` should be marked as an active relationship.
     Note that the edge-induced graph of the cuds objects by only considering active relationships must be acyclic at any point in time.
     Active relationships must not be symmetric.
     See `doc/yaml_spec.md` for more details.
     You can specify active relationships with the `active_relationships` keyword.
     You need to provide a list of IRIs of relationships that should become an active relationship.

   - If you are not satisfied with your result, you can manually modify the resulting yml file.
     You can also use the keywords `insert_entities` or `update_entities` to modify the resulting
     yml automatically.
