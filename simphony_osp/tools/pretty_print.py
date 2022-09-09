"""Utility functions for printing ontology entities objects in a nice way."""

import sys
from functools import reduce
from operator import add
from typing import Iterable, Optional, Set, Union

from simphony_osp.namespaces import owl
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.composition import Composition
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.ontology.restriction import Restriction


def pretty_print(
    entity: OntologyEntity,
    rel: Union[
        OntologyRelationship, Iterable[OntologyRelationship]
    ] = owl.topObjectProperty,
    file=sys.stdout,
):
    """Print a tree-like, text representation stemming from an individual.

    Generates a tree-like, text-based representation stemming from a given
    ontology individual, that includes the IRI, ontology classes and attributes
    of the involved individuals, as well as the relationships connecting them.

    Args:
        entity: Ontology individual to be used as starting point of the
            text-based representation.
        file: A file to print the text to. Defaults to the standard output.
        rel: Restrict the relationships to consider when searching for
            attached individuals to subclasses of the given relationships.
    """
    # Fix the order of each element by pre-populating a dictionary.
    pp = {
        x: ""
        for x in (
            "title",
            "identifier",
            "classes",
            "superclasses",
            "attributes",
            "subelements",
        )
    }

    # Title
    pp["title"] = f"{_pp_entity_name(entity)}:"

    # Superclasses
    superclasses = (
        {
            superclass
            for class_ in entity.classes
            for superclass in class_.superclasses
        }
        if isinstance(entity, OntologyIndividual)
        else set(entity.superclasses)
    )
    labels = _pp_list_of_labels_or_uids(superclasses, namespace=True)
    pp["superclasses"] = "\n  superclasses: " + labels

    if isinstance(entity, OntologyIndividual):
        # Classes
        classes = set(entity.classes)
        labels = _pp_list_of_labels_or_uids(classes, namespace=True)
        pp["classes"] = f"\n  type{'s' if len(classes) > 1 else ''}: {labels}"
        # Attribute values
        values_str = _pp_individual_values(entity)
        if values_str:
            pp["attributes"] = f"\n  values: {values_str}"
        # Subelements
        pp["subelements"] = _pp_individual_subelements(entity, rel)

    pp["identifier"] = f"\n  identifier: {entity.uid}"

    pp = reduce(add, pp.values())
    print(pp, file=file)


def _pp_entity_name(entity: OntologyEntity, type_: bool = False):
    """Return the name of the given element following the pretty print format.

    Args:
        entity: element to be printed.

    Returns:
        String with the pretty printed text.
    """
    type_names = {
        OntologyIndividual: "Ontology individual",
        OntologyClass: "Ontology class",
        OntologyRelationship: "Ontology relationship",
        OntologyAttribute: "Ontology attribute",
        Composition: "Composition",
        Restriction: "Restriction",
    }
    type_name = next(
        (
            name
            for type_, name in type_names.items()
            if isinstance(entity, type_)
        ),
        "Ontology entity",
    )

    title = "- %s" % type_name

    if type_ is True and isinstance(entity, OntologyIndividual):
        classes = entity.classes
        title += (
            f" of class{'es' if len(classes) > 1 else ''} "
            f"{','.join(str(x) for x in classes)}"
        )

    label = entity.label
    if label is not None:
        title += f" named {label}"
    # else:
    #     title += f" {entity.uid}"

    return title


def _pp_individual_subelements(
    individual: OntologyIndividual,
    rel: Union[
        OntologyRelationship, Iterable[OntologyRelationship]
    ] = owl.topObjectProperty,
    level_indentation: str = "\n  ",
    visited: Optional[Set] = None,
) -> str:
    """Recursively formats the subelements from an individual.

    The objects are grouped by ontology class.

    Args:
        individual: element to inspect.
        level_indentation: common characters to left-pad the text.

    Returns:
        String with the pretty printed text
    """
    pp_sub = ""

    # Find relationships connecting the individual to its subelements.
    consider_relationships = set()
    if isinstance(rel, OntologyRelationship):
        rels = {rel}
    else:
        rels = rel
    for predicate in individual.session.graph.predicates(
        individual.identifier, None
    ):
        try:
            relationship = individual.session.ontology.from_identifier(
                predicate
            )
            if isinstance(relationship, OntologyRelationship):
                consider_relationships |= {relationship}
        except KeyError:
            pass
    filtered_relationships = filter(
        lambda x: any(x.is_subclass_of(r) for r in rels),
        consider_relationships,
    )
    sorted_relationships = sorted(filtered_relationships, key=str)

    visited = visited or set()
    visited.add(individual.uid)
    for i, relationship in enumerate(sorted_relationships):
        relationship_name = _pp_list_of_labels_or_uids({relationship})
        pp_sub += level_indentation + (
            " |_Relationship %s (%s):"
            % (relationship_name, relationship.namespace.name)
        )
        sorted_elements = sorted(
            individual.iter(rel=relationship, return_rel=True),
            key=lambda x: (
                "\0"
                + str(
                    sorted(
                        class_.label
                        if class_.label is not None
                        else class_.identifier
                        for class_ in x[0].classes
                    )[0]
                ),
                f"\0{x[1].label}"
                if x[1].label is not None
                else f"{x[1].identifier}",
                f"\0{x[0].label}" if x[0].label is not None else f"{x[0].uid}",
            ),
        )
        for j, (element, rel) in enumerate(sorted_elements):
            if rel != relationship:
                continue
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + _pp_entity_name(element, type_=True)
            if j == len(sorted_elements) - 1:
                indentation += "   "
            else:
                indentation += " . "

            identifier_str = f"identifier: {element.uid}"
            pp_sub += indentation + identifier_str

            if element.uid in visited:
                pp_sub += indentation + "(already printed)"
                continue

            values_str = _pp_individual_values(element, indentation)
            if values_str:
                pp_sub += indentation + values_str

            pp_sub += _pp_individual_subelements(
                element, rels, indentation, visited
            )
    return pp_sub


def _pp_individual_values(cuds_object, indentation="\n          "):
    r"""Print the attributes of a cuds object.

    Args:
        cuds_object (Cuds): Print the values of this cuds object.
        indentation (str): The indentation to prepend, defaults to
            "\n          "

    Returns:
        str: The resulting string to print.
    """
    result = []
    sorted_attributes = sorted(
        cuds_object.attributes.items(),
        key=lambda x: (
            f"\0{x[0].label}"
            if x[0].label is not None
            else f"{x[0].identifier}",
            str(x[1]),
        ),
    )
    for attribute, value in sorted_attributes:
        result.append(
            "%s: %s"
            % (
                f"\0{attribute.label}"
                if attribute.label is not None
                else f"{attribute.identifier}",
                value if not len(value) == 1 else next(iter(value)),
            )
        )
    if result:
        return indentation.join(result)


def _pp_list_of_labels_or_uids(
    entities: Iterable[OntologyEntity], namespace: bool = False
) -> str:
    entities = set(entities)
    if namespace:
        labels = (
            f"{entity.label} ({entity.namespace.name})" for entity in entities
        )
    else:
        labels = (entity.label for entity in entities)
    labels = (
        label if label is not None else str(entity.uid)
        for label, entity in zip(labels, entities)
    )
    labels = ", ".join(labels)
    return labels
