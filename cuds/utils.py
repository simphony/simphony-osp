# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import sys
import inspect
import requests
import json
from copy import deepcopy
from cuds.metatools.ontology_datatypes import convert_to


# General utility methods
def check_arguments(types, *args):
    """
    Checks that the arguments provided are of the certain type(s).

    :param types: tuple with all the allowed types
    :type types: Union[Type, Tuple[Type]]
    :param args: instances to check
    :type args: Any
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
    :type name: str
    :return: string with the name in CapWords
    :rtype: str
    """
    fixed_name = name.title().replace("_", "")
    return fixed_name


def post(url, cuds_object, max_depth=float("inf")):
    from cuds.classes import ActiveRelationship
    from cuds.classes.core.session.transport.transport_util import serializable
    cuds_objects = find_cuds_object(criterion=lambda x: True,
                                    root=cuds_object,
                                    rel=ActiveRelationship,
                                    find_all=True,
                                    max_depth=max_depth)
    serialized = json.dumps(serializable(cuds_objects))
    return requests.post(url=url,
                         data=serialized,
                         headers={"content_type": "application/json"})


def find_cuds_object(criterion, root, rel, find_all, max_depth=float("inf"),
                     current_depth=0, visited=None):
    """
    Recursively finds an element inside a container
    by considering the given relationship.

    :param criterion: function that returns True on the Cuds object
        that is searched.
    :type criterion: Callable
    :param root: Starting point of search
    :type root: Cuds
    :param rel: The relationship (incl. subrelationships) to consider
    :type rel: Type[Relationship]
    :param find_all: Whether to find all cuds_objects with satisfying
        the criterion.
    :type find_all: bool
    :param max_depth: The maximum depth for the search.
    :type max_depth: Union(float, int)
    :return: the element if found
    :rtype: Union[Cuds, List[Cuds]]
    """
    visited = visited or set()
    visited.add(root.uid)
    output = [root] if criterion(root) else []

    if output and not find_all:
        return output[0]

    if current_depth < max_depth:
        for sub in root.iter(rel=rel):
            if sub.uid not in visited:
                result = find_cuds_object(criterion=criterion,
                                          root=sub,
                                          rel=rel,
                                          find_all=find_all,
                                          max_depth=max_depth,
                                          current_depth=current_depth + 1,
                                          visited=visited)
                if not find_all and result is not None:
                    return result
                if result is not None:
                    output += result
    return output if find_all else None


def find_cuds_object_by_uid(uid, root, rel):
    """
    Recursively finds an element with given uid inside a cuds object
    by considering the given relationship.

    :param uid: The uid of the cuds_object that is searched.
    :type uid: UUID
    :param root: Starting point of search
    :type root: Cuds
    :param rel: The relationship (incl. subrelationships) to consider
    :type rel: Type[Relationship]
    :return: the element if found
    :rtype: Cuds
    """
    return find_cuds_object(
        criterion=lambda cuds_object: cuds_object.uid == uid,
        root=root,
        rel=rel,
        find_all=False,
    )


def find_cuds_objects_by_cuba_key(cuba_key, root, rel):
    """
    Recursively finds an element with given cuba key inside a cuds object
    by considering the given relationship.

    :param cuba_key: The cuba_key of the cuds_object that is searched.
    :type uid: CUBA
    :param root: Starting point of search
    :type root: Cuds
    :param rel: The relationship (incl. subrelationships) to consider
    :type rel: Type[Relationship]
    :return: The found suds objects.
    :rtype: List[Cuds]
    """
    return find_cuds_object(
        criterion=lambda cuds_object: cuds_object.cuba_key == cuba_key,
        root=root,
        rel=rel,
        find_all=True
    )


def find_cuds_objects_by_attribute(attribute, value, root, rel):
    """Recursively finds a cuds object by attribute and value by
    only considering the given relationship.

    :param attribute: The attribute to look for
    :type attribute: str
    :param value: The corresponding value to filter by
    :type value: Any
    :param root: The root for the search
    :type root: Cuds
    :param rel: The relationship (+ subrelationships) to consider.
    :type rel: Type[Relationship]
    :return: The found cuds objects.
    :rtype: List[Cuds]
    """
    return find_cuds_object(
        criterion=(lambda cuds_object: hasattr(cuds_object, attribute)
                   and getattr(cuds_object, attribute) == value),
        root=root,
        rel=rel,
        find_all=True
    )


def find_relationships(find_rel, root, consider_rel, find_sub_rels=False):
    """Find the given relationship in the subtree of the given root.

    :param find_rel: The relationship to find
    :type find_rel: Type[Relationship]
    :param root: Only consider the subgraph rooted in this root.
    :type root: Cuds
    :param consider_rel: Only consider these relationships when searching.
    :type consider_rel: Type[Relationship]
    :return: The cuds objects having the given relationship.
    :rtype: List[Cuds]
    """
    if find_sub_rels:
        def criterion(cuds_object):
            return cuds_object.contains(find_rel)
    else:
        def criterion(cuds_object):
            return find_rel in cuds_object

    return find_cuds_object(
        criterion=criterion,
        root=root,
        rel=consider_rel,
        find_all=True
    )


