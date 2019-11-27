import re
from osp.core.ontology.datatypes import ONTOLOGY_DATATYPES

entity_name_regex = r"(_|[A-Z])([A-Z]|[0-9]|_)*"
entity_name_pattern = re.compile(r"^%s$" % entity_name_regex)
qualified_entity_name_pattern = re.compile(
    r"^%s.%s$" % tuple([entity_name_regex] * 2)
)

entity_common_keys = {
    "description": str,
    "!subclass_of": ["class_expression"],
}

class_definition = {
    "attributes": {qualified_entity_name_pattern: str},
    "disjoint_with": ["class_expression"],
    "equivalent_to": ["class_expression"],
}

relationship_definition = {
    "inverse": qualified_entity_name_pattern,
    "default_rel": bool,
    "domain": "class_expression",
    "range": "class_expression",
    "characteristics": [re.compile(r"^(%s)$" % "|".join([
        "reflexive",
        "symmetric",
        "transitive",
        "functional",
        "irreflexive",
        "asymmetric",
        "inversefunctional"
    ]))]
}

attribute_definition = {
    "datatype": re.compile(r"^(%s)(:\d+)*$"
                           % "|".join(map(re.escape, ONTOLOGY_DATATYPES)))
}

format_description = {
    "/": {
        "!VERSION": re.compile(r"^\d+\.\d+(\.\d+)?$"),
        "!NAMESPACE": entity_name_pattern,
        "!ONTOLOGY": {entity_name_pattern: "entity_def"}
    },
    "entity_def": dict(**entity_common_keys, **class_definition,
                       **relationship_definition, **attribute_definition),
    "class_expression": [
        qualified_entity_name_pattern,
        {qualified_entity_name_pattern:
            "relationship_class_expression"},
        {re.compile(r"^(OR|AND)$"): ["class_expression"]},
        {re.compile(r"^NOT$"): "class_expression"}
    ],
    "relationship_class_expression": {
        "!range": "class_expression",
        "cardinality": re.compile(r"^(many|some|\*|\+|\?|\d+\+|\d+-\d|\d+)$"),
        "exclusive": bool
    },
    "class_def": dict(**entity_common_keys, **class_definition),
    "relationship_def": dict(**entity_common_keys, **relationship_definition),
    "attribute_def": dict(**entity_common_keys, **attribute_definition)
}


def validate(yaml_doc, pattern="/", context=""):
    """Check if the yaml doc matched the given pattern.

    :param yaml_doc: The yaml doc to check
    :type yaml_doc: Any
    :param pattern: The pattern to match with the yaml doc, defaults to "/"
    :type pattern: Any, optional
    :param context: The current path in the yaml_doc, defaults to ""
    :type context: str, optional
    :raises ValueError: The YAML doc does not match
    """
    # Pattern is string -> match with format description in dictionary above
    if isinstance(pattern, str):
        _validate_format(yaml_doc, format_description[pattern], context)

    # Pattern is regex -> match regex
    elif hasattr(pattern, "match"):
        if not isinstance(yaml_doc, (str, int, float)):
            raise ValueError("%s must be a string." % context)
        yaml_doc = str(yaml_doc)
        if not pattern.match(yaml_doc):
            raise ValueError("%s does not match %s in %s"
                             % (yaml_doc, pattern, context))

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
            validate(value, value_pattern, context + "/" + key)

    # Pattern is callable -> Check if call throws an error
    else:
        try:
            pattern(yaml_doc)
        except ValueError as e:
            raise ValueError("%s is not of type %s"
                             % (context, pattern)) from e


def _validate_format(yaml_doc, format_desc, context):
    """Match the pattern with the given format description.

    :param yaml_doc: The yaml doc to check
    :type yaml_doc: Any
    :param format_desc: The format description.
    :type format_desc: Union[List, Dict]
    :param context: The current path in the yaml doc.
    :type context: str
    :raises ValueError: The yaml doc does not match the format
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
            raise ValueError("%s has wrong format. Fix one of the following "
                             "errors: \n - %s"
                             % (context, "\n - ".join(map(str, errors))))

    # format description is dict -> check the individuals items
    elif isinstance(format_desc, dict):
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
