"""This module contains methods for datatype conversions."""

import ast
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal
from fractions import Fraction
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union, \
    Sequence, MutableSequence

from rdflib import RDF, RDFS, XSD, Literal, URIRef

from osp.core.ontology.cuba import rdflib_cuba

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds#"

# See [Datatype Maps](https://www.w3.org/TR/owl2-syntax/#Datatype_Maps) on
# the OWL specification.
# All the classes on the RHS need to be hashable.
OWL_TO_PYTHON = {URIRef('http://www.w3.org/2002/07/owl#real'): float,
                 URIRef('http://www.w3.org/2002/07/owl#rational'): Fraction,
                 # ↑ Workaround
                 #   [rdflib issue #1378](
                 #   https://github.com/RDFLib/rdflib/issues/1378).
                 XSD.decimal: Decimal,
                 XSD.integer: int,
                 XSD.nonNegativeInteger: int,
                 XSD.nonPositiveInteger: int,
                 XSD.positiveInteger: int,
                 XSD.negativeInteger: int,
                 XSD.long: int,
                 XSD.int: int,
                 XSD.short: int,
                 # XSD.byte: ?, (TODO: not yet supported)
                 XSD.unsignedLong: int,
                 XSD.unsignedInt: int,
                 XSD.unsignedShort: int,
                 # XSD.unsignedByte: ?, (TODO: not yet supported)
                 XSD.double: float,
                 XSD.float: float,
                 XSD.string: str,
                 # XSD.normalizedString: ?, (TODO: not yet supported)
                 # XSD.token: ?, (TODO: not yet supported)
                 # XSD.Name: ?, (TODO: not yet supported)
                 # XSD.NCName: ?, (TODO: not yet supported)
                 # XSD.NMTOKEN: ?, (TODO: not yet supported)
                 XSD.boolean: bool,
                 # XSD.hexBinary: ?, (TODO: not yet supported)
                 # XSD.base64Binary: ?, (TODO: not yet supported)
                 XSD.anyURI: URIRef,
                 # XSD.dateTime: ?, (TODO: not yet supported)
                 # XSD.dateTimeStamp: ?, (TODO: not yet supported)
                 # RDF.XMLLiteral: ?, (TODO: not yet supported)
                 }
PYTHON_TO_OWL = {item: key for key, item in OWL_TO_PYTHON.items()}
OWL_COMPATIBLE_TYPES = tuple(x for x in OWL_TO_PYTHON.values())
OWLCompatibleType = Union[tuple(value for value in OWL_TO_PYTHON.values())]

# All the classes on the RHS need to be hashable.
CUSTOM_TO_PYTHON = dict()
PYTHON_TO_CUSTOM = {item: key for key, item in CUSTOM_TO_PYTHON.items()}
CUSTOM_COMPATIBLE_TYPES = tuple(x for x in CUSTOM_TO_PYTHON.values())
CustomCompatibleType = Union[tuple(value for value in
                                   CUSTOM_TO_PYTHON.values())] if \
        CUSTOM_TO_PYTHON else None

# Automatically generated from the previous mappings.
RDF_TO_PYTHON = dict()
RDF_TO_PYTHON.update(OWL_TO_PYTHON)
RDF_TO_PYTHON.update(CUSTOM_TO_PYTHON)
RDF_COMPATIBLE_TYPES = tuple(x for x in RDF_TO_PYTHON.values())
RDFCompatibleType = Union[tuple(value for value in RDF_TO_PYTHON.values())]

YML_DATATYPES = {
    "BOOL": XSD.boolean,
    "INT": XSD.integer,
    "FLOAT": XSD.float,
    "STRING": XSD.string,
}


class CustomDataType(ABC):

    @classmethod
    @abstractmethod
    def compatible(cls, rdf_datatype: URIRef) -> bool:
        """Determine whether an RDF datatype can be represented by this class.

        Args:
            rdf_datatype: The RDF datatype to evaluate.

        Returns:
            True when such datatype is adequately represented by this class,
            False when not.
        """
        pass

    def __init__(self, value: Union[Literal, Any]):
        """Take a Python object and convert it to an instance of this datatype.

        Args:
            value: A Python object or an RDF literal.

        Returns:
            An instance of this custom datatype.
        """
        if isinstance(value, Literal) and not self.compatible(value.datatype):
            raise TypeError(f"Datatype {value.datatype} not compatible "
                            f"with {self.__class__}.")


