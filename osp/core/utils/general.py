"""A collection of utility method for osp-core.

These are potentially useful for every user of SimPhoNy.
"""

import io
import itertools
import json
import logging
import pathlib
from typing import List, Optional, TextIO, Union
from uuid import UUID

import requests
from rdflib import OWL, RDF, RDFS, Graph, Literal, URIRef
from rdflib import __version__ as rdflib_version
from rdflib.parser import Parser as RDFLib_Parser
from rdflib.plugin import get as get_plugin
from rdflib.serializer import Serializer as RDFLib_Serializer
from rdflib.util import guess_format

if rdflib_version >= "6":
    from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf
else:
    import warnings

    def _silent_warn(*args, **kwargs) -> None:
        """Function to replace `warnings.warn`, silences forced warnings."""
        pass

    warn = warnings.warn
    warnings.warn = _silent_warn
    from rdflib_jsonld.parser import to_rdf as json_to_rdf

    warnings.warn = warn

from osp.core.namespaces import cuba
from osp.core.ontology.cuba import rdflib_cuba
from osp.core.ontology.datatypes import convert_from
from osp.core.ontology.relationship import OntologyRelationship

CUDS_IRI_PREFIX = "http://www.osp-core.com/cuds#"
logger = logging.getLogger(__name__)

# Private utilities (not user-facing and only used in this same file).


def _get_rdf_graph(
    session=None, skip_custom_datatypes=False, skip_ontology=True
):
    """Get the RDF Graph from a session.

    If no session is given, the core session will be used.

    Args:
        session (Session, optional): The session to compute the RDF Graph of.
            Defaults to None.
        skip_custom_datatypes (bool): Whether triples concerining custom
            datatypes should be skipped in export.
        skip_ontology (bool): Whether to have the ontology triples in the
            result graph.

    Returns:
        Graph: The resulting rdf Graph
    """
    from osp.core.session.session import Session

    if session is not None:
        if not isinstance(session, Session):
            raise TypeError(
                f"Invalid argument: {session}."
                f"Function can only be called on (sub)classes of {Session}."
                ""
            )
    from osp.core.cuds import Cuds
    from osp.core.ontology.namespace_registry import namespace_registry

    session = session or Cuds._session
    result = session._get_full_graph()
    if not skip_ontology:
        result = result | namespace_registry._graph
        # The union includes namespace bindings.
    else:
        # Still bind the installed namespaces
        for prefix, iri in namespace_registry._graph.namespaces():
            result.bind(prefix, iri)
    if skip_custom_datatypes:
        return result - get_custom_datatype_triples()
    return result


def _serialize_rdf_graph(
    format="xml",
    session=None,
    skip_custom_datatypes=False,
    skip_ontology=True,
    skip_wrapper=True,
):
    """Serialize an RDF graph and take care of custom data types."""
    from osp.core.session.core_session import CoreSession

    graph = _get_rdf_graph(session, skip_custom_datatypes, skip_ontology)
    result = Graph()
    for s, p, o in graph:
        if isinstance(o, Literal):
            o = Literal(
                convert_from(o.toPython(), o.datatype),
                datatype=o.datatype,
                lang=o.language,
            )
        if (
            not session
            or type(session) is CoreSession
            or not skip_wrapper
            or iri_from_uid(session.root) not in {s, o}
        ):
            result.add((s, p, o))
    for prefix, iri in graph.namespaces():
        result.bind(prefix, iri)
    return result.serialize(format=format, encoding="UTF-8").decode("UTF-8")


