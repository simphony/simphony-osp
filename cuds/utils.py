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


# Cuds utility methods


def find_cuds(uid, cuds_object):
    """
    Recursively finds the element with a given uid inside a container
    :param uid: unique identifier of the wanted element
    :param cuds_object: container in which to search
    :return: the element if found
    """
    if cuds_object.uid == uid:
        return cuds_object
    else:
        for sub in cuds_object.iter():
            return find_cuds(uid, sub)


def find_cuds_by(criteria, value, cuds_object):
    """
    Recursively finds the element with a given value inside a container

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
    Recursively finds all the elements with a given value inside a container

    :param criteria: string with the category of the discriminant
    :param value: discriminant value
    :param cuds_object: container in which to search
    :return: the element(s) if found
    """

    output = []
    try:
        if getattr(cuds_object, criteria) == value:
            # FIXME: None TypeError with hdf5
            output.append(cuds_object)
    # If container does not have 'criteria'
    except AttributeError:
        pass
    # A contained element could have it
    for sub in cuds_object.iter():
        result = find_all_cuds_by(criteria, value, sub)
        if result is not None:
            output.extend(result)
    return output


def get_definition(cuds_object):
    return cuds_object.__doc__


def get_ancestors(cuds_object):
    ancestors = []
    parent = cuds_object.__class__.__bases__[0]
    while parent != dict:
        ancestors.append(parent.__name__)
        parent = parent.__bases__[0]
    return ancestors


def pretty_print(cuds_object):
    pp = pp_entity_name(cuds_object)
    pp += "\n  uuid: " + str(cuds_object.uid)
    pp += "\n  type: " + str(cuds_object.cuba_key)
    pp += "\n  ancestors: " + ", ".join(get_ancestors(cuds_object))
    pp += "\n  description: " + get_definition(cuds_object)
    pp += pp_subelements(cuds_object)
    print(pp)


def pp_entity_name(cuds_object):
    # In case it is None, street()
    name = str(cuds_object.name)
    return "- Entity named <" + name + ">:"


def pp_subelements(cuds_object, level_indentation="\n  "):
    """
    Recursively formats the subelements from a cuds_object grouped by cuba_key
    :param cuds_object: element to inspect
    :param level_indentation: common characters to left-pad the text
    :return: string with the pretty printed text
    """
    pp_sub = ""
    if cuds_object:
        pp_sub += level_indentation + "contains (has a relationship):"
        for key in cuds_object:
            pp_sub += level_indentation + " |_" + str(key) + ":"
            for element in cuds_object.iter(key):
                indentation = level_indentation + " | "
                pp_sub += indentation + pp_entity_name(element)
                indentation += "  "
                pp_sub += indentation + "uuid: " + str(element.uid)
                pp_sub += pp_subelements(element, indentation)
    return pp_sub