NestedSequence = Union[Sequence[Any], Sequence['NestedSequence']]
NestedMutableSequence = Union[MutableSequence[Any],
                              MutableSequence['NestedSequence']]
NestedTuple = Union[Tuple[Any, ...], Tuple['NestedTuple', ...]]
NestedList = Union[List[Any], List['NestedList']]


class Vector(CustomDataType, tuple):
    _PREFIX: str = str(rdflib_cuba["_datatypes/VECTOR-"])

    @classmethod
    def compatible(cls, rdf_datatype: URIRef) -> bool:
        return str(rdf_datatype).startswith(cls._PREFIX)

    def __new__(cls, value: Union[Literal, NestedSequence]):
        if isinstance(value, Literal):
            array = Vector._literal_to_array(value)
        else:  # Assuming NestedSequence.
            array = Vector._nested_sequence_to_tuple(value)
        array = tuple(array)
        return tuple.__new__(cls, array)

    @staticmethod
    def _literal_to_array(value: Literal) -> NestedTuple:
        array = ast.literal_eval(str(value))
        args = str(value.datatype)[len(Vector._PREFIX):].split("-")
        args = tuple(x for x in args if x)
        rdf_dtype, shape = Vector._parse_vector_args(args)
        python_dtype = RDF_TO_PYTHON[rdf_dtype]
        # Validate shape if specified.
        if shape:
            actual_shape = Vector._get_sequence_shape(array)
            if not actual_shape == shape:
                raise ValueError(f'Invalid shape {shape} for array {array}.')
        # Convert to python dtype and nested tuple.
        array = Vector._nested_sequence_to_tuple(array, python_dtype)
        return array

    @staticmethod
    def _parse_vector_args(args: List[str], return_yml_dtypes: bool = False) \
            -> \
            Tuple[Union[str, URIRef], Tuple[int]]:
        """Parse the YAML datatype description of a vector.

        Args:
            args: The arguments of the vector (shape and datatype of elements).
            return_yml_dtypes: Whether to return the datatype of the elements
                as YML string or RDF datatype. Defaults to False.

        Returns:
            Tuple[Union[str, URIRef], Tuple[int]]: datatype of elements and
                shape of array
        """
        if args:
            datatype = args[0] if args[0] in YML_DATATYPES else "FLOAT"
            shape = tuple(map(int, args[1:]))
        else:
            datatype = "FLOAT"
            shape = tuple()
        if return_yml_dtypes:
            return datatype, shape
        return YML_DATATYPES[datatype], shape

    @staticmethod
    def _get_sequence_shape(seq: Sequence) -> Tuple[int]:
        # Get previous shape datatype value.
        shape = []
        exploration = seq
        while isinstance(exploration, Sequence):
            shape.append(len(exploration))
            exploration = exploration[0]
        return tuple(shape)

    @staticmethod
    def _nested_sequence_to_tuple(array: NestedSequence,
                                  target: Optional[Callable] = None) -> \
            NestedTuple:
        new_array = [None] * len(array)
        for i, x in enumerate(array):
            if isinstance(x, Sequence):
                new_array[i] = Vector._nested_sequence_to_tuple(x)
            else:
                new_array[i] = x if target is None else target(x)
        else:
            return tuple(new_array)


class String(CustomDataType, str):
    _PREFIX = str(rdflib_cuba["_datatypes/STRING-"])

    def __new__(cls, o: object):
        return str.__new__(cls, o)

    @classmethod
    def compatible(cls, rdf_datatype: URIRef) -> bool:
        return str(rdf_datatype).startswith(cls._PREFIX)


def normalize_python_object(value: Any, rdf_datatype: URIRef) -> Any:
    """Convert object to one that is compatible with the target RDF dataype.

    Args:
        value: The python object to be converted.
        rdf_datatype: The RDF datatype with which the result will be compatible.

    Raises:
        RuntimeError: Unknown datatype.

    Returns:
        A new python object, compatible with the specified `rdf_datatype`.
    """
    try:
        datatype = _get_normalized_python_type(rdf_datatype)
    except KeyError as e:
        raise RuntimeError("unknown datatype %s" % rdf_datatype) \
            from e
    return datatype(Literal(value, datatype=rdf_datatype))