def _serialize_cuds_object_json(
    cuds_object,
    rel=cuba.activeRelationship,
    max_depth=float("inf"),
    json_dumps=True,
):
    """Serialize a cuds objects and all of its contents recursively.

    Args:
        cuds_object (Cuds): The cuds object to serialize
        rel (OntologyRelationship, optional): The relationships to follow when
            serializing recursively. Defaults to cuba.activeRelationship.
        max_depth (int, optional): The maximum recursion depth.
            Defaults to float("inf").
        json_dumps (bool, optional): Whether to dump it to the registry.
            Defaults to True.

    Returns:
        Union[str, List]: The serialized cuds object.
    """
    from osp.core.session.transport.transport_utils import serializable
    from osp.core.utils.simple_search import find_cuds_object

    cuds_objects = find_cuds_object(
        criterion=lambda _: True,
        root=cuds_object,
        rel=rel,
        find_all=True,
        max_depth=max_depth,
    )
    result = serializable(cuds_objects, partition_cuds=False, mark_first=True)
    if json_dumps:
        return json.dumps(result)
    return result


def _serialize_cuds_object_triples(
    cuds_object,
    rel=cuba.activeRelationship,
    max_depth=float("inf"),
    format: str = "ttl",
):
    """Serialize a CUDS object as triples.

    Args:
        cuds_object (Cuds): the cuds object to serialize.
        rel (OntologyRelationship): the ontology relationship to use as
            containment relationship.
        max_depth (float): the maximum depth to search for children CUDS
            objects.
        format (str): the format of the serialized triples.

    Returns:
        str: The CUDS object serialized as a RDF file.
    """
    from osp.core.ontology.namespace_registry import namespace_registry
    from osp.core.utils.simple_search import find_cuds_object

    cuds_objects = find_cuds_object(
        criterion=lambda _: True,
        root=cuds_object,
        rel=rel,
        find_all=True,
        max_depth=max_depth,
    )
    graph = Graph()
    graph.add(
        (rdflib_cuba._serialization, RDF.first, Literal(str(cuds_object.uid)))
    )
    for prefix, iri in namespace_registry._graph.namespaces():
        graph.bind(prefix, iri)
    for s, p, o in itertools.chain(
        *(cuds.get_triples() for cuds in cuds_objects)
    ):
        if isinstance(o, Literal):
            o = Literal(
                convert_from(o.toPython(), o.datatype),
                datatype=o.datatype,
                lang=o.language,
            )
        graph.add((s, p, o))
    return graph.serialize(format=format, encoding="UTF-8").decode("UTF-8")


def _serialize_session_json(session, json_dumps=True):
    """Serialize a session in application/ld+json format.

    Args:
        session (Session): The session to serialize.
        json_dumps (bool, optional): Whether to dump it to the registry.
            Defaults to True.

    Returns:
        Union[str, List]: The serialized session.
    """
    from osp.core.session.transport.transport_utils import serializable

    cuds_objects = list(
        cuds
        for cuds in session._registry.values()
        if not cuds.is_a(cuba.Wrapper)
    )
    result = serializable(cuds_objects, partition_cuds=False, mark_first=False)
    if json_dumps:
        return json.dumps(result)
    return result


def _deserialize_cuds_object(json_doc, session=None, buffer_context=None):
    """Deserialize the given json objects (to CUDS).

    Will add the CUDS objects to the buffers.

    Args:
        json_doc (Union[str, dict, List[dict]]): the json document to load.
            Either string or already loaded json object.
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.
        buffer_context (BufferContext): Whether to add the objects to the
            buffers of the user or the engine. Default is equivalent of
            the user creating the CUDS objects by hand.

    Returns:
        Cuds: The deserialized Cuds.
    """
    from osp.core.cuds import Cuds
    from osp.core.ontology.cuba import rdflib_cuba
    from osp.core.session.buffers import BufferContext
    from osp.core.session.transport.transport_utils import import_rdf

    if isinstance(json_doc, str):
        json_doc = json.loads(json_doc)
    session = session or Cuds._session
    buffer_context = buffer_context or BufferContext.USER
    g = json_to_rdf(json_doc, Graph())
    # only return first (when a cuds instead of a session was exported)
    first = g.value(rdflib_cuba._serialization, RDF.first)
    if first:  # return the element marked as first later
        try:
            first = UUID(hex=first)
        except ValueError:
            first = URIRef(first)
        g.remove((rdflib_cuba._serialization, RDF.first, None))
    deserialized = import_rdf(
        graph=g,
        session=session,
        buffer_context=buffer_context,
        return_uid=first,
    )
    return deserialized


