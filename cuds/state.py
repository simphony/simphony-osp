# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import cuds.classes


def add_state(states_container, new_version):
    """
    Creates a new state and add the elements contained

    :param states_container: entity with all the states
    :param new_version: new state to add
    """
    current_states = states_container.get(cuds.classes.CUBA.STATE)
    if not current_states:
        message = 'The given object {} has no proper state structure'
        raise AttributeError(message.format(states_container.uid))

    # Create a new state with the increased counter
    new_state = cuds.classes.State(len(current_states))
    add_subelements(new_state, new_version)
    states_container.add(new_state)


def add_subelements(cuds_object, element):
    """
    Adds to a given cuds_object the subelements contained in another.

    :param cuds_object: where to add the elements
    :param element: container with subelements to add
    """
    for subelement in element.iter():
        cuds_object.add(subelement)
