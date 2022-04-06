"""This file contains keywords that occur in the OWL ontology config files."""

IDENTIFIER_KEY = "identifier"
RDF_FILE_KEY = "ontology_file"
NAMESPACES_KEY = "namespaces"
ACTIVE_REL_KEY = "active_relationships"
DEFAULT_REL_KEY = "default_relationship"
FILE_FORMAT_KEY = "format"
REQUIREMENTS_KEY = "requirements"
REFERENCE_STYLE_KEY = "reference_by_label"
FILE_HANDLER_KEY = "file"

MANDATORY_KEYS = [
    IDENTIFIER_KEY,
    RDF_FILE_KEY,
    NAMESPACES_KEY,
    # FILE_FORMAT_KEY,
]

ALL_KEYS = [
    IDENTIFIER_KEY,
    RDF_FILE_KEY,
    NAMESPACES_KEY,
    ACTIVE_REL_KEY,
    DEFAULT_REL_KEY,
    FILE_FORMAT_KEY,
    REQUIREMENTS_KEY,
    REFERENCE_STYLE_KEY,
    FILE_HANDLER_KEY,
]
