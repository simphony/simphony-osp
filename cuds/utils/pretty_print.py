# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sys
from cuds.utils import get_ancestors
from cuds.utils import get_definition


def pretty_print(cuds_object, file=sys.stdout):
    """
    Prints the given cuds_object with the uuid, the type,
    the ancestors and the description in a human readable way.

    :param cuds_object: container to be printed
    :type cuds_object: Cuds
    """
    pp = pp_cuds_object_name(cuds_object)
    pp += "\n  uuid: " + str(cuds_object.uid)
    pp += "\n  type: " + str(cuds_object.cuba_key)
    pp += "\n  ancestors: " + ", ".join(get_ancestors(cuds_object))
    values_str = pp_values(cuds_object)
    if values_str:
        pp += "\n  values: " + pp_values(cuds_object)
    pp += "\n  description: " + get_definition(cuds_object)
    pp += pp_subelements(cuds_object)

    print(pp, file=file)


def pp_cuds_object_name(cuds_object, cuba=False):
    """
    Returns the name of the given element following the
    pretty print format.

    :param cuds_object: element to be printed
    :return: string with the pretty printed text
    """
    title = "Cuds object" if not cuba else "cuds object"
    cuba = (" %s " % cuds_object.cuba_key) if cuba else ""

    if hasattr(cuds_object, "name"):
        name = str(cuds_object.name)
        return "- %s%s named <%s>:" % (cuba, title, name)
    return "- %s%s:" % (cuba, title)


def pp_subelements(cuds_object, level_indentation="\n  ", visited=None):
    """
    Recursively formats the subelements from a cuds_object grouped by cuba_key.

    :param cuds_object: element to inspect
    :param level_indentation: common characters to left-pad the text
    :return: string with the pretty printed text
    """
    from cuds.classes import ActiveRelationship
    pp_sub = ""
    filtered_relationships = filter(
        lambda x: issubclass(x, ActiveRelationship),
        cuds_object.keys())
    sorted_relationships = sorted(filtered_relationships, key=str)
    visited = visited or set()
    visited.add(cuds_object.uid)
    for i, relationship in enumerate(sorted_relationships):
        pp_sub += level_indentation \
            + " |_Relationship %s:" % relationship.cuba_key
        sorted_elements = sorted(cuds_object.iter(rel=relationship),
                                 key=lambda x: str(x.cuba_key))
        for j, element in enumerate(sorted_elements):
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + pp_cuds_object_name(element, cuba=True)
            if j == len(sorted_elements) - 1:
                indentation += "   "
            else:
                indentation += ".  "
            pp_sub += indentation + "uuid: " + str(element.uid)

            if element.uid in visited:
                pp_sub += indentation + "(already printed)"
                continue

            values_str = pp_values(element, indentation)
            if values_str:
                pp_sub += indentation + pp_values(element, indentation)

            pp_sub += pp_subelements(element, indentation, visited)
    return pp_sub


def pp_values(cuds_object, indentation="\n          "):
    """Print the attributes of a cuds object.

    :param cuds_object: Print the values of this cuds object.
    :type cuds_object: Cuds
    :param indentation: The indentation to prepend, defaults to "\n          "
    :type indentation: str, optional
    :return: The resulting string to print.
    :rtype: [type]
    """
    result = []
    for attr in cuds_object.get_attributes(skip=["session", "uid", "name"]):
        value = getattr(cuds_object, attr)
        result.append("%s: %s" % (attr, value))
    if result:
        return indentation.join(result)