def remove_cuds_object(cuds_object):
    """
    Remove a cuds_object from the datastructure.
    Removes the relationships to all neighbors.
    To delete it from the registry you must call the
    sessions prune method afterwards.

    :param cuds_object: The cuds_object to remove.
    """
    # Method does not allow deletion of the root element of a container
    from cuds.classes import Relationship
    for elem in cuds_object.iter(rel=Relationship):
        cuds_object.remove(elem.uid, rel=Relationship)


def get_definition(cuds_object):
    """
    Returns the definition of the given cuds_object.

    :param cuds_object: cuds_object of interest
    :return: the definition of the cuds_object
    """
    return cuds_object.__doc__


def get_ancestors(cuds_object_or_class):
    """
    Finds the ancestors of the given cuds object or class.

    :param cuds_object_or_class: cuds object or class of interest
    :type cuds_object_or_class: Union[Cuds, Type[Cuds]]
    :return: a list with all the ancestors
    """
    import cuds.classes
    # object from osp_core
    if isinstance(cuds_object_or_class, cuds.classes.core.Cuds):
        parent = cuds_object_or_class.__class__.__bases__[0]
    # wrapper instance
    else:
        cuba_key = str(cuds_object_or_class.cuba_key).replace("CUBA.", "")
        class_name = format_class_name(cuba_key)
        parent = getattr(cuds.classes, class_name).__bases__[0]

    ancestors = []
    while parent != dict:
        ancestors.append(parent.__name__)
        parent = parent.__bases__[0]
    return ancestors


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


def destroy_cuds_object(cuds_object):
    """Reset all attributes and relationships.
    Use this for example if a cuds object has been deleted on the backend.

    :param cuds_object: The cuds object to destroy
    :type cuds_object: Cuds
    """
    session = cuds_object.session
    if hasattr(session, "_expired") and cuds_object.uid in session._expired:
        session._expired.remove(cuds_object.uid)
    for rel in set(cuds_object.keys()):
        del cuds_object[rel]
    for attr in cuds_object.get_attributes(skip=["session", "uid"]):
        setattr(cuds_object, "_" + attr, None)
    if cuds_object.uid in cuds_object._session._registry:
        del cuds_object._session._registry[cuds_object.uid]


def clone_cuds_object(cuds_object):
    """Avoid that the session gets copied.

    :return: A copy of self with the same session
    :rtype: Cuds
    """
    if cuds_object is None:
        return None
    session = cuds_object._session
    if "_session" in cuds_object.__dict__:
        del cuds_object.__dict__["_session"]
    clone = deepcopy(cuds_object)
    clone._session = session
    cuds_object._session = session
    return clone


def create_for_session(entity_cls, kwargs, session):
    """Instantiate a cuds_object with a given session.
    If cuds_object with same uid is already in the session,
    this object will be reused.

    :param entity_cls: The type of cuds_object to instantiate
    :type entity_cls: Cuds
    :param kwargs: The kwargs of the cuds_object
    :type kwargs: Dict[str, Any]
    :param session: The session of the new Cuds object
    :type session: Session
    """
    from cuds.classes import Cuds
    uid = convert_to(kwargs["uid"], "UUID")
    if hasattr(session, "_expired") and uid in session._expired:
        session._expired.remove(uid)

    # recycle old object
    if uid in session._registry:
        cuds_object = session._registry.get(uid)
        if type(cuds_object) == entity_cls:
            for key, value in kwargs.items():
                if key not in cuds_object.get_attributes():
                    raise TypeError
                if key not in ["uid", "session"]:
                    setattr(cuds_object, key, value)
            for rel in set(cuds_object.keys()):
                del cuds_object[rel]
            return cuds_object

    # create new
    if "session" in inspect.getfullargspec(entity_cls.__init__).args:
        kwargs["session"] = session
    default_session = Cuds._session
    Cuds._session = session
    cuds_object = entity_cls(**kwargs)
    Cuds._session = default_session
    cuds_object._session = session
    session.store(cuds_object)
    return cuds_object


def create_from_cuds_object(cuds_object, session):
    """Create a copy of the given cuds_object in a different session.
    WARNING: Will not recursively copy children.

    :return: A copy of self with the given session.
    :rtype: Cuds
    """
    assert cuds_object.session is not session
    attributes = cuds_object.get_attributes(skip="session")
    values = [getattr(cuds_object, x) for x in attributes]
    kwargs = dict(zip(attributes, values))
    entity_cls = type(cuds_object)
    clone = create_for_session(entity_cls, kwargs, session)
    for key, uid_cuba in cuds_object.items():
        clone[key] = dict()
        for uid, cuba in uid_cuba.items():
            clone[key][uid] = cuba
    return clone
