"""This module contains methods for datatype conversions."""
from __future__ import annotations

import logging
import re
import sys
from abc import ABC
from base64 import b85decode, b85encode
from datetime import datetime
from decimal import Decimal
from distutils.version import StrictVersion
from fractions import Fraction
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    MutableSequence,
    Optional,
    Sequence,
    Tuple,
    Union,
)
from uuid import UUID, uuid4

import numpy as np
import rdflib
from rdflib import RDFS, XSD, BNode, Literal, URIRef, term
from rdflib.term import Identifier, Node

if TYPE_CHECKING:
    from simphony_osp.ontology.annotation import OntologyAnnotation
    from simphony_osp.ontology.attribute import OntologyAttribute
    from simphony_osp.ontology.individual import OntologyIndividual
    from simphony_osp.ontology.oclass import OntologyClass
    from simphony_osp.ontology.relationship import OntologyRelationship

# Some IDEs may not detect a type alias defined as Union[...] otherwise.
python_version_supports_type_alias = (
    StrictVersion("3.10")
    <= StrictVersion(f"{sys.version_info.major}.{sys.version_info.minor}")
    < StrictVersion("4.0")
)
if python_version_supports_type_alias:
    from typing import TypeAlias
else:
    from typing import Any as TypeAlias

__all__ = [
    "ATTRIBUTE_VALUE_TYPES",
    "AttributeValue",
    "AnnotationValue",
    "Identifier",
    "NestedList",
    "NestedMutableSequence",
    "NestedSequence",
    "NestedTuple",
    "OntologyPredicate",
    "Pattern",
    "PredicateValue",
    "RelationshipValue",
    "SimplePattern",
    "SimpleTriple",
    "Triple",
    "UID",
    "Vector",
    "rdf_to_python",
]

# Collection type hints
NestedSequence = Union[Sequence[Any], Sequence["NestedSequence"]]
NestedMutableSequence = Union[
    MutableSequence[Any], MutableSequence["NestedSequence"]
]
NestedTuple = Union[Tuple[Any, ...], Tuple["NestedTuple", ...]]
NestedList = Union[List[Any], List["NestedList"]]


# Ignore RDFLib binding warning.
class _BindingWarningFilter(logging.Filter):
    """Filters datatype rebinding warnings from RDFLib."""

    def filter(self, record):
        """Checks that the string is not contained in the message."""
        return " was already bound. Rebinding." not in record.getMessage()


rdflib_term_logger = logging.getLogger(rdflib.term.__name__)
rdflib_term_logger.addFilter(_BindingWarningFilter())


class CustomDataType(ABC):
    """Abstract class for the Python representation of custom data types.

    Such custom data types must also have an RDF representation (the IRI
    attribute and a string representation).

    Beware that any custom datatype will need to have a "lexicalizer" and a
    "constructor" for rdflib compatibility. See the piece of code
    immediately after this class for more details.
    """

    iri: URIRef


