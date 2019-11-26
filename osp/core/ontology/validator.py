import re
from osp.core.ontology.datatypes import ONTOLOGY_DATATYPES

entity_name_regex = r"[A-Z]([A-Z]|[0-9]|_)*"
entity_name_pattern = re.compile(r"^%s$" % entity_name_regex)
qualified_entity_name_pattern = re.compile(
    r"^%s.%s$" % tuple([entity_name_regex] * 2)
)

format_description = {
    "/": {
        "!VERSION": re.compile(r"^\d+\.\d+(\.\d+)?$"),
        "!NAMESPACE": entity_name_pattern,
        "!ONTOLOGY": {qualified_entity_name_pattern: "entity_def"}
    },
    "entity_def": {
        "description": str,
        "!subclass_of": ["class_expression"],
        "inverse": qualified_entity_name_pattern,
        "default_rel": bool,
        "datatype": re.compile(r"^(%s)(:\d+)*$"
                               % "|".join(map(re.escape, ONTOLOGY_DATATYPES))),
        "attributes": {qualified_entity_name_pattern: str},
        "disjoints": ["class_expression"],
        "equivalent_to": ["class_expression"],
        "domain": "class_expression",
        "range": "class_expression",
        "characteristics": re.compile(r"^(%s)$" % "|".join([
            "reflexive",
            "symmetric",
            "transitive",
            "functional",
            "irreflexive",
            "asymmetric",
            "inversefunctional"
        ]))
    },
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
}


def validate(yaml_doc, pattern="/", context=""):
    if isinstance(pattern, str):
        _validate_format(yaml_doc, format_description[pattern], context)
    elif hasattr(pattern, "match"):
        if not isinstance(yaml_doc, (str, int, float)):
            raise ValueError("%s must be a string." % context)
        yaml_doc = str(yaml_doc)
        if not pattern.match(yaml_doc):
            raise ValueError("%s does not match %s in %s"
                             % (yaml_doc, pattern, context))
    elif isinstance(pattern, list):
        assert len(pattern) == 1
        pattern = pattern[0]
        if not isinstance(yaml_doc, list):
            raise ValueError("%s must be a list." % context)
        for i, item in enumerate(yaml_doc):
            validate(item, pattern, "%s/<%s>" % (context, i))
    elif isinstance(pattern, dict):
        assert len(pattern) == 1
        key_pattern = next(iter(pattern.keys()))
        value_pattern = next(iter(pattern.values()))
        if not isinstance(yaml_doc, dict):
            raise ValueError("%s must be a dict." % context)
        for key, value in yaml_doc.items():
            validate(key, key_pattern, context)
            validate(value, value_pattern, context + "/" + key)
    else:
        try:
            pattern(yaml_doc)
        except ValueError as e:
            raise ValueError("%s is not of type %s"
                             % (context, pattern)) from e


def _validate_format(yaml_doc, format_desc, context):
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
    elif isinstance(format_desc, dict):
        allowed_keys = list()
        for key, pattern in format_desc.items():
            if key.startswith("!"):
                key = key[1:]
                if key not in yaml_doc:
                    raise ValueError("%s has to be in %s" % (key, context))
            if key in yaml_doc:
                validate(yaml_doc[key], pattern, context + "/" + key)
            allowed_keys.append(key)
        for key in yaml_doc.keys():
            if key not in allowed_keys:
                raise ValueError("Key %s not allowed in %s" % (key, context))
