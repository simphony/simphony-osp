"""This module contains methods for datatype conversions."""

import ast
import uuid
import sqlite3
from abc import ABC, abstractmethod
from decimal import Decimal
from fractions import Fraction
from typing import (Any, Callable, List, Optional, Tuple, Union, Sequence,
                    MutableSequence)
from uuid import uuid4

import numpy as np
from rdflib import RDF, RDFS, XSD, BNode, Literal, URIRef, term
from rdflib.term import Identifier
from uuid import UUID

# --- Various type hints --- #
NestedSequence = Union[Sequence[Any], Sequence['NestedSequence']]
NestedMutableSequence = Union[MutableSequence[Any],
                              MutableSequence['NestedSequence']]
NestedTuple = Union[Tuple[Any, ...], Tuple['NestedTuple', ...]]
NestedList = Union[List[Any], List['NestedList']]
Pattern = Tuple[Union[Identifier, None], Union[Identifier, None],
                Union[Identifier, None]]
SimplePattern = Tuple[Union[Union[URIRef, Literal], None],
                      Union[Union[URIRef, Literal], None],
                      Union[Union[URIRef, Literal], None]]
Triple = Tuple[Identifier, Identifier, Identifier]
SimpleTriple = Tuple[Union[URIRef, Literal],
                     Union[URIRef, Literal],
                     Union[URIRef, Literal]]


class CustomDataType(ABC):
    iri: URIRef


class Vector(CustomDataType, tuple):
    iri = URIRef('http://www.osp-core.com/types#Vector')

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
            datatype = args[0] if args[0] in YML_TO_RDF else "FLOAT"
            shape = tuple(map(int, args[1:]))
        else:
            datatype = "FLOAT"
            shape = tuple()
        if return_yml_dtypes:
            return datatype, shape
        return YML_TO_RDF[datatype], shape

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


class UID(CustomDataType):
    iri = URIRef('http://www.osp-core.com/types#UID')
    data: Union[UUID, URIRef]

    def __init__(self,
                 value: Optional[Union['UID', UUID, str, int, bytes]] = None):
        super().__init__()
        invalid = False
        if value is None:
            value = uuid4()
        elif isinstance(value, UID):
            value = value.data
        elif isinstance(value, UUID):
            invalid = value.int == 0
        elif isinstance(value, (str, URIRef)):
            if value.startswith(CUDS_IRI_PREFIX):
                value = value[len(CUDS_IRI_PREFIX):]
            split = value.split(':')
            if len(split) > 1 and all(y != "" for y in split):
                value = URIRef(value)
            else:
                try:
                    value = UUID(hex=value)
                except ValueError:
                    invalid = True
        elif isinstance(value, int):
            value = uuid.UUID(int=value)
        elif isinstance(value, bytes):
            value = uuid.UUID(bytes=value)
        if invalid or not isinstance(value, (UUID, URIRef)):
            raise ValueError(f"Invalid uid: {value}.")
        self.data = value

    def __hash__(self):
        return self.data.__hash__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
               self.data.__eq__(other.data)

    def __repr__(self):
        return f"<class '{self.__class__.__module__}" \
               f".{self.__class__.__name__}':" \
               f" {self.data.__repr__()}>"

    def __str__(self):
        return self.data.__str__()

    def __format__(self, format_spec):
        return self.data.__format__(format_spec)

    def to_iri(self) -> URIRef:
        return self.data if isinstance(self.data, URIRef) else \
            URIRef(CUDS_IRI_PREFIX + str(self.data))

    def to_uuid(self) -> UUID:
        if not isinstance(self.data, UUID):
            raise Exception(f'Tried to get the UUID of the UID object '
                            f'{self}, but this object is an IRI.')
        return self.data

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds#"

# --- RDF TO PYTHON --- #


def get_all_python_subclasses(cls):
    return set(cls.__subclasses__()) | set(sc for c in
                                           cls.__subclasses__() for sc in
                                           get_all_python_subclasses(c))


# OWL data types
# See [Datatype Maps](https://www.w3.org/TR/owl2-syntax/#Datatype_Maps) on
#  the OWL specification.
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
OWL_COMPATIBLE_TYPES = tuple(x for x in OWL_TO_PYTHON.values())
OWLCompatibleType = Union[tuple(value for value in OWL_TO_PYTHON.values())]
# Custom STATIC data types (fixed URI).
CUSTOM_TO_PYTHON = {cls.iri: cls
                    for cls in get_all_python_subclasses(CustomDataType)}
CUSTOM_COMPATIBLE_TYPES = tuple(x for x in CUSTOM_TO_PYTHON.values())
CustomCompatibleType = Union[tuple(value for value in
                                   CUSTOM_TO_PYTHON.values())] if \
        CUSTOM_TO_PYTHON else None
# Custom DYNAMIC data types (unlimited amount of URIs).
#  TODO: Not supported.
# All RDF data types compatible with OSP-core, automatically generated from
#  the previous mappings.
RDF_TO_PYTHON = {}
RDF_TO_PYTHON.update(OWL_TO_PYTHON)
RDF_TO_PYTHON.update(CUSTOM_TO_PYTHON)
RDF_COMPATIBLE_TYPES = tuple(x for x in RDF_TO_PYTHON.values())
RDFCompatibleType = Union[tuple(value for value in RDF_TO_PYTHON.values())]
#  Bind all the types to RDFLib.
for iri, data_type in RDF_TO_PYTHON.items():
    term.bind(iri, data_type)

# --- YML TO RDF --- #
YML_TO_RDF = {
    "BOOL": XSD.boolean,
    "INT": XSD.integer,
    "FLOAT": XSD.float,
    "STRING": XSD.string,
    "VECTOR": Vector.iri,
}
