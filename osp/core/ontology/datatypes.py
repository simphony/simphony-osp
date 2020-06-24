import uuid
import numpy as np
import rdflib


def convert_to(x, rdf_datatype):
    try:
        datatype = ONTOLOGY_DATATYPES[rdf_datatype][0]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % rdf_datatype) \
            from e
    return datatype(x)


def convert_from(x, rdf_datatype):
    try:
        datatype = ONTOLOGY_DATATYPES[rdf_datatype][1]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % rdf_datatype) \
            from e
    return datatype(x)


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


# def to_vector(x, *args): TODO
#     datatype, shape = parse_vector_args(args)
#     np_dtype = ONTOLOGY_DATATYPES[datatype][2]
#     if np_dtype is None:
#         raise ValueError("Cannot instantiate Vector with datatype %s"
#                          % datatype)
#     x = np.array(x, dtype=np_dtype)
#     return x.reshape([int(x) for x in shape])


# def parse_vector_args(args):
#     datatype = "FLOAT"
#     shape = args
#     if args[0] in ONTOLOGY_DATATYPES:
#         datatype = args[0]
#         shape = args[1:]
#     return datatype, list(map(int, shape))


def from_vector(x):
    return x.reshape((-1, )).tolist()


ONTOLOGY_DATATYPES = {
    rdflib.XSD.boolean: (bool, bool, np.dtype("bool")),
    rdflib.XSD.integer: (int, int, np.dtype("int")),
    rdflib.XSD.float: (float, float, np.dtype("float")),
    rdflib.XSD.string: (str, str, np.dtype("str")),
    None: (str, str, np.dtype("str"))
    # TODO vectors, uuid
}