def _import_rdf_file(path, format="xml", session=None, buffer_context=None):
    """Import rdf from file.

    Args:
        path (Union[str, TextIO]): Path of the rdf file to import or file-like
            object containing the rdf data.
        format (str, optional): The file format of the file. Defaults to "xml".
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.
        buffer_context (BufferContext, optional): Whether to add the objects
            to the buffers of the user or the engine. Default is equivalent of
            the user creating the CUDS objects by hand.. Defaults to None.
    """
    from osp.core.cuds import Cuds
    from osp.core.session.buffers import BufferContext
    from osp.core.session.transport.transport_utils import import_rdf

    g = Graph()
    g.parse(path, format=format)
    test_triples = [
        (None, RDF.type, OWL.Class),
        (None, RDF.type, OWL.DatatypeProperty),
        (None, RDF.type, OWL.ObjectProperty),
    ]
    if any(t in g for t in test_triples):
        raise ValueError(
            "Data contains class or property definitions. "
            "Please install ontologies using pico and use the "
            "rdf import only for individuals!"
        )
    onto_iri = g.value(None, RDF.type, OWL.Ontology)
    if onto_iri:
        g.remove((onto_iri, None, None))
    # only return first (when a cuds instead of a session was exported)
    first = g.value(rdflib_cuba._serialization, RDF.first)
    if first:  # return the element marked as first later
        try:
            first = UUID(hex=first)
        except ValueError:
            first = URIRef(first)
        g.remove((rdflib_cuba._serialization, RDF.first, None))
    session = session or Cuds._session
    buffer_context = buffer_context or BufferContext.USER
    deserialized = import_rdf(
        graph=g,
        session=session,
        buffer_context=buffer_context,
        return_uid=first,
    )
    return deserialized


# Internal utilities (not user-facing).


def iri_from_uid(uid: Union[UUID, URIRef]) -> URIRef:
    """Transform an uid to an IRI.

    Args:
        uid: The UUID to transform.

    Returns:
        The IRI of the CUDS object with the given UUID.
    """
    if type(uid) is UUID:
        return URIRef(CUDS_IRI_PREFIX + str(uid))
    else:
        return uid


def uid_from_iri(iri):
    """Transform an IRI to an uid.

    Args:
        iri (URIRef): The IRI to transform.

    Returns:
        URIRef: The IRI of the CUDS object with the given uid.
    """
    if iri.startswith(CUDS_IRI_PREFIX):
        try:
            return UUID(hex=str(iri)[len(CUDS_IRI_PREFIX) :])
        except ValueError as e:
            raise ValueError(f"Unable to transform {iri} to uid.") from e
    else:
        return iri


def get_custom_datatypes():
    """Get the set of all custom datatypes used in the ontology.

    Custom datatypes are non standard ones, defined in the CUBA namespace.

    Returns:
        Set[IRI]: The set of IRI of custom datatypes.
    """
    from osp.core.ontology.cuba import rdflib_cuba
    from osp.core.ontology.namespace_registry import namespace_registry

    pattern = (None, RDF.type, RDFS.Datatype)
    result = set()
    for s, p, o in namespace_registry._graph.triples(pattern):
        if s in rdflib_cuba:
            result.add(s)
    return result


def get_custom_datatype_triples():
    """Get the set of triples in the ontology that include custom datatypes.

    Custom datatypes are non standard ones, defined in the CUBA namespace.

    Returns:
        Graph: A graph containing all the triples concerning custom
            datatypes.
    """
    custom_datatypes = get_custom_datatypes()
    from osp.core.ontology.namespace_registry import namespace_registry

    result = Graph()
    for d in custom_datatypes:
        result.add((d, RDF.type, RDFS.Datatype))
        pattern = (None, RDFS.range, d)
        for s, p, o in namespace_registry._graph.triples(pattern):
            result.add((s, p, o))
    return result


