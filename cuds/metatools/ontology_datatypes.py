# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


def convert(x, datatype_string):
    datatype_args = datatype_string.split(":")[1:]
    try:
        datatype = ONTOLOGY_DATATYPES[datatype_string.split(":")[0]]
    except KeyError as e:
        raise RuntimeError("The specified datatype %s" % datatype_string) \
            from e
    return datatype(x, *datatype_args)


def to_string(x, maxsize=None):
    x = str(x)
    if maxsize and len(x) > int(maxsize):
        raise ValueError("String %s is longer than " % x
                         + "allowed maximum size of %s" % maxsize)
    return x


ONTOLOGY_DATATYPES = {
    "INT": int,
    "FLOAT": float,
    "STRING": to_string,
}
