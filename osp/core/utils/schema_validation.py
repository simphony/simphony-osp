"""Contains methods that check if CUDS objects satisfy a certain schema."""

import logging

import yaml

from osp.core.namespaces import get_entity
from osp.core.ontology import OntologyAttribute, OntologyRelationship
from osp.core.ontology.datatypes import YML_DATATYPES

logger = logging.getLogger(__name__)


class ConsistencyError(Exception):
    """The given CUDS structure is inconsistent."""


class CardinalityError(Exception):
    """A cardinality constraint is violated."""


def validate_tree_against_schema(root_obj, schema_file, strict_check=False):
    """Test cardinality constraints on given CUDS tree.

    The tree that starts at root_obj.
    The constraints are defined in the schema file.

    Args:
        root_obj (Cuds): The root CUDS object of the tree
        schema_file (str): The path to the schema file that
            defines the constraints
        strict_check (bool): whether extra cuds not listed in
            the schema_file should be tolerated or not

    Raise:
        Exception: Tells the user which constraint was violated
    """
    logger.info(
        """Validating tree of root object {}
    against schema file {} ...""".format(
            root_obj.uid, schema_file
        )
    )

    data_model_dict = _load_data_model_from_yaml(schema_file)
    (
        optional_subtrees,
        mandatory_subtrees,
    ) = _get_optional_and_mandatory_subtrees(data_model_dict)
    oclass_groups = _traverse_tree_and_group_all_objects_by_oclass(root_obj)

    # first check that the model oclasses that do
    # not specify relationships (their only constraint is to exist)
    # or that are mandatory are all in the tree
    for model_oclass, relationships in data_model_dict["model"].items():
        if (
            not relationships
            or model_oclass in mandatory_subtrees
            or model_oclass not in optional_subtrees
        ):
            try:
                oclass_groups[model_oclass]
            except KeyError:
                raise ConsistencyError(
                    f"Instance of entity {model_oclass} is expected to be \
                    present in the CUDS tree, but none was found."
                )

    for oclass, all_objects_to_check in oclass_groups.items():
        # get the definition for this oclass from the model
        try:
            relationships = data_model_dict["model"][oclass]
        except KeyError:
            if strict_check:
                message = f"An entity for {oclass} was found,"
                " but it is not part of the provided schema"
                raise ConsistencyError(message)
            else:
                continue
        if relationships is None:
            # if there are no relationships defined,
            # the only constraint is that the object exists
            continue

        # now go through all objects of this oclass in the tree
        # and check whether the definition is fulfilled
        for object_to_check in all_objects_to_check:
            for relationship, neighbor_entities in relationships.items():
                for neighbor_oclass, constraints in neighbor_entities.items():
                    _check_cuds_object_cardinality(
                        object_to_check,
                        neighbor_oclass,
                        relationship,
                        constraints,
                    )
    logger.info("Tree is valid.")


def _load_data_model_from_yaml(data_model_file):
    with open(data_model_file) as f:
        data_model_dict = yaml.safe_load(f)
    return data_model_dict


def _check_cuds_object_cardinality(origin_cuds, dest_oclass, rel, constraints):
    rel_entity = get_entity(rel)

    if type(rel_entity) == OntologyRelationship:
        actual_cardinality = len(
            origin_cuds.get(rel=rel_entity, oclass=get_entity(dest_oclass))
        )
    elif type(rel_entity) == OntologyAttribute:
        # No datatype checking since this is already done when Cuds are
        # instantiated or imported from a file
        actual_cardinality = (
            1 if rel_entity in origin_cuds.get_attributes() else 0
        )
    else:
        raise ConsistencyError(
            f"Relation '{rel}' not supported for {origin_cuds.oclass}."
        )

    min, max = _interpret_cardinality_value_from_constraints(constraints)
    if actual_cardinality < min or actual_cardinality > max:
        message = """Found invalid cardinality between {} and {}
        with relationship {}. The constraint says it should be
        between {} and {}, but we found {}.
        The uid of the affected cuds_object is: {}""".format(
            str(origin_cuds.oclass),
            dest_oclass,
            rel,
            min,
            max,
            actual_cardinality,
            origin_cuds.uid,
        )
        raise CardinalityError(message)

    _check_attribute_contraints(
        origin_cuds, rel_entity, dest_oclass, constraints
    )


