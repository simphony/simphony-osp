# How to convert an OWL ontology to YAML

OSP-core requires an ontology in YAML format for installation.
This document explains how an ontology in OWL format can be
converted to YAML.

## Disclaimer

In the current version of OSP core, not all OWL-ontologies are supported.
We are working hard to change that as soon as possible.
In the course of converting the OWL ontology to YAML, the ontology
has to be modified to match the constraints of a YAML ontology.
These constraints are explained in doc/yaml_specification.md
The conversion script will perform the modifications.
It will ask the user to make decisions on how the ontology should be modified.

As soon as OWL is supported completely, there will be a script converting
OWL to YAML without user input.

If you have any issues with the conversion, please use the GitLab
issue tracker. Attach the `owl-conversion` label to your issue.

## Prerequisites

- We use owlready2 for the conversion. Therefore, the ontology
must be in one of the following formats: RDF/XML, OWL/XML, NTriples.
- Make sure you ran the reasoner and exported the inferred axioms.

## Conversion

This section will explain in detail how you can convert an OWL ontology
to YAML. We will use the EMMO as an example.
The document doc/working_with_emmo.md explains how you can get the EMMO.

1. Run the conversion script. It is located in `cuds/generator/owl_to_yml.py`.
   Give the path to your OWL file as the only argument.

   ```sh
   python cuds/generator/owl_to_yml.py emmo.owl
   ```

2. Choose the parent for the relationships:
   In OWL ontologies it is common that relationships are
   sub-relationship of multiple relationships.
   This is currently not allowed by OSP-core, but will be in the near future.
   For now, the user has to choose a single parent per relationship.

   ```sh
   Choose the parent of HAS_TEMPORAL_PROPER_PART. 
    1) CUBA.HAS_TEMPORAL_PART
    2) CUBA.HAS_PROPER_PART
    Type the number of your choice: 1
    ```

3. Choose the primary parent for the classes.
   In OWL ontologies it is common that classes are a sub-class of
   multiple classes.
   This is currently not allowed by OSP-core, but will be in the near future.
   For now, the user has to choose a single primary parent per class.
   The other (secondary) parents will be connected by a CUBA.IS_A relationship.

    ```sh
    Choose the primary parent of ELEMENTARY. The others will be related by CUBA.IS_A.
    1) CUBA.STATE
    2) CUBA.PHYSICAL
    Type the number of your choice: 2
    ```

    This will result in:

    ```yml
    ELEMENTARY:
      definition: ...
      parent: CUBA.PHYSICAL
      ...
      CUBA.IS_A:
        CUBA.STATE:
          cardinality: 1
    ```

4. Choose where to insert ACTIVE_RELATIONSHIP.
   Cuds objects can be seen as containers, that contain other cuds objects.
   In OSP-core, there is (currently) the concept of active (and passive) relationships.
   Active relationships describe which cuds objects are contained in other cuds objects.

   ```txt
   No CUBA.ACTIVE_RELATIONSHIP in the ontology.
   Specify the entity, that should have ACTIVE_RELATIONSHIP as parent:
   > encloses
   ```

5. In the next step you can add arguments to the classes.
   The datatypes are specified
   in doc/yaml_spec.md. The argument must not be in the ontology.
   Alternatively you
   can have a VALUE entity in the OWL ontology. Then each sub-entity of value
   will be a argument for other cuds-classes.

   ```txt
   Enter classes that should have arguments: number
   argument name: x
   datatype: float
   ```

6. Specify missing inverses.
   In OSP-core every relation must have an inverse (currently). In this step
   you can specify an inverse for every relationship that does not have one.
   Note that the specified inverse must be in the ontology.

   ```txt
   OSP-core currently does not allow missing inverses. Please specify an inverse for every relationship. Each specified inverse must be in the ontology. Specifying an inverse for every entity will not be necessary in upcoming osp-core versions.
   Specify inverse of RELATION: relation
   Specify inverse of HAS_ICON: is icon of
   Specify inverse of HAS_INDEX: is index of
   Specify inverse of IS_ICON_OF: has icon
   Specify inverse of SEMIOTIC: semiotic
   Specify inverse of IS_INDEX_OF: has index
   ```

7. Rename duplicates.
   In OWL it is possible to have a class and a relationship with the same name. This is (currently)
   not allowed in OSP-core. If you have such duplicates, the script will
   ask you to rename one of them.

   ```txt
   SEMIOTIC has been specified as class and relationship. Which one do you want to rename?
   1) class
   2) relationship
   Type the number of your choice: 2
   Rename to: semiotic rel
   ```

8. The ontology will be saved as ontology.<name>.yml in your current working directory.
   Take a look at it by opening it with a text editor. The great thing about
   yaml ontologies is that they are understandable by humans. If you are not
   satisfied with the result, you can modify the resulting ontology by hand.