# Public utilities (user-facing).


def branch(cuds_object, *args, rel=None):
    """Like Cuds.add(), but returns the element you add to.

    This makes it easier to create large CUDS structures.

    Args:
        cuds_object (Cuds): the object to add to.
        args (Cuds): object(s) to add
        rel (OntologyRelationship): class of the relationship between the
            objects.

    Raises:
        ValueError: adding an element already there.

    Returns:
        Cuds: The first argument.
    """
    cuds_object.add(*args, rel=rel)
    return cuds_object


def get_relationships_between(subj, obj):
    """Get the set of relationships between two cuds objects.

    Args:
        subj (Cuds): The subject
        obj (Cuds): The object

    Returns:
        Set[OntologyRelationship]: The set of relationships between subject
            and object.
    """
    result = set()
    for rel, obj_uids in subj._neighbors.items():
        if obj.uid in obj_uids:
            result.add(rel)
    return result


def delete_cuds_object_recursively(
    cuds_object, rel=cuba.activeRelationship, max_depth=float("inf")
):
    """Delete a cuds object  and all the object inside of the container of it.

    Args:
        cuds_object (Cuds): The CUDS object to recursively delete.
        rel (OntologyRelationship, optional): The relationship used for
            traversal. Defaults to cuba.activeRelationship.
        max_depth (int, optional):The maximum depth of the recursion.
            Defaults to float("inf"). Defaults to float("inf").
    """
    from osp.core.utils.simple_search import find_cuds_object

    cuds_objects = find_cuds_object(
        criterion=lambda x: True,
        root=cuds_object,
        rel=rel,
        find_all=True,
        max_depth=max_depth,
    )
    for obj in cuds_objects:
        obj.session.delete_cuds_object(obj)


def remove_cuds_object(cuds_object):
    """Remove a cuds_object from the data structure.

    Removes the relationships to all neighbors.
    To delete it from the registry you must call the
    sessions prune method afterwards.

    Args:
        cuds_object (Cuds): The cuds_object to remove.
    """
    # Method does not allow deletion of the root element of a container
    for elem in cuds_object.iter(rel=cuba.relationship):
        cuds_object.remove(elem.uid, rel=cuba.relationship)


