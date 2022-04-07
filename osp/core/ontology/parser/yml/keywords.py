"""This file contains keywords that occur in the YAML ontology."""

VERSION_KEY = "version"
AUTHOR_KEY = "author"
ONTOLOGY_KEY = "ontology"
NAMESPACE_KEY = "namespace"
REQUIREMENTS_KEY = "requirements"

MAIN_NAMESPACE = "cuba"
ROOT_relationship = "relationship"
ROOT_ATTRIBUTE = "ATTRIBUTE"
ROOT_CLASS = "CLASS"

DESCRIPTION_KEY = "description"
SUPERCLASSES_KEY = "subclass_of"
INVERSE_KEY = "inverse"
DEFAULT_REL_KEY = "default_rel"
DATATYPE_KEY = "datatype"
ATTRIBUTES_KEY = "attributes"
DISJOINTS_KEY = "disjoint_with"
EQUIVALENT_TO_KEY = "equivalent_to"
DOMAIN_KEY = "domain"
RANGE_KEY = "range"
CHARACTERISTICS_KEY = "characteristics"

# class expressions
CARDINALITY_KEY = "cardinality"
TARGET_KEY = "range"
EXCLUSIVE_KEY = "exclusive"

CHARACTERISTICS = {
    "reflexive",
    "symmetric",
    "transitive",
    "functional",
    "irreflexive",
    "asymmetric",
    "inversefunctional",
}

DATATYPES = {"BOOL", "INT", "FLOAT", "STRING", "VECTOR"}
