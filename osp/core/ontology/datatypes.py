"""This module contains methods for datatype conversions."""


from base64 import b85encode, b85decode
import re
import sqlite3
from abc import ABC
from decimal import Decimal
from fractions import Fraction
from typing import Any, List, Optional, Tuple, Union, Sequence, MutableSequence
from uuid import uuid4, UUID

import numpy as np
from rdflib import XSD, Literal, URIRef, term
from rdflib.term import Identifier

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
    """Abstract class for the Python representation of custom data types.

    Such custom data types must also have an RDF representation (the IRI
    attribute and a string representation).

    Beware that any custom datatype will need to have a serializer to a
    datatype compatible with an SQL database, as well as a "lexicalizer" and a
    "constructor" for rdflib compatibility. See the piece of code
    immediately after the class for more details.
    """
    iri: URIRef


"""After the custom data type has been defined, the SQL serializer or
adapter, and the rdflib lexicalizer and constructor have to be specified.

The SQL adapter tells the sqlite3 Python library how to convert the object
to a data type that can be fit in the database. For example, for Vectors,
a binary representation is used, so this function converts the vector to a
binary blob.

The rdflib lexicalizer creates a string representation of the Python object.
For example, for vectors it is just a string representation of their binary
representation. This is string representation is what the user will find in
exported json or rdf files, and also what literals print to the Python console
through the __repr__ method.

The rdflib constructor does the opposite, create a Python representation
from a literal constructed from a string. For example, for vectors,
it converts the string representation of their binary form into the Vector
python object.

Both the lexicalizer and the constructor might be optional. For more
information, please check  the documentation and source code for
[`rdflib.term.bind`]
(https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.term.bind).
"""
# TODO: Is the data data fetched from the SQL database being recreated with the
#  rdflib constructor? This would not be the ideal behavior. Instead,
#  one would want to recreate the Python object using a sqlite3 converter,
#  just like an adapter is being used for saving.
# sqlite3.register_adapter(CustomDataType, lambda x: convet_to_sql_data())
# term.bind(CustomDataType.iri,
#           CustomDataType,
#           lexicalizer=lambda x: lexicalizer(x),
#           constructor=constructor x: constructor(x),
#           datatype_specific=True)


