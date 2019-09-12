# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import inspect
from copy import copy, deepcopy
import pkg_resources
from typing import Set, Type, Callable, List, Union
from uuid import UUID
from cuds.metatools.ontology_datatypes import convert_to


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
        for j, element in enumerate(sorted_elements):
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + pp_entity_name(element, cuba=True)
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
    result = []
    for attr in cuds_object.get_attributes(skip=["session", "uid", "name"]):
        value = getattr(cuds_object, attr)
        result.append("%s: %s" % (attr, value))
    if result:
        return indentation.join(result)


def destruct_cuds(entity):
    for rel in set(entity.keys()):
        del entity[rel]
    for attr in entity.get_attributes(skip=["session", "uid"]):
        setattr(entity, "_" + attr, None)
    if entity.uid in entity._session._registry:
        del entity._session._registry[entity.uid]


def clone_cuds(entity, new_session=None):
    """Avoid that the session gets copied.

    :return: A copy of self with the same session
    :rtype: Cuds
    """
    session = entity._session
    if "_session" in entity.__dict__:
        del entity.__dict__["_session"]
    clone = deepcopy(entity)
    clone._session = new_session or session
    return clone


def create_for_session(entity_cls, kwargs, session, recycle_old=True):
    """Instantiate a cuds object with a given session

    :param entity_cls: The type of cuds object to instantiate
    :type entity_cls: Cuds
    :param kwargs: The kwargs of the cuds object
    :type kwargs: Dict[str, Any]
    :param session: The session of the new Cuds object
    :type session: Session
    :param recycle_old: Whether to recycle old objects with same uid already
        in session
    :type recycle_old: bool
    """
    uid = convert_to(kwargs["uid"], "UUID")
    if hasattr(session, "_expired") and uid in session._expired:
        session._expired.remove(uid)

    # recycle old object
    if uid in session._registry and recycle_old:
        cuds = session._registry.get(uid)
        if type(cuds) == entity_cls:
            for key, value in kwargs.items():
                if key not in cuds.get_attributes():
                    raise TypeError
                if key not in ["uid", "session"]:
                    setattr(cuds, key, value)
            for rel in set(cuds.keys()):
                del cuds[rel]
            return cuds

    # create new
    if "session" in inspect.getfullargspec(entity_cls.__init__).args:
        kwargs["session"] = session
    default_session = entity_cls._session
    entity_cls._session = session
    cuds = entity_cls(**kwargs)
    entity_cls._session = default_session
    cuds._session = session
    return cuds


def create_from_cuds(entity, new_session=None):
    """Avoid that the session gets copied.

    :return: A copy of self with the same session
    :rtype: Cuds
    """
    attributes = entity.get_attributes(skip="session")
    values = [getattr(entity, x) for x in attributes]
    kwargs = dict(zip(attributes, values))
    entity_cls = type(entity)
    clone = create_for_session(entity_cls, kwargs,
                               new_session or entity.session,
                               recycle_old=True)
    for key, uid_cuba in entity.items():
        clone[key] = dict()
        for uid, cuba in uid_cuba.items():
            clone[key][uid] = cuba
    return clone