def import_cuds(
    path_or_filelike: Union[str, TextIO, dict, List[dict]],
    session: Optional = None,
    format: str = None,
):
    """Imports CUDS in various formats (see the `format` argument).

    Args:
        path_or_filelike (Union[str, TextIO], optional): either,
            (str) the path of a file to import;
            (Union[List[dict], dict]) a dictionary representing the contents of
             a json file;
            (TextIO) any file-like object  (in string mode) that provides a
            `read()` method. Note that it is possible to get such an object
            from any `str` object using the python standard library. For
            example, given the `str` object `string`, `import io;
            filelike = io.StringIO(string)` would create such an object.
            If not format is specified, it will be guessed.
        session (Session): the session in which the imported data will be
            stored.
        format (str, optional): the format of the content to import. The
            supported formats are `json` and the ones supported by RDFLib. See
            `https://rdflib.readthedocs.io/en/latest/plugin_parsers.html`.
            If no format is specified, then it will be guessed. Note that in
            some specific cases, the guess may be wrong. In such cases, try
            again specifying the format.

    Returns (List[Cuds]): a list of cuds objects.
    """
    # Check the validity of the requested format and raise useful exceptions.
    if format is not None and format not in ("json", "application/ld+json"):
        try:
            get_plugin(format, RDFLib_Parser)
        except AttributeError as e:
            if "/" not in format:
                raise ValueError(
                    f"Unsupported format {format}. The supported formats are "
                    f"`json` and the ones supported by RDFLib "
                    f"`https://rdflib.readthedocs.io/en/latest"
                    f"/plugin_parsers.html`."
                ) from e
            else:
                raise ValueError(
                    f"Unsupported mime-type {format}. The supported mime-types"
                    f" are `application/ld+json` and the ones supported by "
                    f"RDFLib. Unfortunately, the latter are not documented, "
                    f"but can be checked directly on its source code "
                    f"`https://github.com/RDFLib/rdflib/blob/master"
                    f"/rdflib/plugin.py`. Look for lines of the form "
                    f'`register(".*", Parser, ".*", ".*")`.'
                ) from e

    # Guess and/or validate the specified format.
    if isinstance(path_or_filelike, (dict, list)):  # JSON document.
        if not (format is None or format in ("json", "application/ld+json")):
            raise ValueError(
                f"The CUDS objects to be imported do not match "
                f"the specified format: {format}."
            )
        contents = path_or_filelike
        format = "application/ld+json"
    else:  # Path to a file or file-like object.
        # Read the contents of the object.
        if isinstance(path_or_filelike, str):  # Path.
            if not pathlib.Path(path_or_filelike).is_file():
                raise ValueError(
                    f"{path_or_filelike} is not a file or does " f"not exist."
                )
            with open(path_or_filelike, "r") as file:
                contents = file.read()
        else:  # File-like object.
            if "read" not in path_or_filelike.__dir__():
                raise TypeError(
                    f"{path_or_filelike} is neither a path"
                    f"or a file-like object."
                )
            contents = path_or_filelike.read()

        # Guess or validate the format.
        if format is None or format in ("json", "application/ld+json"):
            try:
                contents = json.loads(contents)
                format = "application/ld+json"
            except ValueError as e:
                # It is not json, but json format was specified. Raise
                # ValueError.
                if format in ("json", "application/ld+json"):
                    raise ValueError(
                        f"The CUDS objects to be imported do not match "
                        f"the specified format: {format}."
                    ) from e
        if format is None:
            # Let RDFLib guess (it can only guess for files)
            if isinstance(path_or_filelike, str):
                if isinstance(path_or_filelike, str):
                    format = guess_format(path_or_filelike)
            else:
                raise ValueError(
                    "Could not guess the file format. Please"
                    'specify it using the "format" keyword '
                    "argument."
                )

    # Import the contents.
    from osp.core.cuds import Cuds

    session = session or Cuds._session
    if format == "application/ld+json":
        results = _deserialize_cuds_object(
            contents, session=session, buffer_context=None
        )
    else:
        results = _import_rdf_file(
            io.StringIO(contents),
            format=format,
            session=session,
            buffer_context=None,
        )
    return results