"""After the custom data type has been defined, the rdflib lexicalizer
and constructor have to be specified.

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
    iri = URIRef("https://www.simphony-osp.eu/types#Vector")

    _ELEMENT_LEN: int = 3
    _DTYPE_LEN: int = 1
    _SHAPE_LEN: int = 1

    @property
    def data(self) -> np.ndarray:
        """Returns the underlying numpy array, constructed from static data."""
        return np.frombuffer(self.__bytes, dtype=self.__dtype).reshape(
            self.__shape
        )

    def __getitem__(self, item: int):
        """Slice the underlying numpy array."""
        return self.data[item]

    def __init__(
        self, value: Union[Literal, np.ndarray, NestedSequence, Vector]
    ):
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
        array_repr = array_repr.replace("\n", " ")
        array_repr = re.sub(r"\s{2,}", " ", array_repr)
        return (
            f"<{self.__class__.__module__}.{self.__class__.__name__}:"
            f" {array_repr}>"
        )

    def __hash__(self):
        """Get the vector's hash."""
        return hash((self.__bytes, self.__dtype, self.__shape))

    def __eq__(
        self, other: Union[Literal, np.ndarray, NestedSequence, Vector]
    ):
        """Compare the vector to another object that can be vectorized."""
        return np.array_equal(self.data, Vector(other).data)

    def to_blob(self) -> bytes:
        """Convert the vector to a bytes representation.

        Use `from_blob` to convert back to a vector.
        """
        blob = bytes()
        # Attach data type.
        blob += len(bytes(self.__dtype.str, encoding="UTF-8")).to_bytes(
            self._DTYPE_LEN, "big"
        )
        blob += bytes(self.__dtype.str, encoding="UTF-8")
        # Attach shape.
        blob += len(self.__shape).to_bytes(self._SHAPE_LEN, "big")
        for integer in self.__shape:
            blob += integer.to_bytes(self._ELEMENT_LEN, "big")
        # Attach array.
        blob += self.__bytes
        return blob

    @classmethod
    def from_blob(cls, blob: bytes) -> Vector:
        """Convert a bytes representation of a vector into a Vector object."""
        # Get data type.
        start_dtype = 0
        len_dtype = int.from_bytes(blob[start_dtype : cls._DTYPE_LEN], "big")
        dtype = np.dtype(
            blob[
                start_dtype
                + cls._DTYPE_LEN : start_dtype
                + cls._DTYPE_LEN
                + len_dtype
            ].decode()
        )
        # Get shape.
        start_shape = start_dtype + cls._DTYPE_LEN + len_dtype
        len_shape = int.from_bytes(
            blob[start_shape : start_shape + cls._SHAPE_LEN], "big"
        )
        shape = tuple(
            int.from_bytes(
                blob[
                    start_shape
                    + cls._SHAPE_LEN
                    + i * cls._ELEMENT_LEN : start_shape
                    + cls._SHAPE_LEN
                    + (i + 1) * cls._ELEMENT_LEN
                ],
                "big",
            )
            for i in range(0, len_shape)
        )
        # Get byte array.
        start_array = (
            start_shape + cls._SHAPE_LEN + len_shape * cls._ELEMENT_LEN
        )
        byte_array = blob[start_array:]
        array = np.frombuffer(byte_array, dtype=dtype).reshape(shape)
        return Vector(array)

    def to_b85(self) -> str:
        """Convert the vector to a base85 representation.

        Use `from_b85` to convert back to a vector.
        """
        return b85encode(self.to_blob()).decode("UTF-8")

    @classmethod
    def from_b85(cls, string) -> Vector:
        """Convert a base 85 representation of a vector back into a Vector."""
        return cls.from_blob(b85decode(string.encode("UTF-8")))

    @classmethod
    def from_blob_or_b85(cls, value: Union[str, bytes]) -> Vector:
        """Restore a vector from a base 85 or bytes representation of it."""
        if isinstance(value, bytes):
            return cls.from_blob(value)
        elif isinstance(value, str):
            return cls.from_b85(value)
        else:
            raise TypeError("Only str and bytes are allowed.")


for datatype in (Literal, np.ndarray, Sequence, list, tuple, Vector):
    term.bind(
        Vector.iri,
        datatype,
        lexicalizer=lambda x: Vector(x).to_b85(),
        constructor=lambda x: Vector.from_blob_or_b85(x),
        datatype_specific=True,
    )


class UID(CustomDataType):
    """Custom data type representing the unique identifier of an entity.

    This data type is actually not used in the RDF graph itself (an RDF
    identifier is used instead), but rather within SimPhoNy to identify the
    ontology entities objects. It plays the same role as a semantic web
    identifier, and can always be converted to one. In fact, such conversion
    is always performed before it is used in a graph operation. The only
    difference is that it can be based not only on semantic web identifiers
    such as blank nodes or IRIs, but also on other datatypes that can be
    converted on the fly to semantic-web compatible identifiers.

    However, if you want to store a UID as a literal for whatever reason,
    you are welcome to use this custom data type.
    """

    iri = URIRef("https://www.simphony-osp.eu/types#UID")
    data: Union[Node, UUID]

    __slots__ = ("data",)

    def __init__(
        self,
        value: Optional[Union[UID, UUID, str, Node, int, bytes]] = None,
    ):
        """Initializes a new UID from `value`."""
        super().__init__()
        invalid = False
        if value is None:
            value = uuid4()
        elif isinstance(value, str):
            if value.startswith(ENTITY_IRI_PREFIX):
                value = value[len(ENTITY_IRI_PREFIX) :]
                try:
                    value = UUID(hex=value)
                except ValueError:
                    invalid = True
            elif not isinstance(value, Node):
                value = URIRef(value)
        elif isinstance(value, UUID):
            invalid = value.int == 0
        elif isinstance(value, int):
            value = UUID(int=value)
        elif isinstance(value, bytes):
            value = UUID(bytes=value)
        elif isinstance(value, UID):
            value = value.data
        if invalid or not isinstance(value, (UUID, Node)):
            raise ValueError(f"Invalid uid: {value}.")
        self.data = value

    def __hash__(self):
        """Get the uid's hash."""
        return hash(self.data)

    def __eq__(self, other):
        """Compare the uid to other uids.

        Returns false if `other` does not belong to the same class.
        """
        return isinstance(other, self.__class__) and self.data.__eq__(
            other.data
        )

    def __repr__(self):
        """String representation for the uid (i.e. on the Python console)."""
        return (
            f"<class '{self.__class__.__module__}"
            f".{self.__class__.__name__}':"
            f" {self.data.__repr__()}>"
        )

    def __str__(self):
        """Convert the uid to a string."""
        return self.data.__str__()

    def __format__(self, format_spec):
        """Formatter for UID objects."""
        return self.data.__format__(format_spec)

    def to_iri(self) -> URIRef:
        """Convert the UID to an IRI."""
        data = self.data
        if isinstance(data, UUID):
            return_iri = URIRef(ENTITY_IRI_PREFIX + str(data))
        elif isinstance(data, URIRef):
            return_iri = data
        elif isinstance(data, BNode):
            raise TypeError(
                f"The UID {self} cannot be converted to an IRI, "
                f"as it is a blank node."
            )
        else:
            raise RuntimeError(f"Illegal UID type {type(data)}.")
        return return_iri

    def to_uuid(self) -> UUID:
        """Convert the UID to a UUID.

        Will only work if the underlying data is a UUID.
        """
        data = self.data
        if not isinstance(data, UUID):
            raise Exception(
                f"Tried to get the UUID of the UID object "
                f"{self}, but this object is not a UUID."
            )
        return data

    def to_identifier(self) -> Identifier:
        """Convert the UID to a RDFLib Identifier."""
        data = self.data
        # logic in `to_iri` duplicated here in exchange for performance gains
        return (
            URIRef(ENTITY_IRI_PREFIX + str(data))
            if isinstance(data, UUID)
            else data
        )


