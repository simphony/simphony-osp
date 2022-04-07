"""Utility functions for printing CUDS objects in a nice way."""

import sys

from osp.core.namespaces import cuba


def pretty_print(cuds_object, file=sys.stdout):
    """Print the given cuds_object in a human readable way.

    The uuid, the type, the ancestors and the description and the contents
    is printed.

    Args:
        cuds_object (Cuds): container to be printed.
        file (TextIOWrapper): The file to print to.
    """
    pp = _pp_cuds_object_name(cuds_object)
    pp += "\n  uid: " + str(cuds_object.uid)
    pp += "\n  type: " + str(cuds_object.oclass)
    pp += "\n  superclasses: " + ", ".join(
        sorted(map(str, cuds_object.oclass.superclasses))
    )
    values_str = _pp_values(cuds_object)
    if values_str:
        pp += "\n  values: " + _pp_values(cuds_object)
    pp += "\n  description: \n    %s\n" % cuds_object.oclass.description
    pp += _pp_subelements(cuds_object)

    print(pp, file=file)


def _pp_cuds_object_name(cuds_object, print_oclass=False):
    """Return the name of the given element following the pretty print format.

    Args:
        cuds_object (Cuds): element to be printed.

    Returns:
        String with the pretty printed text.
    """
    title = "Cuds object" if not print_oclass else "cuds object"
    oclass = (" %s " % cuds_object.oclass) if print_oclass else ""

    if hasattr(cuds_object, "name"):
        name = str(cuds_object.name)
        return "- %s%s named <%s>:" % (oclass, title, name)
    return "- %s%s:" % (oclass, title)


def _pp_subelements(cuds_object, level_indentation="\n  ", visited=None):
    """Recursively formats the subelements from a cuds_object.

    The objects are grouped by ontology class.

    Args:
        cuds_object (Cuds): element to inspect.
        level_indentation (str): common characters to left-pad the text.

    Returns:
        str: string with the pretty printed text
    """
    pp_sub = ""
    filtered_relationships = filter(
        lambda x: x.is_subclass_of(cuba.activeRelationship),
        cuds_object._neighbors.keys(),
    )
    sorted_relationships = sorted(filtered_relationships, key=str)
    visited = visited or set()
    visited.add(cuds_object.uid)
    for i, relationship in enumerate(sorted_relationships):
        pp_sub += level_indentation + " |_Relationship %s:" % relationship
        sorted_elements = sorted(
            cuds_object.iter(rel=relationship, return_rel=True),
            key=lambda x: (
                str(x[0].oclass),
                str(x[1]),
                x[0].name if hasattr(x[0], "name") else False,
            ),
        )
        for j, (element, rel) in enumerate(sorted_elements):
            if rel != relationship:
                continue
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + _pp_cuds_object_name(
                element, print_oclass=True
            )
            if j == len(sorted_elements) - 1:
                indentation += "   "
            else:
                indentation += ".  "
            pp_sub += indentation + "uid: " + str(element.uid)

            if element.uid in visited:
                pp_sub += indentation + "(already printed)"
                continue

            values_str = _pp_values(element, indentation)
            if values_str:
                pp_sub += indentation + _pp_values(element, indentation)

            pp_sub += _pp_subelements(element, indentation, visited)
    return pp_sub


def _pp_values(cuds_object, indentation="\n          "):
    r"""Print the attributes of a cuds object.

    Args:
        cuds_object (Cuds): Print the values of this cuds object.
        indentation (str): The indentation to prepend, defaults to
            "\n          "

    Returns:
        str: The resulting string to print.
    """
    result = []
    sorted_attributes = sorted(
        cuds_object.get_attributes().items(),
        key=lambda x: (str(x[0]), str(x[1])),
    )
    for attribute, value in sorted_attributes:
        if attribute.argname != "name":
            result.append("%s: %s" % (attribute.argname, value))
    if result:
        return indentation.join(result)
