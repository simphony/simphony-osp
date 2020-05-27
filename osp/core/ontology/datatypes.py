import uuid
import numpy as np
import rdflib


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


def to_vector(x, *args):
    datatype, shape = parse_vector_args(args)
    np_dtype = ONTOLOGY_DATATYPES[datatype][2]
    if np_dtype is None:
        raise ValueError("Cannot instantiate Vector with datatype %s"
                         % datatype)
    x = np.array(x, dtype=np_dtype)
    return x.reshape([int(x) for x in shape])


def parse_vector_args(args):
    datatype = "FLOAT"
    shape = args
    if args[0] in ONTOLOGY_DATATYPES:
        datatype = args[0]
        shape = args[1:]
    return datatype, list(map(int, shape))


def from_vector(x):
    return x.reshape((-1, )).tolist()


ONTOLOGY_DATATYPES = {
    "BOOL": (bool, bool, np.dtype("bool"), rdflib.XSD.boolean),
    "INT": (int, int, np.dtype("int"), rdflib.XSD.integer),
    "FLOAT": (float, float, np.dtype("float"), rdflib.XSD.float),
    "STRING": (to_string, str, np.dtype("str"), rdflib.XSD.string),
    "UUID": (to_uuid, str, None, rdflib.XSD.string),
    "UNDEFINED": (str, str, np.dtype("str"), None),
    "VECTOR": (to_vector, from_vector, None, rdflib.XSD.string)
}