for datatype in (UID, UUID, URIRef, str, int, bytes):
    if datatype in (int, bytes):

        def _lexicalizer(x):
            return str(UID(x))

    else:
        _lexicalizer = None
    term.bind(
        UID.iri,
        datatype,
        lexicalizer=_lexicalizer,
        constructor=None,
        datatype_specific=True,
    )

ENTITY_IRI_PREFIX = "https://www.simphony-osp.eu/entity#"

# --- RDF TO PYTHON --- #


def _get_all_python_subclasses(cls):
    return set(cls.__subclasses__()) | {
        sc
        for c in cls.__subclasses__()
        for sc in _get_all_python_subclasses(c)
    }


# OWL data types
#  See [Datatype Maps](https://www.w3.org/TR/owl2-syntax/#Datatype_Maps) on
#  the OWL specification.
#  OWL_TO_PYTHON gathers data types that are not bound already to RDFLib terms.
OWL_TO_PYTHON = {
    URIRef("http://www.w3.org/2002/07/owl#real"): float,
    # ↑ Not defined by RDFLib.
    URIRef("http://www.w3.org/2002/07/owl#rational"): Fraction,
    # ↑ Not defined by RDFLib.
    # XSD.Name: ?, (TODO: not supported)
    # ↑ Not defined by RDFLib.
    # XSD.NCName: ?, (TODO: not yet supported)
    # ↑ Not defined by RDFLib.
    # XSD.NMTOKEN: ?, (TODO: not yet supported)
    # ↑ Not defined by RDFLib.
    # XSD.base64Binary: ?, (TODO: not yet supported)
    # ↑ Not defined by RDFLib.
    # XSD.dateTimeStamp: ?, (TODO: not yet supported)
    # ↑ ¿Is it defined by RDFLib?
    # RDF.XMLLiteral: ?, (TODO: not yet supported)
    # ↑ ¿Is it defined by RDFLib?
}
#  OWL_TO_PYTHON_DEFINED_RDFLIB gathers data types that were bound to RDFLib
#  terms already by the RDFLib developers.
OWL_TO_PYTHON_DEFINED_RDFLIB = {
    XSD.decimal: Decimal,  # -> Defined already by RDFLib.
    XSD.integer: int,  # -> Defined already by RDFLib.
    XSD.nonNegativeInteger: int,  # -> Defined already by RDFLib.
    XSD.nonPositiveInteger: int,  # -> Defined already by RDFLib.
    XSD.positiveInteger: int,  # -> Defined already by RDFLib.
    XSD.negativeInteger: int,  # -> Defined already by RDFLib.
    XSD.long: int,  # -> Defined already by RDFLib.
    XSD.int: int,  # -> Defined already by RDFLib.
    XSD.short: int,  # -> Defined already by RDFLib.
    XSD.byte: int,  # -> Defined already by RDFLib.
    XSD.unsignedLong: int,  # -> Defined already by RDFLib.
    XSD.unsignedInt: int,  # -> Defined already by RDFLib.
    XSD.unsignedShort: int,  # -> Defined already by RDFLib.
    XSD.unsignedByte: int,  # -> Defined already by RDFLib.
    XSD.double: float,  # -> Defined already by RDFLib.
    XSD.float: float,  # -> Defined already by RDFLib.
    XSD.string: str,  # -> Defined already by RDFLib.
    XSD.normalizedString: str,  # -> Defined already by RDFLib.
    XSD.token: str,  # -> Defined already by RDFLib.
    XSD.boolean: bool,  # -> Defined already by RDFLib.
    XSD.hexBinary: bytes,  # -> Defined already by RDFLib.
    XSD.anyURI: str,  # -> Defined already by RDFLib.
    XSD.dateTime: datetime,  # -> Defined already by RDFLib.
}
OWL_TO_PYTHON.update(OWL_TO_PYTHON_DEFINED_RDFLIB)
OWL_COMPATIBLE_TYPES = tuple(OWL_TO_PYTHON.values())
OWLCompatibleType = Union[OWL_COMPATIBLE_TYPES]
# Custom STATIC data types (fixed URI).
CUSTOM_TO_PYTHON = {
    cls.iri: cls for cls in _get_all_python_subclasses(CustomDataType)
}
CUSTOM_COMPATIBLE_TYPES = tuple(CUSTOM_TO_PYTHON.values())
CustomCompatibleType = (
    Union[CUSTOM_COMPATIBLE_TYPES] if CUSTOM_COMPATIBLE_TYPES else None
)
# All RDF data types compatible with SimPhoNy, automatically generated from
#  the previous mappings.
RDF_TO_PYTHON = {RDFS.Literal: str}
RDF_TO_PYTHON.update(OWL_TO_PYTHON)
RDF_TO_PYTHON.update(CUSTOM_TO_PYTHON)
#  Bind all the types to RDFLib.
for iri, data_type in RDF_TO_PYTHON.items():
    # Skip custom data types, which where already bound under their definition.
    # Skip also data types already bound by RDFLib.
    if iri in set(CUSTOM_TO_PYTHON) | set(OWL_TO_PYTHON_DEFINED_RDFLIB):
        continue
    term.bind(iri, data_type)
