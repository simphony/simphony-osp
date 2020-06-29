import uuid
import numpy as np
import rdflib
import ast

from osp.core.ontology.cuba import rdflib_cuba


def convert_to(x, rdf_datatype):
    try:
        datatype = get_python_datatype(rdf_datatype)[0]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % rdf_datatype) \
            from e
    return datatype(x)


def convert_from(x, rdf_datatype):
    try:
        datatype = get_python_datatype(rdf_datatype)[1]
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


def to_string(x, maxsize=None):
    x = str(x)
    if maxsize and len(x) > int(maxsize):
        raise ValueError("String %s is longer than " % x
                         + "allowed maximum size of %s" % maxsize)
    return x


def to_vector(x, np_dtype, shape):
    if isinstance(x, rdflib.Literal):
        x = ast.literal_eval(str(x))
    x = np.array(x, dtype=np_dtype)
    return x.reshape([int(x) for x in shape])


def from_vector(x):
    return x.reshape((-1, )).tolist()


RDF_DATATYPES = {
    rdflib.XSD.boolean: (bool, bool, np.dtype("bool")),
    rdflib.XSD.integer: (int, int, np.dtype("int")),
    rdflib.XSD.float: (float, float, np.dtype("float")),
    rdflib.XSD.string: (str, str, np.dtype("str")),
    "UUID": (to_uuid, str, np.dtype("str")),
    None: (str, str, np.dtype("str"))
}


def get_python_datatype(rdf_datatype):
    if rdf_datatype in RDF_DATATYPES:
        return RDF_DATATYPES[rdf_datatype]
    str_prefix = str(rdflib_cuba["datatypes/STRING-"])
    vec_prefix = str(rdflib_cuba["datatypes/VECTOR-"])
    if str(rdf_datatype).startswith(str_prefix):
        maxsize = int(str(rdf_datatype)[len(str_prefix):])
        return (lambda x: to_string(x, maxsize=maxsize), str, np.dtype("str"))
    if str(rdf_datatype).startswith(vec_prefix):
        args = str(rdf_datatype)[len(str_prefix):].split("-")
        dtype, shape = _parse_vector_args(args)
        np_dtype = RDF_DATATYPES[YML_DATATYPES[dtype]][2]
        return (lambda x: to_vector(x, np_dtype, shape), from_vector, np_dtype)
    raise RuntimeError(f"Unknown datatype {rdf_datatype}")


YML_DATATYPES = {
    "BOOL": rdflib.XSD.boolean,
    "INT": rdflib.XSD.integer,
    "FLOAT": rdflib.XSD.float,
    "STRING": rdflib.XSD.string,
}


def get_rdflib_datatype(graph, yml_datatype):
    if yml_datatype in YML_DATATYPES:
        return YML_DATATYPES[yml_datatype]
    args = yml_datatype.split(":")
    if args[0] == "VECTOR":
        dtype, shape = _parse_vector_args(args[1:])
        return _add_vector_datatype(graph, shape, dtype)
    if args[0] == "STRING" and len(args) == 2:
        length = int(args[1])
        return _add_string_datatype(graph, length)


def _parse_vector_args(args):
    datatype = "FLOAT"
    shape = args
    if args[0] in YML_DATATYPES:
        datatype = args[0]
        shape = args[1:]
    return datatype, list(map(int, shape))


def _add_string_datatype(graph, length):
    iri = rdflib_cuba[f"datatypes/STRING-{length}"]
    triple = (iri, rdflib.RDF.type, rdflib.RDFS.Datatype)
    if triple in graph:
        return
    graph.add(triple)
    # length_triple = (iri, rdflib_cuba._length, rdflib.Literal(int(length)))
    # graph.add(length_triple)
    return iri


def _add_vector_datatype(graph, shape, dtype):
    shape = list(map(int, shape))
    iri = rdflib_cuba[f"datatypes/VECTOR-{dtype}-"
                      + "-".join(map(str, shape))]
    triple = (iri, rdflib.RDF.type, rdflib.RDFS.Datatype)
    if triple in graph:
        return
    graph.add(triple)
    # dtype_triple = (iri, rdflib_cuba._length, YML_DATATYPES[dtype])
    # graph.add(dtype_triple)
    # shape = list(map(rdflib.Literal, shape))
    # shape = rdflib.collection.Collection(graph, [], shape)
    # shape_triple = (iri, rdflib_cuba._shape, shape.uri)
    # graph.add(shape_triple)
    return iri
