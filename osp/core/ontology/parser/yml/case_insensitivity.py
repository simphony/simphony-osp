"""This file exists for backwards compatibility reasons."""

from osp.core.ontology.cuba import rdflib_cuba


def get_case_insensitive_alternative(name, is_cuba):
    """Get an alternative naming convention for the given name.

    Allows backwards compatibility.

    Args:
        name (str): The name
        is_cuba (bool): Whether the name is from the cuba namespace

    Returns:
        str: An alternative name (different naming convetion)
    """
    given = name
    name = name[0].upper()
    if (
        not is_cuba
        and any(x.islower() for x in given)
        and any(x.isupper() for x in given)
    ):
        for x in given[1:]:
            if x.isupper():
                name += "_"
            name += x
        name = name.upper()
        return name

    elif not is_cuba:
        return given.upper()

    elif is_cuba and "_" in given[1:] or all(x.isupper() for x in given):
        upper = False
        for x in given[1:]:
            if x == "_":
                upper = True
                continue

            name += x.upper() if upper else x.lower()
            upper = False
        if name in rdflib_cuba:
            return name
        name = name[0].lower() + name[1:]
        if name in rdflib_cuba:
            return name

    elif is_cuba and given[0].isupper():
        name = given[0].lower() + given[1:]
        if name in rdflib_cuba:
            return name

    elif is_cuba and given[0].islower():
        name = given[0].upper() + given[1:]
        if name in rdflib_cuba:
            return name
