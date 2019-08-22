# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.
import pkg_resources
from typing import Set, Type, Callable, List, Union
from uuid import UUID


# General utility methods
def check_arguments(types, *args):
    """
    Checks that the arguments provided are of the certain type(s).

    :param types: tuple with all the allowed types
    :param args: instances to check
    :raises TypeError: if the arguments are not of the correct type
    """
    for arg in args:
        if not isinstance(arg, types):
            message = '{!r} is not a correct object of allowed types {}'
            raise TypeError(message.format(arg, types))


def format_class_name(name):
    """
    Formats a string to CapWords.

    :param name: string to format
    :return: string with the name in CapWords
    """
    fixed_name = name.title().replace("_", "")
    return fixed_name


def find_cuds(criteria, root, rel, all, visited):
    """
    Recursively finds an element inside a container
    by considering the given relationship.

    :param criteria: function that returns True on the Cuds object
        that is searched.
    :param root: Starting point of search
    :param all: Whether to find all cuds with satisfying the criteria.
    :param rel: The relationship (incl. subrelationships) to consider
    :return: the element if found
    """
    if criteria(root):
        return [root] if all else root

    visited = visited or set()
    visited.add(root.uid)
    output = []
    for sub in root.iter(rel=rel):
        if sub.uid not in visited:
            result = find_cuds(criteria, sub, rel, visited)
            if not all and result is not None:
                return result
            if result is not None:
                output += result
    return None if all else output


def find_cuds_by_uid(uid, root, rel, visited):
    """
    Recursively finds an element with given uid inside a container
    by considering the given relationship.

    :param criteria: The uid of the cuds object that is searched.
    :param root: Starting point of search
    :param rel: The relationship (incl. subrelationships) to consider
    :return: the element if found
    """
    return find_cuds(
        criteria=lambda cuds: cuds.uid == uid,
        root=root,
        rel=rel,
        visited=visited
    )


def delete_cuds(cuds_object):
    """
    Deletes a cuds object from the datastructure.
    Removes the relationships to all neighbors.

    :param cuds_object: The cuds object to remove.
    """
    # Method does not allow deletion of the root element of a container
    from cuds.classes import Relationship
    for elem in cuds_object.iter(rel=Relationship):
        cuds_object.remove(elem.uid)


def get_definition(cuds_object):
    """
    Returns the definition of the given cuds object.

    :param cuds_object: cuds object of interest
    :return: the definition of the cuds object
    """
    return cuds_object.__doc__


def get_ancestors(cuds_object):
    """
    Finds the ancestors of the given cuds object.

    :param cuds_object: cuds object of interest
    :return: a list with all the ancestors
    """
    # FIXME: If import in the beginning,
    #  loop with Cuds and check_arguments
    import cuds.classes
    # object from osp_core
    if isinstance(cuds_object, cuds.classes.core.Cuds):
        parent = cuds_object.__class__.__bases__[0]
    # wrapper instance
    else:
        cuba_key = str(cuds_object.cuba_key).replace("CUBA.", "")
        class_name = format_class_name(cuba_key)
        parent = getattr(cuds.classes, class_name).__bases__[0]

    ancestors = []
    while parent != dict:
        ancestors.append(parent.__name__)
        parent = parent.__bases__[0]
    return ancestors


def pretty_print(cuds_object):
    """
    Prints the given cuds object with the uuid, the type,
    the ancestors and the description in a readable way.

    :param cuds_object: container to be printed
    """
    pp = pp_entity_name(cuds_object)
    pp += "\n  uuid: " + str(cuds_object.uid)
    pp += "\n  type: " + str(cuds_object.cuba_key)
    pp += "\n  ancestors: " + ", ".join(get_ancestors(cuds_object))
    values_str = pp_values(cuds_object)
    if values_str:
        pp += "\n  values: " + pp_values(cuds_object)
    pp += "\n  description: " + get_definition(cuds_object)
    pp += pp_subelements(cuds_object)

    print(pp)


def pp_entity_name(cuds_object, cuba=False):
    """
    Returns the name of the given element following the
    pretty print format.

    :param cuds_object: element to be printed
    :return: string with the pretty printed text
    """
    entity = "Entity" if not cuba else "entity"
    cuba = (" %s " % cuds_object.cuba_key) if cuba else ""

    if hasattr(cuds_object, "name"):
        name = str(cuds_object.name)
        return "- %s%s named <%s>:" % (cuba, entity, name)
    return "- %s%s:" % (cuba, entity)


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
        for element in sorted_elements:
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + pp_entity_name(element, cuba=True)
            indentation += "   "
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
    result = []
    for attr in cuds_object.get_attributes(skip=["session", "uid", "name"]):
        value = getattr(cuds_object, attr)
        result.append("%s: %s" % (attr, value))
    if result:
        return indentation.join(result)
