"""A collection of utility methods for SimPhoNy.

These are potentially useful for every user of SimPhoNy.
"""

import logging
from typing import Set

from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.relationship import OntologyRelationship

logger = logging.getLogger(__name__)

__all__ = [
    "branch",
    "relationships_between",
]


def branch(
    individual, *individuals, rel: OntologyRelationship
) -> OntologyIndividual:
    """Like `connect`, but returns the element you connect to.

    This makes it easier to create large structures involving ontology
    individuals.

    Args:
        individual: The ontology individual that is the subject of the
            connections to be created.
        individuals: Ontology individuals to connect to.
        rel: Relationship to use.

    Returns:
        The ontology individual that is the subject of the connections to be
        created (the first argument).
    """
    individual.connect(*individuals, rel=rel)
    return individual


def relationships_between(
    subj: OntologyIndividual, obj: OntologyIndividual
) -> Set[OntologyRelationship]:
    """Get the set of relationships between two ontology individuals.

    Args:
        subj: The subject of the relationship.
        obj: The object (target) of the relationship.

    Returns:
        The set of relationships between the given subject and object
        individuals.
    """
    return {
        relationship
        for individual, relationship in subj.get(obj, return_rel=True)
    }
