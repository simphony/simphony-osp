"""Utilities for searching entities."""

from itertools import chain
from typing import (
    Callable,
    FrozenSet,
    Iterable,
    Iterator,
    Optional,
    Set,
    Union,
)

from rdflib import OWL
from rdflib.term import Node

from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import QueryResult, Session
from simphony_osp.utils.datatypes import UID, AttributeValue


def find(
    root: OntologyIndividual,
    criterion: Callable[[OntologyIndividual], bool] = (lambda x: True),
    rel: Union[
        Union[OntologyRelationship, Node],
        Iterable[Union[OntologyRelationship, Node]],
    ] = OWL.topObjectProperty,
    find_all: bool = True,
    max_depth: Union[int, float] = float("inf"),
) -> Union[Optional[OntologyIndividual], Iterator[OntologyIndividual]]:
    """Finds a set of ontology individuals following the given relationships.

    Use the given relationship for traversal.

    Args:
        criterion: Function that returns True on the ontology individual that
            is searched.
        root: Starting point of the search.
        rel: The relationship(s) (incl. sub-relationships) to consider for
            traversal.
        find_all: Whether to find all ontology individuals satisfying
            the criterion.
        max_depth: The maximum depth for the search. Defaults to
            float("inf") (unlimited).

    Returns:
        The element(s) found. One element (or `None` is returned when
        `find_all` is `False`, a generator when `find_all` is True.
    """
    if isinstance(rel, (OntologyRelationship, Node)):
        rel = {rel}
    rel = frozenset(rel)

    result = _iter(criterion, root, rel, max_depth)
    if not find_all:
        result = next(result, None)

    return result


def _iter(
    criterion: Callable[[OntologyIndividual], bool],
    root: OntologyIndividual,
    rel: FrozenSet[Union[OntologyRelationship, Node]],
    max_depth: Union[int, float] = float("inf"),
    current_depth: int = 0,
    visited: Optional[Set[UID]] = None,
) -> Iterator[OntologyIndividual]:
    """Finds a set of ontology individuals following the given relationships.

    Use the given relationship for traversal.

    Args:
        criterion: Function that returns True on the ontology individual that
            is searched.
        root: Starting point of the search.
        rel: The relationship(s) (incl. sub-relationships) to consider for
            traversal.
        max_depth: The maximum depth for the search. Defaults to
            float("inf") (unlimited).
        current_depth: The current search depth. Defaults to 0.
        visited: The set of UIDs already visited. Defaults to None.

    Returns:
        The element(s) found.
    """
    visited = visited or set()
    visited.add(root.uid)
    if criterion(root):
        yield root

    if current_depth < max_depth:
        for sub in chain(*(root.iter(rel=r) for r in rel)):
            if sub.uid not in visited:
                yield from _iter(
                    criterion=criterion,
                    root=sub,
                    rel=rel,
                    max_depth=max_depth,
                    current_depth=current_depth + 1,
                    visited=visited,
                )


def find_by_identifier(
    root: OntologyIndividual,
    identifier: Union[Node, UID, str],
    rel: Union[
        Union[OntologyRelationship, Node],
        Iterable[Union[OntologyRelationship, Node]],
    ] = OWL.topObjectProperty,
) -> Optional[OntologyIndividual]:
    """Recursively finds an ontology individual with given identifier.

    Only uses the given relationship for traversal.

    Args:
        root: Starting point of search.
        identifier: The identifier of the entity that is searched.
        rel: The relationship (incl. sub-relationships) to consider.

    Returns:
        The resulting individual.
    """
    return find(
        root=root,
        criterion=lambda individual: individual.uid == UID(identifier),
        rel=rel,
        find_all=False,
    )


def find_by_class(
    root: OntologyIndividual,
    oclass: OntologyClass,
    rel: Union[
        Union[OntologyRelationship, Node],
        Iterable[Union[OntologyRelationship, Node]],
    ] = OWL.topObjectProperty,
) -> Iterator[OntologyIndividual]:
    """Recursively finds ontology individuals with given class.

    Only uses the given relationship for traversal.

    Args:
        root: Starting point of search.
        oclass: The ontology class of the entity that is searched.
        rel: The relationship (incl. sub-relationships) to consider for
            traversal.

    Returns:
        The individuals found.
    """
    return find(
        criterion=lambda individual: individual.is_a(oclass),
        root=root,
        rel=rel,
        find_all=True,
    )


def find_by_attribute(
    root: OntologyIndividual,
    attribute: OntologyAttribute,
    value: AttributeValue,
    rel: Union[
        Union[OntologyRelationship, Node],
        Iterable[Union[OntologyRelationship, Node]],
    ] = OWL.topObjectProperty,
) -> Iterator[OntologyIndividual]:
    """Recursively finds ontology individuals by attribute and value.

    Only the given relationship will be used for traversal.

    Args:
        root: The root for the search.
        attribute: The attribute to look for.
        value: The corresponding value to filter by.
        rel: The relationship (incl. sub-relationships) to consider.

    Returns:
        The individuals found.
    """
    return find(
        criterion=(lambda individual: value in individual[attribute]),
        root=root,
        rel=rel,
        find_all=True,
    )


def find_relationships(
    root: OntologyIndividual,
    find_rel: OntologyRelationship,
    find_sub_relationships: bool = False,
    rel: Union[
        Union[OntologyRelationship, Node],
        Iterable[Union[OntologyRelationship, Node]],
    ] = OWL.topObjectProperty,
) -> Iterator[OntologyIndividual]:
    """Find the given relationship in the subtree of the given root.

    Args:
        root: Only consider the subgraph rooted in this root.
        find_rel: The relationship to find.
        find_sub_relationships: Treat relationships that are a
            sub-relationship of the relationship to find as valid results.
            Defaults to `False`.
        rel: Only consider these relationships (incl. sub-relationships) when
            searching.


    Returns:
        The ontology individuals having the given relationship.
    """
    subclasses = find_rel.subclasses if find_sub_relationships else {find_rel}

    def criterion(individual):
        return any(
            relationship in subclasses
            for _, relationship in individual.relationships_iter(
                return_rel=True
            )
        )

    return find(criterion=criterion, root=root, rel=rel, find_all=True)


def sparql(query: str, session: Optional[Session] = None) -> QueryResult:
    """Performs a SPARQL query on a session.

    Args:
        query: A string with the SPARQL query to perform.
        session: The session on which the SPARQL query will be performed. If no
            session is specified, then the current default session is used.
            This means that, when no session is specified, inside session
            `with` statements, the query will be performed on the session
            associated with such statement, while outside, it will be
            performed on the SimPhoNy default session.

    Returns:
        A QueryResult object, which can be iterated to obtain
        the output rows. Then for each `row`, the value for each query
        variable can be retrieved as follows: `row['variable']`.
    """
    session = session or Session.get_default_session()
    return session.sparql(query)
