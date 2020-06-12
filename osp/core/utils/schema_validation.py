import yaml
import logging

from osp.core import get_entity

logger = logging.getLogger(__name__)


def validate_tree_against_schema(root_obj, schema_file):
    """Checks whether the CUDS tree that starts at root_obj
    fulfills the cardinality constraints defined in the schema file.

    :param root_obj: The root CUDS object of the tree
    :type root_obj: CUDS
    :param schema_file: The path to the schema file that \
    defines the constraints
    :type schema_file: str
    :raises Exception: Tells the user which constraint was violated
    """

    logger.info("""Validating tree of root object {}
    against schema file {} ...""".format(root_obj.uid, schema_file))

    data_model_dict = _load_data_model_from_yaml(schema_file)
    oclass_groups = _traverse_tree_and_group_all_objects_by_oclass(root_obj)

    for entity, relationships in data_model_dict['model'].items():
        # get all objects that are an instance of the entity we want to check
        try:
            entity_instances_to_check = oclass_groups[entity]
        except KeyError:
            raise Exception(f"Instance of entity {entity} is expected to be \
                            present in the CUDS tree, but none was found.")

        for cuds_obj in entity_instances_to_check:
            for relationship, connected_entities in relationships.items():
                for connected_entity, constraints in connected_entities.items(
                ):
                    _check_cuds_object_cardinality(
                        cuds_obj,
                        connected_entity,
                        relationship,
                        constraints
                    )
    logger.info('Tree is valid.')


def _load_data_model_from_yaml(data_model_file):
    with open(data_model_file) as f:
        data_model_dict = yaml.safe_load(f)
    return data_model_dict


def _check_cuds_object_cardinality(
    origin_cuds,
    dest_oclass,
    rel,
    constraints
):

    actual_cardinality = len(origin_cuds.get(
        rel=get_entity(rel),
        oclass=get_entity(dest_oclass)
    ))

    min, max = _interpret_cardinality_value_from_constraints(constraints)
    if actual_cardinality < min or actual_cardinality > max:
        message = """Found invalid cardinality between {} and {} with relationship {}.
        The constraint says it should be between {} and {}, but we found {}.
        The uid of the affected cuds_object is: {}""".format(
            str(origin_cuds.oclass),
            dest_oclass,
            rel,
            min,
            max,
            actual_cardinality,
            origin_cuds.uid)
        raise Exception(message)


def _interpret_cardinality_value_from_constraints(constraints):
    # default is arbitrary
    min = 0
    max = float('inf')
    if constraints is not None:
        cardinality_value = constraints.get('cardinality')
        if isinstance(cardinality_value, int):
            min = cardinality_value
            max = cardinality_value
        elif '-' in cardinality_value:
            min = int(cardinality_value.split('-')[0])
            max = int(cardinality_value.split('-')[1])
        elif '+' in cardinality_value:
            min = int(cardinality_value.split('+')[0])
    return min, max


def _traverse_tree_and_group_all_objects_by_oclass(root_obj, result=None):
    """Traverses the tree once and groups all objects by oclass

    :param root_obj: The root object where to start the traversion
    :type root_obj: CUDS
    :param result: The current results of the recursion, defaults to None
    :type result: dict, optional
    :return: All CUDS objects in the tree, grouped by oclass.
    :rtype: dict
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
