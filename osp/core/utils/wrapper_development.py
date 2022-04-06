"""Utilities useful for Wrapper developers."""

from copy import deepcopy

import rdflib

from osp.core.namespaces import cuba
from osp.core.ontology.datatypes import convert_to
from osp.core.utils.general import get_relationships_between


# General utility methods
def check_arguments(types, *args):
    """Check that the arguments provided are of the certain type(s).

    Args:
        types (Union[Type, Tuple[Type]]): tuple with all the allowed types
        args (Any): instances to check

    Raises:
        TypeError: if the arguments are not of the correct type
    """
    for arg in args:
        if not isinstance(arg, types):
            message = "{!r} is not a correct object of allowed types {}"
            raise TypeError(message.format(arg, types))


def get_neighbor_diff(cuds1, cuds2, mode="all"):
    """Get the ids of neighbors of cuds1 which are no neighbors in cuds2.

    Furthermore get the relationship the neighbors are connected with.
    Optionally filter the considered relationships.

    Args;
        cuds1 (Cuds): A Cuds object.
        cuds2 (Cuds): A Cuds object.
        mode (str): one of "all", "active", "non-active", whether to consider
            only.
        active or non-active relationships.

    Returns:
        List[Tuple[Union[UUID, URIRef], Relationship]]: List of Tuples that
            contain the found uids and relationships.
    """
    allowed_modes = ["all", "active", "non-active"]
    if mode not in allowed_modes:
        raise ValueError(
            "Illegal mode specified. Choose one of %s" % allowed_modes
        )
    if cuds1 is None:
        return []

    result = list()
    # Iterate over all neighbors that are in cuds1 but not cuds2.
    for relationship in cuds1._neighbors.keys():
        if (
            mode == "active"
            and not relationship.is_subclass_of(cuba.activeRelationship)
        ) or (
            mode == "non-active"
            and relationship.is_subclass_of(cuba.activeRelationship)
        ):
            continue

        # Get all the neighbors that are no neighbors is cuds2
        old_neighbor_uids = set()
        if cuds2 is not None and relationship in cuds2._neighbors:
            old_neighbor_uids = cuds2._neighbors[relationship].keys()
        new_neighbor_uids = list(
            cuds1._neighbors[relationship].keys() - old_neighbor_uids
        )
        result += list(
            zip(new_neighbor_uids, [relationship] * len(new_neighbor_uids))
        )
    return result


def clone_cuds_object(cuds_object):
    """Avoid that the session gets copied.

    Returns:
        Cuds: A copy of self with the same session.
    """
    if cuds_object is None:
        return None
    session = cuds_object._session
    clone = deepcopy(cuds_object)
    clone._session = session
    return clone


