# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
import numpy as np


def convert_to(x, datatype_string):
    datatype_args = datatype_string.split(":")[1:]
    try:
        datatype = ONTOLOGY_DATATYPES[datatype_string.split(":")[0]][0]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % datatype_string) \
            from e
    return datatype(x, *datatype_args)


def convert_from(x, datatype_string):
    try:
        datatype = ONTOLOGY_DATATYPES[datatype_string.split(":")[0]][1]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % datatype_string) \
            from e
    return datatype(x)


def to_string(x, maxsize=None):
    x = str(x)
    if maxsize and len(x) > int(maxsize):
        raise ValueError("String %s is longer than " % x
                         + "allowed maximum size of %s" % maxsize)
    return x


def to_uuid(x):
    if isinstance(x, uuid.UUID):
        return x
    if isinstance(x, str):
        return uuid.UUID(hex=x)
    if isinstance(x, int):
        return uuid.UUID(int=x)
    if isinstance(x, bytes):
        return uuid.UUID(bytes=x)
    raise ValueError("Specify a valid UUID")


def to_vector(x, *shape):
    x = np.array(x)
    return x.reshape([int(x) for x in shape])


def from_vector(x):
    return x.reshape((-1, )).tolist()


ONTOLOGY_DATATYPES = {
    "BOOL": (bool, bool),
    "INT": (int, int),
    "FLOAT": (float, float),
    "STRING": (to_string, str),
    "UUID": (to_uuid, str),
    "UNDEFINED": (str, str),
    "VECTOR": (to_vector, from_vector)
}
