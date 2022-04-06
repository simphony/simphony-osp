"""Validate the format of a YAML ontology file."""

import logging
import re

from osp.core.ontology.parser.yml.keywords import (
    ATTRIBUTES_KEY,
    AUTHOR_KEY,
    CARDINALITY_KEY,
    CHARACTERISTICS,
    CHARACTERISTICS_KEY,
    DATATYPE_KEY,
    DATATYPES,
    DEFAULT_REL_KEY,
    DESCRIPTION_KEY,
    DISJOINTS_KEY,
    DOMAIN_KEY,
    EQUIVALENT_TO_KEY,
    EXCLUSIVE_KEY,
    INVERSE_KEY,
    NAMESPACE_KEY,
    ONTOLOGY_KEY,
    RANGE_KEY,
    REQUIREMENTS_KEY,
    SUPERCLASSES_KEY,
    TARGET_KEY,
    VERSION_KEY,
)

logger = logging.getLogger(__name__)

entity_name_regex = r"([a-zA-Z])([a-zA-Z]|[0-9]|_)*"
namespace_name_regex = r"([a-zA-Z])([a-zA-Z]|[0-9]|_)*"
namespace_name_pattern = re.compile(namespace_name_regex)
entity_name_pattern = re.compile(r"^%s$" % entity_name_regex)
qualified_entity_name_pattern = re.compile(
    r"^%s\.%s$" % (namespace_name_regex, entity_name_regex)
)

entity_common_keys = {
    DESCRIPTION_KEY: str,
    "!" + SUPERCLASSES_KEY: ["class_expression"],
}

class_definition = {
    ATTRIBUTES_KEY: {qualified_entity_name_pattern: None},
    DISJOINTS_KEY: ["class_expression"],
    EQUIVALENT_TO_KEY: ["class_expression"],
}

relationship_definition = {
    INVERSE_KEY: qualified_entity_name_pattern,
    DEFAULT_REL_KEY: bool,
    DOMAIN_KEY: "class_expression",
    RANGE_KEY: "class_expression",
    CHARACTERISTICS_KEY: [re.compile(r"^(%s)$" % "|".join(CHARACTERISTICS))],
}

attribute_definition = {
    DATATYPE_KEY: re.compile(
        r"^(VECTOR:)?(%s)(:\d+)*$" % "|".join(map(re.escape, DATATYPES))
    )
}

format_description = {
    "/": {
        "!" + VERSION_KEY: re.compile(r"^\d+\.\d+(\.\d+)?$"),
        "!" + NAMESPACE_KEY: namespace_name_pattern,
        "!" + ONTOLOGY_KEY: {entity_name_pattern: "entity_def"},
        DEFAULT_REL_KEY: qualified_entity_name_pattern,
        AUTHOR_KEY: str,
        REQUIREMENTS_KEY: [entity_name_pattern],
    },
    "entity_def": dict(
        **entity_common_keys,
        **class_definition,
        **relationship_definition,
        **attribute_definition
    ),
    "class_expression": [
        qualified_entity_name_pattern,
        {qualified_entity_name_pattern: "relationship_class_expression"},
        {re.compile(r"^(or|and)$"): ["class_expression"]},
        {re.compile(r"^not$"): "class_expression"},
    ],
    "relationship_class_expression": {
        "!" + TARGET_KEY: "class_expression",
        CARDINALITY_KEY: re.compile(
            r"^(many|some|\*|\+|\?|\d+\+|\d+-\d|\d+)$"
        ),
        EXCLUSIVE_KEY: bool,
    },
    "class_def": dict(**entity_common_keys, **class_definition),
    "relationship_def": dict(**entity_common_keys, **relationship_definition),
    "attribute_def": dict(**entity_common_keys, **attribute_definition),
}


def validate(yaml_doc, pattern="/", context=""):
    """Check if the yaml doc matched the given pattern.

    Args:
        yaml_doc (dict): The yaml doc to check
        pattern (Any, optional): The pattern to match with the yaml doc.
            Defaults to "/".
        context (str, optional): The current path in the yaml_doc.
            Defaults to "".

    Raises:
        ValueError: The YAML doc does not match
    """
    logger.debug("Validate format of %s" % context)
    if pattern is None:
        return

    # Pattern is string -> match with format description in dictionary above
    elif isinstance(pattern, str):
        _validate_format(yaml_doc, format_description[pattern], context)

    # Pattern is regex -> match regex
    elif hasattr(pattern, "match"):
        if not isinstance(yaml_doc, (str, int, float)):
            raise ValueError("%s must be a string." % context)
        yaml_doc = str(yaml_doc)
        if not pattern.match(yaml_doc):
            raise ValueError(
                "%s does not match %s in %s" % (yaml_doc, pattern, context)
            )

    # Pattern is list -> Match list items of yaml doc
    elif isinstance(pattern, list):
        assert len(pattern) == 1
        pattern = pattern[0]
        if not isinstance(yaml_doc, list):
            raise ValueError("%s must be a list." % context)
        for i, item in enumerate(yaml_doc):
            validate(item, pattern, "%s/<%s>" % (context, i))

    # Pattern is dict -> Match dict items of yaml doc
    elif isinstance(pattern, dict):
        assert len(pattern) == 1
        key_pattern = next(iter(pattern.keys()))
        value_pattern = next(iter(pattern.values()))
        if not isinstance(yaml_doc, dict):
            raise ValueError("%s must be a dict." % context)
        for key, value in yaml_doc.items():
            validate(key, key_pattern, context)
            validate(value, value_pattern, context + "/" + str(key))

    # Pattern is callable -> Check if call throws an error
    else:
        error = ValueError("%s is not of type %s" % (context, pattern))
        try:
            if pattern(yaml_doc) != yaml_doc:
                raise error
        except ValueError as e:
            raise error from e


def _validate_format(yaml_doc, format_desc, context):
    """Match the pattern with the given format description.

    Args:
        yaml_doc (Any): The yaml doc to check
        format_desc (Union[List, Dict]): The format description.
        context (str): The current path in the yaml doc.

    Raises:
        ValueError: The yaml doc does not match the format
    """
    # format description is list -> one of its elements must match
    if isinstance(format_desc, list):
        errors = list()
        for pattern in format_desc:
            try:
                validate(yaml_doc, pattern, context)
            except ValueError as e:
                errors += [e]
        if len(errors) == len(format_desc):
            raise ValueError(
                "%s has wrong format. Fix one of the following "
                "errors: \n - %s" % (context, "\n - ".join(map(str, errors)))
            )

    # format description is dict -> check the individuals items
    elif isinstance(format_desc, dict):
        if not isinstance(yaml_doc, dict):
            raise ValueError("Value at %s must be a dictionary" % context)
        allowed_keys = list()
        for key, pattern in format_desc.items():
            if key.startswith("!"):  # starting with ! means the key must exist
                key = key[1:]
                if key not in yaml_doc:
                    raise ValueError("%s has to be in %s" % (key, context))
            if key in yaml_doc:
                validate(yaml_doc[key], pattern, context + "/" + key)
            allowed_keys.append(key)
        for key in yaml_doc.keys():  # no other keys are allowed
            if key not in allowed_keys:
                raise ValueError("Key %s not allowed in %s" % (key, context))
