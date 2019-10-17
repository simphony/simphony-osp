# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.
import pkg_resources


# General utility methods

def check_arguments(types, *args):
    """
    Checks that the arguments provided are of the certain type(s).

    :param types: tuple with all the allowed types
    :param args: instances to check
    :raises TypeError: if the arguments are not of the correct type
    """
    if types == 'all_simphony_wrappers':
        installed = pkg_resources.iter_entry_points('wrappers')
        types = tuple((wrapper.load() for wrapper in installed))
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


# Cuds utility methods

def filter_cuds_attr(cuds_object):
    """
    Filters the non-relevant attributes from a cuds object.

    :return: set with the filtered, relevant attributes
    """
    # Filter the magic functions
    attributes = [a for a in dir(cuds_object) if not a.startswith("__")]
    # Filter the added methods
    attributes = \
        [a for a in attributes if not callable(getattr(cuds_object, a))]
    # Filter the explicitly unwanted attributes
    attributes = [a for a in attributes if a not in {'restricted_keys'}]

    return set(attributes)


def find_cuds(uid, cuds_object):
    """
    Recursively finds the element with a given uid inside a container.

    :param uid: unique identifier of the wanted element
    :param cuds_object: container in which to search
    :return: the element if found
    """
    if cuds_object.uid == uid:
        return cuds_object
    else:
        found_object = None
        for sub in cuds_object.iter():
            found_object = find_cuds(uid, sub)
            if found_object is not None:
                return found_object
        return found_object


def delete_cuds(uid, cuds_object):
    """
    Recursively finds all parents of the element with a given uid inside a
    container and invokes \ref DataContainer::remove() on it.

    :param uid: unique identifier of the element to be deleted
    :param cuds_object: container in which to search for the element
    :return: true, in case one or more instances of the element were deleted
             false, otherwise
    """
    # Method does not allow deletion of the root element of a container
    if cuds_object.uid == uid:
        return False

    deleted_flag = False
    # Search for the element in the first layer of the container
    for sub_cuds in cuds_object.iter():
        if sub_cuds.uid == uid:
            deleted_flag = True
    if deleted_flag:
        cuds_object.remove(uid)

    # Recursively visit elements of the container
    for sub_cuds in cuds_object.iter():
        deleted_flag |= delete_cuds(uid, sub_cuds)
    return deleted_flag


def find_cuds_by(criteria, value, cuds_object):
    """
    Recursively finds the element with a given value inside a container.

    :param criteria: string with the category of the discriminant
    :param value: discriminant value
    :param cuds_object: container in which to search
    :return: the element if found
    """
    try:
        if getattr(cuds_object, criteria) == value:
            return cuds_object
    # If container does not have 'criteria'
    except (AttributeError, KeyError):
        pass
    # A contained element could have it
    for sub in cuds_object.iter():
        result = find_cuds_by(criteria, value, sub)
        if result is not None:
            return result


def find_all_cuds_by(criteria, value, cuds_object):
    """
    Recursively finds all the elements with a given value inside a container.

    :param criteria: string with the category of the discriminant
    :param value: discriminant value
    :param cuds_object: container in which to search
    :return: the element(s) if found
    """

    output = []
    try:
        if getattr(cuds_object, criteria) == value:
            output.append(cuds_object)
    # If container does not have 'criteria'
    except (AttributeError, KeyError):
        pass
    # A contained element could have it
    for sub in cuds_object.iter():
        result = find_all_cuds_by(criteria, value, sub)
        if result is not None:
            output.extend(result)
    return output


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
    # If import in the beginning, loop with DataContainer
    import cuds.classes
    # object from osp_core
    if isinstance(cuds_object, cuds.classes.core.DataContainer):
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
    pp += "\n  description: " + get_definition(cuds_object)
    if hasattr(cuds_object, 'value'):
        pp += "value--> " + str(cuds_object.value)
        if hasattr(cuds_object, 'unit'):
            pp += "\t unit--> " + str(cuds_object.unit)
    pp += pp_subelements(cuds_object)
    print(pp)


def pp_entity_name(cuds_object):
    """
    Returns the name of the given element following the
    pretty print format.

    :param cuds_object: element to be printed
    :return: string with the pretty printed text
    """
    name = str(cuds_object.name)
    return "- Entity named <" + name + ">:"


def pp_subelements(cuds_object, level_indentation="\n  "):
    """
    Recursively formats the subelements from a cuds_object grouped by cuba_key.

    :param cuds_object: element to inspect
    :param level_indentation: common characters to left-pad the text
    :return: string with the pretty printed text
    """
    pp_sub = ""
    if cuds_object:
        pp_sub += level_indentation + "contains (has a relationship):"
        # Subelements are no longer grouped by cuba_key,
        #  for wrapper interoperability
        current_cuba = ""
        for element in cuds_object.iter():
            if current_cuba != element.cuba_key:
                current_cuba = element.cuba_key
                pp_sub += level_indentation + " |_" + str(current_cuba) + ":"

            indentation = level_indentation + " | "
            pp_sub += indentation + pp_entity_name(element)
            indentation += "  "
            pp_sub += indentation + "uuid: " + str(element.uid)
            if hasattr(element, 'value'):
                pp_sub += indentation + "value--> " + str(element.value)
                if hasattr(element, 'unit'):
                    pp_sub += "\t unit--> " + str(element.unit)

            pp_sub += pp_subelements(element, indentation)
    return pp_sub