def _get_normalized_python_type(rdf_datatype: URIRef) -> Callable:
    """Get the python datatype that is compatible with a given RDF datatype.

    Args:
        rdf_datatype: The rdf datatype.

    Raises:
        RuntimeError: Unknown datatype specified.

    Returns:
        Type or function to convert to the Python type.
    """
    if rdf_datatype is None:
        return str
    if rdf_datatype in OWL_TO_PYTHON:
        return OWL_TO_PYTHON[rdf_datatype]
    for custom_data_type in [String, Vector]:
        if custom_data_type.compatible(rdf_datatype):
            return custom_data_type
    else:
        raise RuntimeError(f"Unknown datatype {rdf_datatype}")


def to_uid(x):
    """Convert given value to an uid.

    Args:
        x (Any): The value to convert

    Raises:
        ValueError: Invalid UUID specified

    Returns:
        Union[UUID, URIRef]: The resulting UUID
    """
    if isinstance(x, uuid.UUID):
        pass
    elif isinstance(x, str):
        if x.startswith(CUDS_IRI_PREFIX):
            x = x[len(CUDS_IRI_PREFIX):]
        split = x.split(':')
        if len(split) > 1 and all(y != "" for y in split):
            x = URIRef(x)
        else:
            x = uuid.UUID(hex=x)
    elif isinstance(x, int):
        x = uuid.UUID(int=x)
    elif isinstance(x, bytes):
        x = uuid.UUID(bytes=x)
    else:
        x = False
    if x is False:
        raise ValueError("Specify a valid uid")
    else:
        return x


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


def get_rdflib_datatype(yml_datatype, graph=None):
    """Get rdflib datatype from given YAML datatype.

    Args:
        yml_datatype (str): YAMl datatype
        graph (Graph, optional): The rdflib graph, necessary if a new
            datatype needs to be created. Defaults to None.

    Returns:
        URIRef: The IRI of the datatype
    """
    if yml_datatype in YML_DATATYPES:
        return YML_DATATYPES[yml_datatype]
    args = yml_datatype.split(":")
    if args[0] == "VECTOR":
        dtype, shape = Vector._parse_vector_args(args[1:],
                                                 return_yml_dtypes=True)
        return _add_vector_datatype(graph, shape, dtype)
    if args[0] == "STRING" and len(args) == 2:
        length = int(args[1])
        return _add_string_datatype(graph, length)


def _add_string_datatype(graph, length):
    """Add a custom string datatype to the graph reference.

    Args:
        graph (Graph): The graph to add the datatype to
        length (int): The maximum length of the string

    Returns:
        URIRef: The iri of the new datatype
    """
    iri = rdflib_cuba[f"_datatypes/STRING-{length}"]
    triple = (iri, RDF.type, RDFS.Datatype)
    if graph is None or triple in graph:
        return iri
    graph.add(triple)
    # length_triple = (iri, rdflib_cuba._length, Literal(int(length)))
    # graph.add(length_triple)
    return iri


def _add_vector_datatype(graph, shape, dtype):
    """Add custom vector datatype to the graph.

    Args:
        graph (Graph): The graph to add the datatype to
        shape (Tuple[int]): The shape of the array
        dtype (str): The datatype of the elements as YAML datatype

    Returns:
        [type]: [description]
    """
    shape = list(map(int, shape))
    iri = rdflib_cuba[f"_datatypes/VECTOR-{dtype}-"
                      + "-".join(map(str, shape))]
    triple = (iri, RDF.type, RDFS.Datatype)
    if graph is None or triple in graph:
        return iri
    graph.add(triple)
    # dtype_triple = (iri, rdflib_cuba._length, YML_DATATYPES[dtype])
    # graph.add(dtype_triple)
    # shape = list(map(Literal, shape))
    # shape = collection.Collection(graph, [], shape)
    # shape_triple = (iri, rdflib_cuba._shape, shape.uri)
    # graph.add(shape_triple)
    return iri