def export_cuds(
    cuds_or_session: Optional = None,
    file: Optional[Union[str, TextIO]] = None,
    format: str = "text/turtle",
    rel: OntologyRelationship = cuba.activeRelationship,
    max_depth: float = float("inf"),
) -> Union[str, None]:
    """Exports CUDS in a variety of formats (see the `format` argument).

    Args:
        cuds_or_session (Union[Cuds, Session], optional): the
            (Cuds) CUDS object to export, or
            (Session) a session to serialize all of its CUDS objects.
            If no item is specified, then the current session is exported.
        file (str, optional): either,
            (str) a path, to save the CUDS objects or,
            (TextIO) any file-like object (in string mode) that provides a
            `write()` method. If this argument is not specified, a string with
            the results will be returned instead.
        format(str): the target format. Defaults to triples in turtle syntax.
        rel (OntologyRelationship): the ontology relationship to use as
            containment relationship when exporting CUDS.
        max_depth (float): maximum depth to search for children CUDS.
    """
    # Choose default session if not specified.
    from osp.core.cuds import Cuds
    from osp.core.session.session import Session

    if cuds_or_session is None:
        cuds_or_session = Cuds._session

    # Check the validity of the requested format and raise useful exceptions.
    if format not in ("json", "application/ld+json"):
        try:
            get_plugin(format, RDFLib_Serializer)
        except AttributeError as e:
            if "/" not in format:
                raise ValueError(
                    f"Unsupported format {format}. The supported formats are "
                    f"`json` and the ones supported by RDFLib "
                    f"`https://rdflib.readthedocs.io/en/latest"
                    f"/plugin_serializers.html`."
                ) from e
            else:
                raise ValueError(
                    f"Unsupported mime-type {format}. The supported mime-types"
                    f" are `application/ld+json`and the ones supported by "
                    f"RDFLib. Unfortunately, the latter are not documented, "
                    f"but can be checked directly on its source code "
                    f"`https://github.com/RDFLib/rdflib/blob/master"
                    f"/rdflib/plugin.py`. Look for lines of the form "
                    f'`register(".*", Serializer, ".*", ".*")`.'
                ) from e

    if isinstance(cuds_or_session, Cuds):
        if format in ("json", "application/ld+json"):
            result = _serialize_cuds_object_json(
                cuds_or_session, rel=rel, max_depth=max_depth, json_dumps=True
            )
        else:
            result = _serialize_cuds_object_triples(
                cuds_or_session, rel=rel, max_depth=max_depth, format=format
            )
    elif isinstance(cuds_or_session, Session):
        if format in ("json", "application/ld+json"):
            result = _serialize_session_json(cuds_or_session, json_dumps=True)
        else:
            result = _serialize_rdf_graph(
                format=format,
                session=cuds_or_session,
                skip_custom_datatypes=False,
                skip_ontology=True,
                skip_wrapper=True,
            )
    else:
        raise ValueError(
            "Specify either a CUDS object or a session to " "be exported."
        )

    if file:
        if isinstance(file, str):  # Path
            if pathlib.Path(file).is_dir():
                raise ValueError(f"{file} is a directory.")
            else:
                with open(file, "w+") as file_handle:
                    file_handle.write(result)
        else:  # File-like object
            if "write" not in file.__dir__():
                raise TypeError(
                    f"{file} is neither a path" f"or a file-like object."
                )
            else:
                file.write(result)
    else:
        return result


def post(
    url, cuds_object, rel=cuba.activeRelationship, max_depth=float("inf")
):
    """Will send the given CUDS object to the given URL.

    Will also send the CUDS object in the container recursively.

    Args:
        url (string): The URL to send the CUDS object to
        cuds_object (Cuds): The CUDS to send
        max_depth (int, optional): The maximum depth to send CUDS objects
            recursively. Defaults to float("inf").

    Returns:
        Server response
    """
    serialized = _serialize_cuds_object_json(
        cuds_object, max_depth=max_depth, rel=rel
    )
    return requests.post(
        url=url,
        data=serialized,
        headers={"content_type": "application/ld+json"},
    )


def sparql(query_string: str, session: Optional = None):
    """Performs a SPARQL query on a session (if supported by the session).

    Args:
        query_string (str): A string with the SPARQL query to perform.
        session (Session, optional): The session on which the SPARQL query
            will be performed. If no session is specified, then the current
            default session is used. This means that, when no session is
            specified, inside session `with` statements, the query will be
            performed on the session associated with such statement, while
            outside, it will be performed on the OSP-core default session,
            the core session.

    Returns:
        SparqlResult: A SparqlResult object, which can be iterated to obtain
            the output rows. Then for each `row`, the value for each query
            variable can be retrieved as follows: `row['variable']`.

    Raises:
        NotImplementedError: when the session does not support SPARQL queries.
    """
    from osp.core.cuds import Cuds

    session = session or Cuds._session
    try:
        return session.sparql(query_string)
    except AttributeError or NotImplementedError:
        raise NotImplementedError(
            f"The session {session} does not support" f" SPARQL queries."
        )
