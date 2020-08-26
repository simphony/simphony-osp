import uuid
import numpy as np
import rdflib
import ast

from osp.core.ontology.cuba import rdflib_cuba


def convert_to(x, rdf_datatype):
    """Convert a value to the given datatype.

    Args:
        x (Any): The value to convert
        rdf_datatype (URIRef): The datatype to convert to.

    Raises:
        RuntimeError: Unknown datatype

    Returns:
        Any: The converted value.
    """
    try:
        datatype = get_python_datatype(rdf_datatype)[0]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % rdf_datatype) \
            from e
    return datatype(x)


def convert_from(x, rdf_datatype):
    """Convert to a python basic type.

    Args:
        x (Any): The value to convert
        rdf_datatype (URIRef): The datatype of x

    Raises:
        RuntimeError: Unknown datatype provided.

    Returns:
        Any: The converted value
    """
    try:
        datatype = get_python_datatype(rdf_datatype)[1]
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % rdf_datatype) \
            from e
    return datatype(x)


def to_uuid(x):
    """Convert given value to a UUID.

    Args:
        x (Any): The value to convert

    Raises:
        ValueError: Invalid UUID specified

    Returns:
        UUID: The resulting UUID
    """
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
    """Convert given value to a string.

    Args:
        x (Any): The value to convert
        maxsize (int, optional): The maximum length of the string.
            Defaults to None.

    Raises:
        ValueError: String longer than specified maximum length.

    Returns:
        str: The converted value
    """
    x = str(x)
    if maxsize and len(x) > int(maxsize):
        raise ValueError("String %s is longer than " % x
                         + "allowed maximum size of %s" % maxsize)
    return x


def to_vector(x, np_dtype, shape):
    """Convert the given value to numpy array.

    Args:
        x (Any): The value to convert
        np_dtype (np.dtype): The numpy datatype if the array elements.
        shape (Tuple[int]): The shape of the array

    Returns:
        np.ndarray: The converted value
    """
    if isinstance(x, rdflib.Literal):
        x = ast.literal_eval(str(x))
    x = np.array(x, dtype=np_dtype)
    return x.reshape([int(x) for x in shape])


def from_vector(x):
    """Convert the given numpy array to a python flat list.

    Args:
        x (np.ndarray): The value to convert

    Returns:
        List: The converted value
    """
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
    """Get the python datatype for a given rdf datatype.

    Args:
        rdf_datatype (URIRef): The rdf datatype

    Raises:
        RuntimeError: Unknown datatype specified.

    Returns:
        Callable: Type or function to convert to python type
    """
    if rdf_datatype in RDF_DATATYPES:
        return RDF_DATATYPES[rdf_datatype]
    str_prefix = str(rdflib_cuba["_datatypes/STRING-"])
    vec_prefix = str(rdflib_cuba["_datatypes/VECTOR-"])
    if str(rdf_datatype).startswith(str_prefix):
        maxsize = int(str(rdf_datatype)[len(str_prefix):])
        return (lambda x: to_string(x, maxsize=maxsize), str, np.dtype("str"))
    if str(rdf_datatype).startswith(vec_prefix):
        args = str(rdf_datatype)[len(str_prefix):].split("-")
        dtype, shape = _parse_vector_args(args)
        np_dtype = RDF_DATATYPES[dtype][2]
        return (lambda x: to_vector(x, np_dtype, shape), from_vector, np_dtype)
    raise RuntimeError(f"Unknown datatype {rdf_datatype}")


YML_DATATYPES = {
    "BOOL": rdflib.XSD.boolean,
    "INT": rdflib.XSD.integer,
    "FLOAT": rdflib.XSD.float,
    "STRING": rdflib.XSD.string,
    "UUID": "UUID"
}


def get_rdflib_datatype(yml_datatype, graph=None):
    """Get rdflib datatype from given YAML datatype.

    Args:
        yml_datatype (str): YAMl datatype
        graph (rdflib.Graph, optional): The rdflib graph, necessary if a new
            datatype needs to be created. Defaults to None.

    Returns:
        URIRef: The IRI of the datatype
    """
    if yml_datatype in YML_DATATYPES:
        return YML_DATATYPES[yml_datatype]
    args = yml_datatype.split(":")
    if args[0] == "VECTOR":
        dtype, shape = _parse_vector_args(args[1:], return_yml_dtypes=True)
        return _add_vector_datatype(graph, shape, dtype)
    if args[0] == "STRING" and len(args) == 2:
        length = int(args[1])
        return _add_string_datatype(graph, length)


def _parse_vector_args(args, return_yml_dtypes=False):
    """Parse the YAML datatype description of a vector.

    Args:
        args (str): The arguments of the vector
            (shape and datatype of elememts)
        return_yml_dtypes (bool, optional): Whether to return the datatype of
            the elements as YML string or rdflib datatype. Defaults to False.

    Returns:
        Tuple[Union[str, URIRef], Tuple[int]]: datatype of elements and
            shape of array
    """
    datatype = "FLOAT"
    shape = args
    if args[0] in YML_DATATYPES:
        datatype = args[0]
        shape = args[1:]
    if return_yml_dtypes:
        return datatype, list(map(int, shape))
    return YML_DATATYPES[datatype], list(map(int, shape))


def _add_string_datatype(graph, length):
    """Add a custom string datatype to the graph refering.

    Args:
        graph (rdflib.Graph): The graph to add the datatype to
        length (int): The maximim length of the string

    Returns:
        URIRef: The iri of the new datatype
    """
    iri = rdflib_cuba[f"_datatypes/STRING-{length}"]
    triple = (iri, rdflib.RDF.type, rdflib.RDFS.Datatype)
    if graph is None or triple in graph:
        return iri
    graph.add(triple)
    # length_triple = (iri, rdflib_cuba._length, rdflib.Literal(int(length)))
    # graph.add(length_triple)
    return iri


def _add_vector_datatype(graph, shape, dtype):
    """Add custom vector datatype to the graph.

    Args:
        graph (rdflib.Graph): The graph to add the datatype to
        shape (Tuple[int]): The shape of the array
        dtype (str): The datatype of the elements as YAML datatype

    Returns:
        [type]: [description]
    """
    shape = list(map(int, shape))
    iri = rdflib_cuba[f"_datatypes/VECTOR-{dtype}-"
                      + "-".join(map(str, shape))]
    triple = (iri, rdflib.RDF.type, rdflib.RDFS.Datatype)
    if graph is None or triple in graph:
        return iri
    graph.add(triple)
    # dtype_triple = (iri, rdflib_cuba._length, YML_DATATYPES[dtype])
    # graph.add(dtype_triple)
    # shape = list(map(rdflib.Literal, shape))
    # shape = rdflib.collection.Collection(graph, [], shape)
    # shape_triple = (iri, rdflib_cuba._shape, shape.uri)
    # graph.add(shape_triple)
    return iri