class Vector(CustomDataType):
    """Custom data type representing vectors.

    The data type is based on an underlying numpy array, or more
    specifically, the binary data for its shape, datatype and content.

    The reason behind not using directly a numpy array is that such objects
    are not hashable, but an RDF graph is a _set_ of triples, so having
    non-hashable objects leads to problems when it comes to handling and
    serializing the object.
    """
    # TODO: improve the interaction of the user with the object if possible:
    #   - If possible create the underlying numpy array when passing it as
    #     an argument to numpy's `array` function, instead of creating an array
    #     of vector objects.
    #   - Implement some operations with numpy arrays that return numpy arrays,
    #     just as it was done in the AttributeSet case.
    iri = URIRef('http://www.osp-core.com/types#Vector')
    _ELEMENT_LEN: int = 3
    _DTYPE_LEN: int = 1
    _SHAPE_LEN: int = 1

    @property
    def data(self) -> np.ndarray:
        """Returns the underlying numpy array, constructed from static data."""
        return np.frombuffer(self.__bytes,
                             dtype=self.__dtype)\
            .reshape(self.__shape)

    def __init__(self, value: Union[Literal,
                                    np.ndarray,
                                    NestedSequence,
                                    'Vector']):
        """Creates a new vector from `value`.

        The process of creating such vector can be divided in several steps:
            1. Construct a numpy array from `value`.
            2. Read its `dtype` and `shape` and store them as private
               attributes.
            3. Convert to bytes the data contained in the array and store
               them in the `__bytes` private attribute.
        """
        if isinstance(value, Vector):
            array = np.array(value.data)
        else:
            array = np.array(value)
        # TODO: restrict datatypes.
        self.__dtype = array.dtype
        self.__shape = array.shape
        self.__bytes = array.tobytes()

    def __str__(self) -> str:
        """Convert the vector to a string."""
        return self.data.__str__()

    def __repr__(self) -> str:
        """String representation for the vector (i.e. on Python console)."""
        array_repr = self.data.__repr__()
        array_repr = array_repr.replace('\n', ' ')
        array_repr = re.sub(r'[\s]{2,}', ' ', array_repr)
        return f"<{self.__class__.__module__}.{self.__class__.__name__}:" \
               f" {array_repr}>"

    def __hash__(self):
        """Get the vector's hash."""
        return hash((self.__bytes, self.__dtype, self.__shape))

    def __eq__(self, other: Union[Literal, np.ndarray,
                                  NestedSequence, 'Vector']):
        """Compare the vector to another object that can be vectorized."""
        return np.array_equal(self.data,
                              Vector(other).data)

    def to_blob(self) -> bytes:
        """Convert the vector to a bytes representation.

        Use `from_blob` to convert back to a vector.
        """
        blob = bytes()
        # Attach data type.
        blob += len(bytes(self.__dtype.str, encoding='UTF-8'))\
            .to_bytes(self._DTYPE_LEN, 'big')
        blob += bytes(self.__dtype.str, encoding='UTF-8')
        # Attach shape.
        blob += len(self.__shape).to_bytes(self._SHAPE_LEN, 'big')
        for integer in self.__shape:
            blob += integer.to_bytes(self._ELEMENT_LEN, 'big')
        # Attach array.
        blob += self.__bytes
        return blob

    @classmethod
    def from_blob(cls, blob: bytes) -> 'Vector':
        """Convert a bytes representation of a vector into a Vector object."""
        # Get data type.
        start_dtype = 0
        len_dtype = int.from_bytes(
            blob[start_dtype:cls._DTYPE_LEN], 'big')
        dtype = np.dtype(
            blob[start_dtype + cls._DTYPE_LEN:start_dtype
                 + cls._DTYPE_LEN + len_dtype].decode())
        # Get shape.
        start_shape = start_dtype + cls._DTYPE_LEN + len_dtype
        len_shape = int.from_bytes(
            blob[start_shape:start_shape + cls._SHAPE_LEN], 'big')
        shape = tuple(
            int.from_bytes(
                blob[start_shape + cls._SHAPE_LEN + i * cls._ELEMENT_LEN:
                     start_shape + cls._SHAPE_LEN + (i + 1)
                     * cls._ELEMENT_LEN],
                'big')
            for i in range(0, len_shape))
        # Get byte array.
        start_array = start_shape + cls._SHAPE_LEN \
            + len_shape * cls._ELEMENT_LEN
        byte_array = blob[start_array:]
        array = np.frombuffer(byte_array, dtype=dtype)\
            .reshape(shape)
        return Vector(array)

    def to_b85(self) -> str:
        """Convert the vector to a base85 representation.

        Use `from_b85` to convert back to a vector.
        """
        return b85encode(self.to_blob()).decode('UTF-8')

    @classmethod
    def from_b85(cls, string) -> 'Vector':
        """Convert a base 85 representation of a vector back into a Vector."""
        return cls.from_blob(b85decode(string.encode('UTF-8')))

    @classmethod
    def from_blob_or_b85(cls, value: Union[str, bytes]) -> 'Vector':
        """Restore a vector from a base 85 or bytes representation of it."""
        if isinstance(value, bytes):
            return cls.from_blob(value)
        elif isinstance(value, str):
            return cls.from_b85(value)
        else:
            raise TypeError("Only str and bytes are allowed.")


sqlite3.register_adapter(Vector, lambda x: x.to_blob())
for datatype in (Literal, np.ndarray, Sequence, list, tuple, Vector):
    term.bind(Vector.iri, datatype,
              lexicalizer=lambda x: Vector(x).to_b85(),
              constructor=lambda x: Vector.from_blob_or_b85(x),
              datatype_specific=True)


