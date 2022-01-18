"""Utility functions for printing ontology entities objects in a nice way."""

import sys
from functools import reduce
from operator import add
from typing import Iterable, Optional, Set

from osp.core.namespaces import cuba
from osp.core.ontology.attribute import OntologyAttribute
from osp.core.ontology.oclass import OntologyClass
from osp.core.ontology.oclass_composition import Composition
from osp.core.ontology.oclass_restriction import Restriction
from osp.core.ontology.entity import OntologyEntity
from osp.core.ontology.individual import OntologyIndividual
from osp.core.ontology.relationship import OntologyRelationship


def pretty_print(entity: OntologyEntity,
                 file=sys.stdout):
    """Print the given ontology entity in a human-readable way.

    The UID, the type, the ancestors and the content are printed.

    Args:
        entity (Cuds): container to be printed.
        file (TextIOWrapper): The file to print to.
    """
    # Fix the order of each element by pre-populating a dictionary.
    pp = {x: '' for x in (
        'title',
        'classes',
        'superclasses',
        'attributes',
        'subelements',
    )}

    # Title
    pp['title'] = _pp_entity_name(entity)

    # Superclasses
    superclasses = set(superclass for class_ in entity.oclasses
                       for superclass in class_.superclasses) \
        if isinstance(entity, OntologyIndividual) else set(entity.superclasses)
    labels = _pp_list_of_labels_or_uids(superclasses)
    pp['superclasses'] = "\n  superclasses: " + labels

    if isinstance(entity, OntologyIndividual):
        # Classes
        classes = set(entity.oclasses)
        labels = _pp_list_of_labels_or_uids(classes)
        pp['classes'] = f"\n  type{'s' if len(classes) > 1 else ''}: {labels}"
        # Attribute values
        values_str = _pp_individual_values(entity)
        if values_str:
            pp['attributes'] = f"\n  values: {values_str}"
        # Subelements
        pp['subelements'] = _pp_individual_subelements(entity)

    pp = reduce(add, pp.values())
    print(pp, file=file)


def _pp_entity_name(entity: OntologyEntity):
    """Return the name of the given element following the pretty print format.

    Args:
        entity (Cuds): element to be printed.

    Returns:
        String with the pretty printed text.
    """
    type_names = {OntologyIndividual: 'Ontology individual',
                  OntologyClass: 'Ontology class',
                  OntologyRelationship: 'Ontology relationship',
                  OntologyAttribute: 'Ontology attribute',
                  Composition: 'Composition',
                  Restriction: 'Restriction'}
    type_name = next(
        (name for type_, name in type_names.items() if isinstance(entity,
                                                                  type_)),
        'Ontology entity')

    title = "- %s" % type_name

    label = entity.label
    if label is not None:
        title += f' named {label}'
    else:
        title += f' {entity.uid}'

    return title


def _pp_individual_subelements(individual: OntologyIndividual,
                               level_indentation: str = "\n  ",
                               visited: Optional[Set] = None) -> str:
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
    for predicate in individual.session.graph.predicates(
            individual.identifier, None):
        try:
            relationship = individual.session.ontology.from_identifier(
                predicate)
            if isinstance(relationship, OntologyRelationship):
                consider_relationships |= {relationship}
        except KeyError:
            pass
    filtered_relationships = filter(
        lambda x: x.is_subclass_of(cuba.activeRelationship),
        consider_relationships)
    sorted_relationships = sorted(filtered_relationships, key=str)

    visited = visited or set()
    visited.add(individual.uid)
    for i, relationship in enumerate(sorted_relationships):
        relationship_name = _pp_list_of_labels_or_uids({relationship})
        pp_sub += level_indentation \
            + " |_Relationship %s:" % relationship_name
        sorted_elements = sorted(
            individual.iter(rel=relationship, return_rel=True),
            key=lambda x: (f'\0{x[0].oclass.label}'
                           if x[0].oclass.label is not None else
                           f'{x[0].oclass.identifier}',
                           f'\0{x[1].label}'
                           if x[1].label is not None else
                           f'{x[1].identifier}',
                           f'\0{x[0].label}' if x[0].label is not None else
                           f'{x[0].uid}')
        )
        for j, (element, rel) in enumerate(sorted_elements):
            if rel != relationship:
                continue
            if i == len(sorted_relationships) - 1:
                indentation = level_indentation + "   "
            else:
                indentation = level_indentation + " | "
            pp_sub += indentation + _pp_entity_name(element)
            if j == len(sorted_elements) - 1:
                indentation += "   "
            else:
                indentation += ".  "

            if element.uid in visited:
                pp_sub += indentation + "(already printed)"
                continue

            values_str = _pp_individual_values(element, indentation)
            if values_str:
                pp_sub += indentation + values_str

            pp_sub += _pp_individual_subelements(element, indentation, visited)
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
    sorted_attributes = sorted(cuds_object.get_attributes().items(),
                               key=lambda x: (
                                   f'\0{x[0].label}'
                                   if x[0].label is not None else
                                   f'{x[0].identifier}',
                                   str(x[1]))
                               )
    for attribute, value in sorted_attributes:
        result.append("%s: %s" % (f'\0{attribute.label}'
                                  if attribute.label is not None else
                                  f'{attribute.identifier}',
                                  value if not len(value) == 1 else
                                  next(iter(value))))
    if result:
        return indentation.join(result)


def _pp_list_of_labels_or_uids(entities: Iterable[OntologyEntity]) -> str:
    entities = set(entities)
    labels = (entity.label for entity in entities)
    labels = (label if label is not None else str(entity.uid)
              for label, entity
              in zip(labels, entities))
    labels = ', '.join(labels)
    return labels
