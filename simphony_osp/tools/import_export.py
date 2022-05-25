"""Tools for importing and exporting data."""

import io
import itertools
import json
import pathlib
from typing import List, Optional, TextIO, Union

from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal
from rdflib.graph import ReadOnlyGraphAggregate
from rdflib.parser import Parser as RDFLib_Parser
from rdflib.plugin import get as get_plugin
from rdflib.plugins.parsers.jsonld import to_rdf as json_to_rdf
from rdflib.serializer import Serializer as RDFLib_Serializer
from rdflib.util import guess_format

from simphony_osp.ontology import OntologyIndividual
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.session.wrapper import Wrapper
from simphony_osp.utils import simphony_namespace
from simphony_osp.utils.datatypes import CUSTOM_TO_PYTHON

__all__ = ["export_cuds", "import_cuds"]


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
    session = session or Session.get_default_session()
    if format == "application/ld+json":
        results = _deserialize_json(contents, session=session)
    else:
        results = _import_rdf_file(
            io.StringIO(contents), format=format, session=session
        )
    return results


def export_cuds(
    individual_or_session: Optional = None,
    file: Optional[Union[str, TextIO]] = None,
    format: str = "text/turtle",
    rel: "OntologyRelationship" = OWL.topObjectProperty,
    max_depth: float = float("inf"),
) -> Union[str, None]:
    """Exports CUDS in a variety of formats (see the `format` argument).

    Args:
        individual_or_session (Union[Cuds, Session], optional): the
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
    from simphony_osp.ontology.individual import OntologyIndividual
    from simphony_osp.session.session import Session

    individual_or_session = (
        individual_or_session or Session.get_default_session()
    )
    if isinstance(individual_or_session, Wrapper):
        individual_or_session = individual_or_session.session

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

    if isinstance(individual_or_session, OntologyIndividual):
        if format in ("json", "application/ld+json"):
            result = _serialize_individual_json(
                individual_or_session,
                rel=rel,
                max_depth=max_depth,
                json_dumps=True,
            )
        else:
            result = _serialize_individual_triples(
                individual_or_session,
                rel=rel,
                max_depth=max_depth,
                format=format,
            )
    elif isinstance(individual_or_session, Session):
        if format in ("json", "application/ld+json"):
            result = _serialize_session_json(
                individual_or_session, json_dumps=True
            )
        else:
            result = _serialize_session_triples(
                format=format,
                session=individual_or_session,
                skip_custom_datatypes=False,
                skip_ontology=True,
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


def _serialize_session_triples(
    format="xml", session=None, skip_custom_datatypes=False, skip_ontology=True
):
    """Serialize an RDF graph and take care of custom data types."""
    from simphony_osp.session.session import Session

    session = session or Session.get_default_session()

    graph = session.graph
    if not skip_ontology:
        graph = ReadOnlyGraphAggregate([graph, session.ontology.graph])
    custom_datatype_triples = (
        _get_custom_datatype_triples(session)
        if skip_custom_datatypes
        else Graph()
    )

    result = Graph()
    for s, p, o in graph:
        if isinstance(o, Literal):
            x = Literal(o.toPython(), datatype=o.datatype).toPython()
            o = Literal(x, datatype=o.datatype, lang=o.language)
        if (s, p, o) in custom_datatype_triples and skip_custom_datatypes:
            continue
        result.add((s, p, o))

    try:
        for prefix, iri in graph.namespaces():
            result.bind(prefix, iri)
    except NotImplementedError:
        pass
    return result.serialize(format=format, encoding="UTF-8").decode("UTF-8")


def _serialize_individual_json(
    individual,
    rel=OWL.topObjectProperty,
    max_depth=float("inf"),
    json_dumps=True,
):
    """Serialize a cuds objects and all of its contents recursively.

    Args:
        individual (Cuds): The cuds object to serialize
        rel (OntologyRelationship, optional): The relationships to follow when
            serializing recursively. Defaults to cuba.activeRelationship.
        max_depth (int, optional): The maximum recursion depth.
            Defaults to float("inf").
        json_dumps (bool, optional): Whether to dump it to the registry.
            Defaults to True.

    Returns:
        Union[str, List]: The serialized cuds object.
    """
    from simphony_osp.tools.search import find_cuds_object

    cuds_objects = find_cuds_object(
        criterion=lambda _: True,
        root=individual,
        rel=rel,
        find_all=True,
        max_depth=max_depth,
    )
    g = Graph()
    for triple in (t for c in cuds_objects for t in c.triples):
        g.add(triple)
    g.add(
        (
            individual.identifier,
            simphony_namespace.main,
            Literal("true", datatype=XSD.boolean),
        )
    )
    result = g.serialize(format="json-ld")
    if not json_dumps:
        return json.loads(result)
    return result


def _serialize_individual_triples(
    individual,
    rel=OWL.topObjectProperty,
    max_depth=float("inf"),
    format: str = "ttl",
):
    """Serialize a CUDS object as triples.

    Args:
        individual (Cuds): the cuds object to serialize.
        rel (OntologyRelationship): the ontology relationship to use as
            containment relationship.
        max_depth (float): the maximum depth to search for children CUDS
            objects.
        format (str): the format of the serialized triples.

    Returns:
        str: The CUDS object serialized as a RDF file.
    """
    from simphony_osp.tools.search import find_cuds_object

    individuals = find_cuds_object(
        criterion=lambda _: True,
        root=individual,
        rel=rel,
        find_all=True,
        max_depth=max_depth,
    )
    graph = Graph()
    graph.add(
        (
            individual.identifier,
            simphony_namespace.main,
            Literal("true", datatype=XSD.boolean),
        )
    )
    for namespace in individual.session.namespaces:
        graph.bind(namespace.name, namespace.iri)
    for s, p, o in itertools.chain(
        *(individual.triples for individual in individuals)
    ):
        if isinstance(o, Literal):
            x = Literal(o.toPython(), datatype=o.datatype).toPython()
            o = Literal(x, datatype=o.datatype, lang=o.language)
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
    entitites = set(session)
    g = Graph()
    for triple in (t for e in entitites for t in e.triples):
        g.add(triple)
    result = g.serialize(format="json-ld")
    if not json_dumps:
        return json.loads(result)
    return result


def _deserialize_json(json_doc, session=None):
    """Deserialize the given json objects (to CUDS).

    Will add the CUDS objects to the buffers.

    Args:
        json_doc (Union[str, dict, List[dict]]): the json document to load.
            Either string or already loaded json object.
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.

    Returns:
        Cuds: The deserialized Cuds.
    """
    from simphony_osp.session.session import Session

    if isinstance(json_doc, str):
        json_doc = json.loads(json_doc)

    temp_session = Session()
    json_to_rdf(json_doc, temp_session.graph)

    session = session or Session.get_default_session()
    results = []
    for entity in set(temp_session):
        # session.merge(entity)
        for triple in entity.triples:
            session.graph.add(triple)
        results += [session.from_identifier(entity.identifier)]

    # only return first (when a cuds instead of a session was exported)
    first = next(
        iter(
            temp_session.graph.subjects(
                simphony_namespace.main, Literal("true", datatype=XSD.boolean)
            )
        ),
        None,
    )
    if first:
        return session.from_identifier_typed(first, typing=OntologyIndividual)

    return results


def _import_rdf_file(path, format="xml", session=None):
    """Import rdf from file.

    Args:
        path (Union[str, TextIO]): Path of the rdf file to import or file-like
            object containing the rdf data.
        format (str, optional): The file format of the file. Defaults to "xml".
        session (Session, optional): The session to add the CUDS objects to.
            Defaults to the CoreSession.
    """
    temp_session = Session()
    temp_session.graph.parse(path, format=format)
    # remove OWL.NamedIndividual type statements as we do not need them
    temp_session.graph.remove((None, RDF.type, OWL.NamedIndividual))

    session = session or Session.get_default_session()
    results = []
    for entity in set(temp_session):
        # session.merge(entity)
        for triple in entity.triples:
            session.graph.add(triple)
        results += [session.from_identifier(entity.identifier)]

    # only return first (when a cuds instead of a session was exported)
    first = next(
        iter(
            temp_session.graph.subjects(
                simphony_namespace.main, Literal("true", datatype=XSD.boolean)
            )
        ),
        None,
    )
    if first:
        return session.from_identifier_typed(first, typing=OntologyIndividual)

    return results


def _get_custom_datatype_triples(session):
    """Get the set of triples in the ontology that include custom datatypes.

    Custom datatypes are non-standard ones, defined in the CUBA namespace.

    Returns:
        Graph: A graph containing all the triples concerning custom
            datatypes.
    """
    custom_datatypes = CUSTOM_TO_PYTHON.keys()
    result = Graph()
    for d in custom_datatypes:
        result.add((d, RDF.type, RDFS.Datatype))
        pattern = (None, RDFS.range, d)
        for s, p, o in session.ontology.graph.triples(pattern):
            result.add((s, p, o))
    return result