class UID(CustomDataType):
    """Custom type representing the unique identification of an individual.

    This data type is actually not used in the RDF graph itself (an IRI is
    used instead), but rather within OSP-core to identify the CUDS objects.
    It is always translated to an IRI before being passed to a graph. However,
    if you want to store a UID as a literal for whatever reason, you are
    welcome to use this custom data type.
    """
    iri = URIRef('http://www.osp-core.com/types#UID')
    data: Union[UUID, URIRef]

    def __init__(self,
                 value: Optional[Union['UID', UUID, str,
                                       URIRef, int, bytes]] = None):
        """Initializes a new UID from `value`."""
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
            value = UUID(int=value)
        elif isinstance(value, bytes):
            value = UUID(bytes=value)
        if invalid or not isinstance(value, (UUID, URIRef)):
            raise ValueError(f"Invalid uid: {value}.")
        self.data = value

    def __hash__(self):
        """Get the uid's hash."""
        return self.data.__hash__()

    def __eq__(self, other):
        """Compare the uid to other uids.

        Returns false if `other` does not belong to the same class.
        """
        return isinstance(other, self.__class__) and \
            self.data.__eq__(other.data)

    def __repr__(self):
        """String representation for the uid (i.e. on the Python console)."""
        return f"<class '{self.__class__.__module__}" \
               f".{self.__class__.__name__}':" \
               f" {self.data.__repr__()}>"

    def __str__(self):
        """Convert the uid to a string."""
        return self.data.__str__()

    def __format__(self, format_spec):
        """Formatter for UID objects."""
        return self.data.__format__(format_spec)

    def to_iri(self) -> URIRef:
        """Convert the UID to an IRI."""
        return self.data if isinstance(self.data, URIRef) else \
            URIRef(CUDS_IRI_PREFIX + str(self.data))

    def to_uuid(self) -> UUID:
        """Convert the UID to an UUID.

        Will only work if the underlying data is a UUID.
        """
        if not isinstance(self.data, UUID):
            raise Exception(f'Tried to get the UUID of the UID object '
                            f'{self}, but this object is an IRI.')
        return self.data


sqlite3.register_adapter(UID, lambda x: str(x))
for datatype in (UID, UUID, URIRef, str, int, bytes):
    if datatype in (int, bytes):
        def _lexicalizer(x):
            return str(UID(x))
    else:
        _lexicalizer = None
    term.bind(UID.iri, datatype,
              lexicalizer=_lexicalizer,
              constructor=None,
              datatype_specific=True)

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds#"

# --- RDF TO PYTHON --- #


def _get_all_python_subclasses(cls):
    return set(cls.__subclasses__()) | set(sc for c in
                                           cls.__subclasses__() for sc in
                                           _get_all_python_subclasses(c))


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
                    for cls in _get_all_python_subclasses(CustomDataType)}
CUSTOM_COMPATIBLE_TYPES = tuple(x for x in CUSTOM_TO_PYTHON.values())
CustomCompatibleType = Union[tuple(value for value in
                                   CUSTOM_TO_PYTHON.values())] if \
    CUSTOM_TO_PYTHON else None
# All RDF data types compatible with OSP-core, automatically generated from
#  the previous mappings.
RDF_TO_PYTHON = {}
RDF_TO_PYTHON.update(OWL_TO_PYTHON)
RDF_TO_PYTHON.update(CUSTOM_TO_PYTHON)
RDF_COMPATIBLE_TYPES = tuple(x for x in RDF_TO_PYTHON.values())
RDFCompatibleType = Union[tuple(value for value in RDF_TO_PYTHON.values())]
#  Bind all the types to RDFLib.
for iri, data_type in RDF_TO_PYTHON.items():
    # Skip custom data types, which where already bound below their definition.
    if iri == Vector.iri:
        continue
    elif iri == UID.iri:
        continue
    term.bind(iri, data_type)


# --- YML TO RDF --- #
YML_TO_RDF = {
    "BOOL": XSD.boolean,
    "INT": XSD.integer,
    "FLOAT": XSD.float,
    "STRING": XSD.string,
    "VECTOR": Vector.iri,
}
