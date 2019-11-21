import sys
from osp.core import CUBA


def pretty_print(cuds_object, file=sys.stdout):
    """
    Prints the given cuds_object with the uuid, the type,
    the ancestors and the description in a human readable way.

    :param cuds_object: container to be printed
    :type cuds_object: Cuds
    """
    pp = pp_cuds_object_name(cuds_object)
    pp += "\n  uuid: " + str(cuds_object.uid)
    pp += "\n  type: " + str(cuds_object.oclass)
    pp += "\n  superclasses: " + ", ".join(
        map(str, cuds_object.oclass.superclasses)
    )
    values_str = pp_values(cuds_object)
    if values_str:
        pp += "\n  values: " + pp_values(cuds_object)
    pp += "\n  description: \n    %s\n" % cuds_object.oclass.description
    pp += pp_subelements(cuds_object)

    print(pp, file=file)


def pp_cuds_object_name(cuds_object, print_oclass=False):
    """
    Returns the name of the given element following the
    pretty print format.

    :param cuds_object: element to be printed
    :return: string with the pretty printed text
    """
    title = "Cuds object" if not print_oclass else "cuds object"
    oclass = (" %s " % cuds_object.oclass) if print_oclass else ""

    if hasattr(cuds_object, "name"):
        name = str(cuds_object.name)
        return "- %s%s named <%s>:" % (oclass, title, name)
    return "- %s%s:" % (oclass, title)


def pp_subelements(cuds_object, level_indentation="\n  ", visited=None):
    """
    Recursively formats the subelements from a cuds_object grouped
        by ontology class.

    :param cuds_object: element to inspect
    :param level_indentation: common characters to left-pad the text
    :return: string with the pretty printed text
    """
    pp_sub = ""
    filtered_relationships = filter(
        lambda x: x.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP),
        cuds_object._neighbours.keys())
    sorted_relationships = sorted(filtered_relationships, key=str)
    visited = visited or set()
    visited.add(cuds_object.uid)
    for i, relationship in enumerate(sorted_relationships):
        pp_sub += level_indentation \
            + " |_Relationship %s:" % relationship
        sorted_elements = sorted(cuds_object.iter(rel=relationship),
                                 key=lambda x: str(x.oclass))
        for j, element in enumerate(sorted_elements):
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + pp_cuds_object_name(element,
                                                        print_oclass=True)
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
    for value in cuds_object.oclass.attributes:
        if value.argname != "name":
            v = getattr(cuds_object, value.argname)
            result.append("%s: %s" % (value.argname, v))
    if result:
        return indentation.join(result)
