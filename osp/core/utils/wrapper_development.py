# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from copy import deepcopy
from osp.core.neighbour_dict import NeighbourDictTarget
from osp.core.ontology.datatypes import convert_to
from osp.core.utils.general import get_relationships_between
from osp.core import CUBA


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


def get_neighbour_diff(cuds1, cuds2, mode="all"):
    """Get the uids of neighbours of cuds1 which are no neighbours in cuds2.
    Furthermore get the relationship the neighbours are connected with.
    Optionally filter the considered relationships.

    :param cuds1: A Cuds object.
    :type cuds1: Cuds
    :param cuds2: A Cuds object.
    :type cuds2: Cuds
    :param mode: one of "all", "active", "non-active", whether to consider only
        active or non-active relationships.
    :type mode: str
    :return: List of Tuples that contain the found uids and relationships.
    :rtype: List[Tuple[UUID, Relationship]]
    """
    allowed_modes = ["all", "active", "non-active"]
    if mode not in allowed_modes:
        raise ValueError("Illegal mode specified. Choose one of %s"
                         % allowed_modes)
    if cuds1 is None:
        return []

    result = list()
    # Iterate over all neighbours that are in cuds1 but not cuds2.
    for relationship in cuds1._neighbours.keys():
        if ((
            mode == "active"
            and not relationship.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP)
        ) or (
            mode == "non-active"
            and relationship.is_subclass_of(CUBA.ACTIVE_RELATIONSHIP)
        )):
            continue

        # Get all the neighbours that are no neighbours is cuds2
        old_neighbour_uids = set()
        if cuds2 is not None and relationship in cuds2._neighbours:
            old_neighbour_uids = cuds2._neighbours[relationship].keys()
        new_neighbour_uids = list(
            cuds1._neighbours[relationship].keys() - old_neighbour_uids)
        result += list(zip(new_neighbour_uids,
                           [relationship] * len(new_neighbour_uids)))
    return result


def destroy_cuds_object(cuds_object):
    """Reset all attributes and relationships.
    Use this for example if a cuds object has been deleted on the backend.

    :param cuds_object: The cuds object to destroy
    :type cuds_object: Cuds
    """
    session = cuds_object.session
    if hasattr(session, "_expired") and cuds_object.uid in session._expired:
        session._expired.remove(cuds_object.uid)
    for rel in set(cuds_object._neighbours.keys()):
        del cuds_object._neighbours[rel]
    for attr in cuds_object.oclass.attributes:
        del cuds_object._attr_values[attr.argname]
        del cuds_object._onto_attributes[attr.argname]
    if cuds_object.uid in cuds_object._session._registry:
        del cuds_object._session._registry[cuds_object.uid]
    session._notify_delete(cuds_object)
    cuds_object._oclass = None


def clone_cuds_object(cuds_object):
    """Avoid that the session gets copied.

    :return: A copy of self with the same session
    :rtype: Cuds
    """
    if cuds_object is None:
        return None
    session = cuds_object._session
    clone = deepcopy(cuds_object)
    clone._session = session
    return clone


def create_recycle(oclass, kwargs, session, uid, fix_neighbours=True):
    """Instantiate a cuds_object with a given session.
    If cuds_object with same uid is already in the session,
    this object will be reused.

    :param oclass: The OntologyClass of cuds_object to instantiate
    :type oclass: Cuds
    :param kwargs: The kwargs of the cuds_object
    :type kwargs: Dict[str, Any]
    :param session: The session of the new Cuds object
    :type session: Session
    :param uid: The uid of the new Cuds object
    :type uid: UUID
    :param fix_neighbours: Whether to remove the link from the old neighbours
        to this cuds object, defaults to True
    :type fix_neighbours: bool
    :result: The created cuds object
    :rtype: Cuds
    """
    uid = convert_to(uid, "UUID")
    if hasattr(session, "_expired") and uid in session._expired:
        session._expired.remove(uid)

    # recycle old object
    if uid in session._registry:
        cuds_object = session._registry.get(uid)
        for rel in set(cuds_object._neighbours.keys()):
            if not fix_neighbours:
                del cuds_object._neighbours[rel]
            else:
                cuds_object.remove(rel=rel)
        change_oclass(cuds_object, oclass, kwargs)
    else:  # create new
        cuds_object = oclass(uid=uid, session=session, **kwargs)
    return cuds_object


def create_from_cuds_object(cuds_object, session):
    """Create a copy of the given cuds_object in a different session.
    WARNING: Will not recursively copy children.

    :param cuds_object: The cuds object to copy
    :type cuds_object: Cuds
    :param kwargs: The kwargs of the cuds_object
    :type kwargs: Dict[str, Any]
    :param session: The session of the new Cuds object
    :type session: Session
    :return: A copy of self with the given session.
    :rtype: Cuds
    """
    assert cuds_object.session is not session
    kwargs = {x.argname: getattr(cuds_object, x.argname)
              for x in cuds_object.oclass.attributes}
    clone = create_recycle(oclass=cuds_object.oclass,
                           kwargs=kwargs,
                           session=session,
                           uid=cuds_object.uid,
                           fix_neighbours=False)
    for rel, target_dict in cuds_object._neighbours.items():
        clone._neighbours[rel] = NeighbourDictTarget(dict(), clone, rel)
        for uid, target_oclass in target_dict.items():
            clone._neighbours[rel][uid] = target_oclass
    return clone


def change_oclass(cuds_object, new_oclass, kwargs):
    """Change the oclass of a cuds object. Only allowed if cuds object does
    not have any neighbours.

    :param cuds_object: The cuds object to change the oclass of
    :type cuds_object: Cuds
    :param new_oclass: The new oclass of the cuds object
    :type new_oclass: OntologyClass
    :param kwargs: The keyword arguments used to instantiate
        cuds object of the new oclass
    :type kwargs: Dict[str, Any]
    :return: The cuds object with the changed oclass
    :rtype: Cuds
    """
    cuds_object.session._notify_read(cuds_object)
    # change oclass
    if cuds_object.oclass != new_oclass:
        cuds_object._oclass = new_oclass
        for neighbour in cuds_object.get(rel=CUBA.RELATIONSHIP):
            for rel in get_relationships_between(cuds_object, neighbour):
                neighbour._neighbours[rel.inverse][cuds_object.uid] = \
                    new_oclass

    # update attributes
    attributes = new_oclass._get_attributes_values(kwargs)
    cuds_object._attr_values = {k.argname: k(v) for k, v in attributes.items()}
    cuds_object._onto_attributes = {k.argname: k for k in attributes}
    cuds_object.session._notify_update(cuds_object)