# Define what are the Python types compatible with RDF.
ATTRIBUTE_VALUE_TYPES = tuple(x for x in RDF_TO_PYTHON.values())


def rdf_to_python(value: Any, rdf_data_type: URIRef) -> Any:
    """Changes the type of a Python object to match an RDF datatype.

    Converts a Python object into another Python object whose type is
    compatible with the specified data type

    Args:
        value: The Python object to be transformed.
        rdf_data_type: The RDF data type that the resulting object needs to
            be compatible with.

    Returns:
        A Python object compatible with `rdf_data_type`.
    """
    # Converting the literal to a string  or calling Literal twice seems
    #  redundant, but is intentional.
    #
    #  One would expect rdflib to convert the literal to the adequate
    #  datatype by calling 'value.toPython()'. However, this is not always
    #  true. Two cases have to be considered:
    #   - The literal has been created from an arbitrary Python object. Then
    #     calling `toPython` returns the original Python object, no matter
    #     what datatype was specified when creating it.
    #   - The literal has been created from a string. Then calling `toPython`
    #     invokes the RDFLib constructor, spawning a Python object of the
    #     adequate datatype.
    if isinstance(value, Literal):
        # Here we convert the received literal to a string so that RDFLib
        # first calls the lexicalizer on it. In such a way the new literal
        # is created from a string, and the constructor is invoked when
        # calling `toPython`.
        result = Literal(
            str(value), datatype=rdf_data_type, lang=value.language
        ).toPython()
    else:
        # When an arbitrary python object is received instead, first we
        # create a literal with the correct data type, and then perform the
        # same action as before: call the lexicalizer on such literal so
        # that the new one is created from a string.
        result = Literal(value, datatype=rdf_data_type)
        result = Literal(str(result), datatype=rdf_data_type).toPython()
    return result


# --- Various type hints and type hint aliases --- #

# RDF type hints
Pattern = Tuple[Optional[Node], Optional[Node], Optional[Node]]
SimplePattern = Tuple[
    Optional[Union[URIRef, Literal]],
    Optional[Union[URIRef, Literal]],
    Optional[Union[URIRef, Literal]],
]
Triple = Tuple[Node, Node, Node]
SimpleTriple = Tuple[
    Union[URIRef, Literal], Union[URIRef, Literal], Union[URIRef, Literal]
]

# Predicates
OntologyPredicate: TypeAlias = Union[
    "OntologyAnnotation",
    "OntologyAttribute",
    "OntologyRelationship",
]

# Predicate targets
AttributeValue = Union[tuple(value for value in RDF_TO_PYTHON.values())]
AnnotationValue: TypeAlias = Union[
    "OntologyAnnotation",
    "OntologyAttribute",
    "OntologyClass",
    "OntologyIndividual",
    "OntologyRelationship",
    AttributeValue,
    URIRef,
    Literal,
]
RelationshipValue: TypeAlias = "OntologyIndividual"
PredicateValue: TypeAlias = Union[
    "OntologyIndividual", AttributeValue, AnnotationValue
]
