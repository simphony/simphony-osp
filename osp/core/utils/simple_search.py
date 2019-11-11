# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


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


def find_cuds_objects_by_oclass(oclass, root, rel):
    """
    Recursively finds an element with given oclass inside a cuds object
    by considering the given relationship.

    :param oclass: The oclass of the cuds_object that is searched.
    :type uid: OntologyClass
    :param root: Starting point of search
    :type root: Cuds
    :param rel: The relationship (incl. subrelationships) to consider
    :type rel: Type[Relationship]
    :return: The found suds objects.
    :rtype: List[Cuds]
    """
    return find_cuds_object(
        criterion=lambda cuds_object: cuds_object.is_a == oclass,
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
            for rel in cuds_object._neighbours.keys():
                if find_rel in rel.superclasses:
                    return True
            return False
    else:
        def criterion(cuds_object):
            return find_rel in cuds_object._neighbours

    return find_cuds_object(
        criterion=criterion,
        root=root,
        rel=consider_rel,
        find_all=True
    )
