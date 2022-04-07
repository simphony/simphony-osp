"""This file contains utility method used for searching in CUDS objects."""


def find_cuds_object(
    criterion,
    root,
    rel,
    find_all,
    max_depth=float("inf"),
    current_depth=0,
    visited=None,
):
    """Recursively finds an element inside a container.

    Use the given relationship for traversal.

    Args:
        criterion (Callable): Function that returns True on the Cuds object
            that is searched.
        root (Cuds): Starting point of search
        rel (OntologyRelationship): The relationship (incl. subrelationships)
            to consider for traversal.
        find_all (bool): Whether to find all cuds_objects satisfying
            the criterion.
        max_depth (int, optional): The maximum depth for the search.
            Defaults to float("inf").
        current_depth (int, optional): The current search depth. Defaults to 0.
        visited (Set[Union[UUID, URIRef]], optional): The set of uids
            already visited. Defaults to None.

    Returns:
        Union[Cuds, List[Cuds]]: The element(s) found.
    """
    visited = visited or set()
    visited.add(root.uid)
    output = [root] if criterion(root) else []

    if output and not find_all:
        return output[0]

    if current_depth < max_depth:
        for sub in root.iter(rel=rel):
            if sub.uid not in visited:
                result = find_cuds_object(
                    criterion=criterion,
                    root=sub,
                    rel=rel,
                    find_all=find_all,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    visited=visited,
                )
                if not find_all and result is not None:
                    return result
                if result is not None:
                    output += result
    return output if find_all else None


def find_cuds_object_by_uid(uid, root, rel):
    """Recursively finds an element with given uid inside a cuds object.

    Only use the given relationship for traversal.

    Args:
        uid (Union[UUID, URIRef]): The uid of the cuds_object
            that is searched.
        root (Cuds): Starting point of search.
        rel (OntologyRelationship): The relationship (incl. subrelationships)
            to consider.

    Returns:
        Cuds: The element found.
    """
    return find_cuds_object(
        criterion=lambda cuds_object: cuds_object.uid == uid,
        root=root,
        rel=rel,
        find_all=False,
    )


def find_cuds_objects_by_oclass(oclass, root, rel):
    """Recursively finds an element with given oclass inside a cuds object.

    Only use the given relationship for traversal.

    Args:
        oclass (OntologyClass): The oclass of the cuds_object that is searched.
        root (Cuds): Starting point of search.
        rel (OntologyRelationship): The relationship (incl. subrelationships)
            to consider for traversal.

    Returns:
        List[Cuds]: The elements found.
    """
    return find_cuds_object(
        criterion=lambda cuds_object: cuds_object.is_a(oclass),
        root=root,
        rel=rel,
        find_all=True,
    )


def find_cuds_objects_by_attribute(attribute, value, root, rel):
    """Recursively finds a cuds object by attribute and value.

    Only the given relationship will be used for traversal.


    Args:
        attribute (str): The attribute to look for
        value (Any): The corresponding value to filter by
        root (Cuds): The root for the search.
        rel (OntologyRelationship): The relationship (+ subrelationships) to
            consider.

    Returns:
        List[Cuds]: The found cuds objects.
    """
    return find_cuds_object(
        criterion=(
            lambda cuds_object: hasattr(cuds_object, attribute)
            and getattr(cuds_object, attribute) == value
        ),
        root=root,
        rel=rel,
        find_all=True,
    )


def find_relationships(find_rel, root, consider_rel, find_sub_rels=False):
    """Find the given relationship in the subtree of the given root.

    Args:
        find_rel (OntologyRelationship): The relationship to find.
        root (Cuds): Only consider the subgraph rooted in this root.
        consider_rel (OntologyRelationship): Only consider these relationships
            when searching.
        find_sub_rels (bool, optional): The cuds objects having the given
            relationship.. Defaults to False.

    Returns:
        List[Cuds]: The cuds objects having the given relationship.
    """
    if find_sub_rels:

        def criterion(cuds_object):
            for rel in cuds_object._neighbors.keys():
                if find_rel.is_superclass_of(rel):
                    return True
            return False

    else:

        def criterion(cuds_object):
            return find_rel in cuds_object._neighbors

    return find_cuds_object(
        criterion=criterion, root=root, rel=consider_rel, find_all=True
    )
