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

def find(uid, cuds_object):
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
            return find(uid, sub)


def find_by(criteria, value, cuds_object):
    """
    Recursively finds the element with a given uid inside a container
    :param criteria: string with the category of the discriminant
    :param value: discriminant value
    :param cuds_object: container in which to search
    :return: the element if found
    """
    try:
        if getattr(cuds_object, criteria) == value:
            return cuds_object
    # If container does not have 'criteria'
    except AttributeError:
        pass
    # A contained element could have it
    for sub in cuds_object.iter():
        return find_by(criteria, value, sub)


def u_type(cuds_object):
    return cuds_object.cuba_key


def pretty_print(cuds_object):
    name = cuds_object.name
    if name is None:
        name = "None"

    pp = "Entity named <" + name + ">:"
    pp += "\n type: " + str(cuds_object.cuba_key)
    pp += "\n uuid: " + str(cuds_object.uid)
    pp += "\n description: " + cuds_object.__doc__
    pp += "\n contains (has a relationship):"
    pp += format_subelements(cuds_object)
    print(pp)


def format_subelements(cuds_object):
    subelements_pp = ""
    for key in cuds_object:
        subelements_pp += "\n  | " + str(key) + ":"
        for element in cuds_object[key]:
            pass
    return subelements_pp
