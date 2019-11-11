# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import requests
import json
from osp.core import CUBA
from osp.core.utils import find_cuds_object


def post(url, cuds_object, max_depth=float("inf")):
    from osp.core.session.transport.transport_util import serializable
    cuds_objects = find_cuds_object(criterion=lambda x: True,
                                    root=cuds_object,
                                    rel=CUBA.ACTIVE_RELATIONSHIP,
                                    find_all=True,
                                    max_depth=max_depth)
    serialized = json.dumps(serializable(cuds_objects))
    return requests.post(url=url,
                         data=serialized,
                         headers={"content_type": "application/json"})


def remove_cuds_object(cuds_object):
    """
    Remove a cuds_object from the datastructure.
    Removes the relationships to all neighbours.
    To delete it from the registry you must call the
    sessions prune method afterwards.

    :param cuds_object: The cuds_object to remove.
    """
    # Method does not allow deletion of the root element of a container
    for elem in cuds_object.iter(rel=CUBA.RELATIONSHIP):
        cuds_object.remove(elem.uid, rel=CUBA.RELATIONSHIP)


def get_relationships_between(subj, obj):
    """Get the set of relationships between two cuds objects.

    :param subj: The subject
    :type subj: Cuds
    :param obj: The object
    :type obj: Cuds
    :return: The set of relationships between subject and object.
    :rtype: Set[Type[Relationship]]
    """
    result = set()
    for rel, obj_uids in subj._neighbours.items():
        if obj.uid in obj_uids:
            result.add(rel)
    return result