def _check_attribute_contraints(
    origin_cuds, rel_entity, dest_oclass, constraints
):
    attribute = origin_cuds.get_attributes().get(rel_entity)
    value = constraints.get("value")
    if attribute:
        if value and attribute != value:
            message = """Found invalid attribute value
            between {} and {} with relationship {}.
            The constraint says it should be valued '{}',
            but we found '{}'. The uid of the affected
            cuds_object is: {}""".format(
                str(origin_cuds.oclass),
                dest_oclass,
                rel_entity,
                value,
                attribute,
                origin_cuds.uid,
            )
            raise ConsistencyError(message)

        if type(attribute) == str:
            attribute = len(attribute)
            target = "length"
        else:
            target = "range"
        min, max = _interpret_attribute_from_constraints(constraints, target)
        if attribute < min or attribute > max:
            message = """Found invalid attribute value {} between {} and {}
            relationship {}. The constraint says it should be between {}
            and {}, but we found {}. The uid of the affected
            cuds_object is: {}""".format(
                target,
                str(origin_cuds.oclass),
                dest_oclass,
                rel_entity,
                min,
                max,
                attribute,
                origin_cuds.uid,
            )
            raise CardinalityError(message)


def _interpret_attribute_from_constraints(constraints, range_or_len: str):
    min = -float("inf")
    if constraints is not None:
        value = constraints.get(range_or_len)
        min, max = _interpret_cardinality_value_from_constraints(
            dict(cardinality=value)
        )
    return min, max


def _interpret_cardinality_value_from_constraints(constraints):
    # default is arbitrary
    min = 0
    max = float("inf")
    if constraints is not None:
        cardinality_value = constraints.get("cardinality")
        if isinstance(cardinality_value, int):
            min = cardinality_value
            max = cardinality_value
        elif isinstance(cardinality_value, str):
            if "-" in cardinality_value:
                min = int(cardinality_value.split("-")[0])
                max = int(cardinality_value.split("-")[1])
            elif "+" in cardinality_value:
                min = int(cardinality_value.split("+")[0])
    return min, max


def _traverse_tree_and_group_all_objects_by_oclass(root_obj, result=None):
    """Traverses the tree once and groups all objects by oclass.

    Args:
        root_obj (Cuds): The root object where to start the traversal.
        result (dict): The current results of the recursion, defaults to None

    Returns:
        dict: All CUDS objects in the tree, grouped by oclass.
    """
    if result is None:
        result = {str(root_obj.oclass): [root_obj]}
    for neighbour in root_obj.iter():
        if neighbour.oclass not in result.keys():
            result[str(neighbour.oclass)] = [neighbour]
        else:
            result[str(neighbour.oclass)].append(neighbour)
        _traverse_tree_and_group_all_objects_by_oclass(neighbour, result)
    return result


def _get_optional_and_mandatory_subtrees(data_model_dict):
    optional_subtrees = set()
    mandatory_subtrees = set()
    entities = data_model_dict["model"]
    for entity, relationships in entities.items():
        if not relationships:
            continue
        for relationship, neighbors in relationships.items():
            for neighbor, constraints in neighbors.items():
                min, max = _interpret_cardinality_value_from_constraints(
                    constraints
                )
                if min == 0 and neighbor not in YML_DATATYPES.keys():
                    optional_subtrees.add(neighbor)
                if min > 0 and neighbor not in YML_DATATYPES.keys():
                    mandatory_subtrees.add(neighbor)

    if optional_subtrees & mandatory_subtrees:
        raise ConsistencyError(
            """You specified the following entities to be
            mandatory and optional at
            the same time: {}. Please check your model file.""".format(
                mandatory_subtrees & optional_subtrees
            )
        )
    return optional_subtrees, mandatory_subtrees
