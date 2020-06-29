import rdflib
from collections import defaultdict

VERSION_KEY = "version"
AUTHOR_KEY = "author"
ONTOLOGY_KEY = "ontology"
NAMESPACE_KEY = "namespace"
REQUIREMENTS_KEY = "requirements"

MAIN_NAMESPACE = "CUBA"
ROOT_RELATIONSHIP = "RELATIONSHIP"
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
    "inversefunctional"
}


DATATYPES = defaultdict(lambda: rdflib.XSD.string)  # TODO normal dict
DATATYPES.update({
    "BOOL": rdflib.XSD.boolean,
    "INT": rdflib.XSD.integer,
    "FLOAT": rdflib.XSD.float,
    "STRING": rdflib.XSD.string,
    # TODO "VECTOR": (to_vector, from_vector, None, rdflib.XSD.string)
})
