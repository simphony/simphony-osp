from copy import deepcopy

DEFAULT = {
    "check_relationship_supported": True,
    "check_cardinalities": True,
    "default_cardinality": "many"
}

MODES = {
    "ignore": {
        "check_relationship_supported": False,
        "check_cardinalities": False,
        "default_cardinality": "many"
    },
    "strict": {
        "check_relationship_supported": True,
        "check_cardinalities": True,
        "default_cardinality": "many"
    },
    "minimum_requirements": {
        "check_relationship_supported": False,
        "check_cardinalities": True,
        "default_cardinality": "many"
    }
}


def get_parsed_settings(parsed_yaml_doc):
    settings = deepcopy(DEFAULT)

    # Check mode
    if "ONTOLOGY_MODE" in parsed_yaml_doc:
        if parsed_yaml_doc["ONTOLOGY_MODE"] not in MODES:
            raise ValueError("Invalid ontology mode specified!")
        settings.update(MODES[parsed_yaml_doc["ONTOLOGY_MODE"]])

    # check settings
    if "CUDS_SETTINGS" in parsed_yaml_doc:
        settings.update(parsed_yaml_doc["CUDS_SETTINGS"])
    return settings
