"""A collection of utility methods for SimPhoNy.

These are potentially useful for every user of SimPhoNy.
"""

import logging
from typing import TYPE_CHECKING

from simphony_osp.utils import simphony_namespace

if TYPE_CHECKING:
    from simphony_osp.ontology.relationship import OntologyRelationship

CUDS_IRI_PREFIX = "https://www.simphony-project.eu/cuds#"
logger = logging.getLogger(__name__)

__all__ = [
    "branch",
    "delete_cuds_object_recursively",
    "get_relationships_between",
]


def branch(cuds_object, *args, rel=None):
    """Like Cuds.add(), but returns the element you add to.

    This makes it easier to create large CUDS structures.

    Args:
        cuds_object (Cuds): the object to add to.
        args (Cuds): object(s) to add
        rel (OntologyRelationship): class of the relationship between the
            objects.

    Raises:
        ValueError: adding an element already there.

    Returns:
        Cuds: The first argument.
    """
    cuds_object.connect(*args, rel=rel)
    return cuds_object


def get_relationships_between(subj, obj):
    """Get the set of relationships between two cuds objects.

    Args:
        subj (Cuds): The subject
        obj (Cuds): The object

    Returns:
        Set[OntologyRelationship]: The set of relationships between subject
            and object.
    """
    result = set()
    for rel, obj_uids in subj._neighbors.items():
        if obj.uid in obj_uids:
            result.add(rel)
    return result


def delete_cuds_object_recursively(
    cuds_object,
    rel=simphony_namespace.activeRelationship,
    max_depth=float("inf"),
):
    """Delete a cuds object and all the objects inside the container of it.

    Args:
        cuds_object (Cuds): The CUDS object to recursively delete.
        rel (OntologyRelationship, optional): The relationship used for
            traversal. Defaults to cuba.activeRelationship.
        max_depth (int, optional):The maximum depth of the recursion.
            Defaults to float("inf"). Defaults to float("inf").
    """
    from simphony_osp.tools.search import find_cuds_object

    cuds_objects = find_cuds_object(
        criterion=lambda x: True,
        root=cuds_object,
        rel=rel,
        find_all=True,
        max_depth=max_depth,
    )
    for obj in cuds_objects:
        obj.ontology.delete_cuds_object(obj)