def create_recycle(
    oclass, kwargs, session, uid, fix_neighbors=True, _force=False
):
    """Instantiate a cuds_object with a given session.

    If cuds_object with same uid is already in the session,
    this object will be reused.

    Args:
        oclass (Cuds): The OntologyClass of cuds_object to instantiate
        kwargs (Dict[str, Any]): The kwargs of the cuds_object
        session (Session): The session of the new Cuds object
        uid (Union[UUID, URIRef): The uid of the new Cuds object
        fix_neighbors (bool): Whether to remove the link from the old neighbors
            to this cuds object, defaults to True
        _force (bool): Skip sanity checks.

    Returns:
        Cuds: The created cuds object.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.wrapper_session import WrapperSession

    uid = convert_to(uid, "UID")
    if isinstance(session, WrapperSession) and uid in session._expired:
        session._expired.remove(uid)

    # recycle old object
    if uid in session._registry:
        cuds_object = session._registry.get(uid)
        for rel in set(cuds_object._neighbors.keys()):
            if not fix_neighbors:
                del cuds_object._neighbors[rel]
            else:
                cuds_object.remove(rel=rel)
        change_oclass(cuds_object, oclass, kwargs, _force=_force)
    else:  # create new
        if oclass is not None:
            cuds_object = oclass(
                uid=uid, session=session, **kwargs, _force=_force
            )
        else:
            cuds_object = Cuds(uid=uid, session=session, **kwargs)
    return cuds_object


def create_from_cuds_object(cuds_object, session):
    """Create a copy of the given cuds_object in a different session.

    WARNING: Will not recursively copy children.

    Args:
        cuds_object (Cuds): The cuds object to copy
        session (Session): The session of the new Cuds object

    Returns:
        Cuds: A copy of self with the given session.
    """
    assert cuds_object.session is not session
    kwargs = {k.argname: v for k, v in cuds_object.get_attributes().items()}
    clone = create_recycle(
        oclass=cuds_object.oclass,
        kwargs=kwargs,
        session=session,
        uid=cuds_object.uid,
        fix_neighbors=False,
    )
    for rel, target_dict in cuds_object._neighbors.items():
        clone._neighbors[rel] = {}
        for uid, target_oclass in target_dict.items():
            clone._neighbors[rel][uid] = target_oclass
    return clone


def change_oclass(cuds_object, new_oclass, kwargs, _force=False):
    """Change the oclass of a cuds object.

    Only allowed if cuds object does not have any neighbors.

    Args:
        cuds_object (Cuds): The cuds object to change the oclass of
        new_oclass (OntologyClass): The new oclass of the cuds object
        kwargs (Dict[str, Any]): The keyword arguments used to instantiate
            cuds object of the new oclass.

    Returns:
        Cuds: The cuds object with the changed oclass
    """
    cuds_object.session._notify_read(cuds_object)
    # change oclass
    if cuds_object.oclass != new_oclass:
        for neighbor in cuds_object.get(rel=cuba.relationship):
            for rel in get_relationships_between(cuds_object, neighbor):
                neighbor._neighbors[rel.inverse][cuds_object.uid] = [
                    new_oclass
                ]

    # update attributes
    attributes = new_oclass._get_attributes_values(kwargs, _force=_force)
    cuds_object._graph.remove((cuds_object.iri, None, None))
    cuds_object._graph.add((cuds_object.iri, rdflib.RDF.type, new_oclass.iri))
    for k, v in attributes.items():
        cuds_object._graph.set(
            (
                cuds_object.iri,
                k.iri,
                rdflib.Literal(k.convert_to_datatype(v), datatype=k.datatype),
            )
        )
    cuds_object.session._notify_update(cuds_object)


def create_from_triples(
    triples, neighbor_triples, session, fix_neighbors=True
):
    """Create a CUDS object from triples.

    Args:
        triples (List[Tuple]): The list of triples of the CUDS object to
            create.
        neighbor_triples (List[Tuple]): A list of important triples of
            neighbors, most importantly their types.
        session (Session): The session to create the CUDS object in.
        fix_neighbors (bool): Whether to remove the link from the old neighbors
            to this cuds object, defaults to True.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.wrapper_session import WrapperSession
    from osp.core.utils.general import uid_from_iri

    triples = list(triples)
    if not triples:
        return None

    uid = uid_from_iri(triples[0][0])
    if isinstance(session, WrapperSession) and uid in session._expired:
        session._expired.remove(uid)

    # recycle old object
    if uid in session._registry:
        cuds_object = session._registry.get(uid)
        cuds_object.session._notify_read(cuds_object)
        if fix_neighbors:
            rels = set(cuds_object._neighbors.keys())
            for rel in rels:
                cuds_object.remove(rel=rel)
        session.graph.remove((cuds_object.iri, None, None))
        for triple in set(triples):
            session.graph.add(triple)
    else:  # create new
        cuds_object = Cuds(
            attributes={},
            oclass=None,
            session=session,
            uid=uid,
            extra_triples=set(triples),
        )

    # add the triples
    for triple in set(neighbor_triples):
        session.graph.add(triple)
    if isinstance(session, WrapperSession):
        session._store_checks(cuds_object)
    cuds_object.session._notify_update(cuds_object)
    return cuds_object
