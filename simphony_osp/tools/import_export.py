"""Tools for importing and exporting data."""
from __future__ import annotations

import io
import json
import pathlib
from itertools import chain
from typing import Iterable, List, Optional, Set, TextIO, Union

from rdflib import OWL, RDF, XSD, Graph, Literal, URIRef
from rdflib.parser import Parser as RDFLib_Parser
from rdflib.plugin import get as get_plugin
from rdflib.serializer import Serializer as RDFLib_Serializer
from rdflib.term import Identifier
from rdflib.util import guess_format

from simphony_osp.ontology import OntologyIndividual
from simphony_osp.session.session import Session
from simphony_osp.utils.simphony_namespace import simphony_namespace

__all__ = ["export_file", "import_file"]


def import_file(
    path_or_filelike: Union[str, TextIO, dict, List[dict]],
    session: Optional[Session] = None,
    format: str = None,
    all_triples: bool = False,
) -> Union[OntologyIndividual, Set[OntologyIndividual]]:
    """Imports ontology individuals from a file and load them into a session.

    Note: If you are reading the SimPhoNy documentation API Reference, it
    is likely that you cannot read this docstring. As a workaround, click
    the `source` button to read it in its raw form.

    Args:
        path_or_filelike: either,
            (str) the path of a file to import;
            (Union[List[dict], dict]) a dictionary representing the contents of
             a json file;
            (TextIO) any file-like object  (in string mode) that provides a
            `read()` method. Note that it is possible to get such an object
            from any `str` object using the python standard library. For
            example, given the `str` object `string`, `import io;
            filelike = io.StringIO(string)` would create such an object.
            If not format is specified, it will be guessed.
        session: the session in which the imported data will be
            stored.
        format: the format of the content to import. The supported formats
            are the ones supported by RDFLib. See
            `https://rdflib.readthedocs.io/en/latest/plugin_parsers.html`.
            If no format is specified, then it will be guessed. Note that in
            some specific cases, the guess may be wrong. In such cases, try
            again specifying the format.
        all_triples: When an RDF triple has an ontology relationship as
            predicate, SimPhoNy checks that both the subject and the object
            of such triple refer to a valid ontology individual, that is, that
            an additional triple defining their types exist. When this is not
            the case, SimPhoNy omits the triple. In some use cases, importing
            those triples may be necessary. Change the value of this argument
            to `True` to import them.

    Returns:
        A set with the imported ontology individuals. If an individual was
        defined as the "main" one using the SimPhoNy ontology, then only the
        main individual is returned instead.
    """
    # Check that the requested format is supported and raise useful exceptions.
    if format is not None:
        try:
            get_plugin(format, RDFLib_Parser)
        except AttributeError as e:
            if "/" not in format:
                raise ValueError(
                    f"Unsupported format {format}. The supported formats are "
                    f"the ones supported by RDFLib "
                    f"`https://rdflib.readthedocs.io/en/latest"
                    f"/plugin_parsers.html`."
                ) from e
            else:
                raise ValueError(
                    f"Unsupported mime-type {format}. The supported mime-types"
                    f" are the ones supported by RDFLib. Unfortunately, the "
                    f"latter are not documented, but can be checked directly "
                    f"on its source code "
                    f"`https://github.com/RDFLib/rdflib/blob/master"
                    f"/rdflib/plugin.py`. Look for lines of the form "
                    f'`register(".*", Parser, ".*", ".*")`.'
                ) from e

    # Guess and/or validate the specified format.
    if isinstance(path_or_filelike, (dict, list)):  # JSON document
        if not (
            format is None or format in ("json-ld", "application/ld+json")
        ):
            raise ValueError(
                f"The file to be imported do not match the specified format: "
                f"{format}."
            )
        contents = json.dumps(path_or_filelike)
    else:  # Path to a file or file-like object.
        # Read the contents of the object.
        if isinstance(path_or_filelike, str):  # Path.
            if not pathlib.Path(path_or_filelike).is_file():
                raise ValueError(
                    f"{path_or_filelike} is not a file or does not exist."
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
        if format is None:
            # Let RDFLib guess (it can only guess for files)
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

    buffer_session = Session()
    buffer_session.graph.parse(io.StringIO(contents), format=format)
    buffer_session.graph.remove((None, RDF.type, OWL.NamedIndividual))

    individuals = set(
        individual
        for individual in buffer_session
        if isinstance(individual, OntologyIndividual)
    )
    session.add(
        individuals, exists_ok=True, merge=False, all_triples=all_triples
    )

    main = next(
        iter(
            buffer_session.graph.subjects(
                simphony_namespace.main, Literal("true", datatype=XSD.boolean)
            )
        ),
        None,
    )
    if main:
        result = session.from_identifier_typed(main, typing=OntologyIndividual)
    else:
        result = set(
            session.from_identifier_typed(
                individual.identifier, typing=OntologyIndividual
            )
            for individual in individuals
        )

    return result


def export_file(
    individuals_or_session: Optional[
        Union[OntologyIndividual, Iterable[OntologyIndividual], Session]
    ] = None,
    file: Optional[Union[str, TextIO]] = None,
    main: Optional[Union[str, Identifier, OntologyIndividual]] = None,
    format: str = "text/turtle",
    all_triples: bool = False,
) -> Union[str, None]:
    """Exports ontology individuals to a variety of formats.

    Note: If you are reading the SimPhoNy documentation API Reference, it
    is likely that you cannot read this docstring. As a workaround, click
    the `source` button to read it in its raw form.

    Args:
        individuals_or_session:
            (OntologyIndividual) A single ontology individual to export, or
            (Iterable[OntologyIndividual]) an iterable of ontology individuals,
            (Session) a session to serialize all of its ontology individuals.
            If `None` is specified, then the current session is exported.
        file: either,
            (str) a path, to save the ontology individuals to, or
            (TextIO) any file-like object (in string mode) that provides a
            `write()` method. If this argument is not specified, a string with
            the results will be returned instead.
        main: the identifier of an ontology individual to be marked as the
            "main" individual using the SimPhoNy ontology.
        format: the target format. Defaults to triples in turtle syntax.
        all_triples: When an RDF triple has an ontology relationship as
            predicate, SimPhoNy checks that both the subject and the object
            of such triple refer to a valid ontology individual, that is, that
            an additional triple defining their types exist. When this is not
            the case, SimPhoNy omits the triple (unless the whole session is
            being exported). In some use cases, exporting those triples may be
            necessary. Change the value of this argument to `True` to export
            them.

    Returns:
        The contents of the exported file as a string (if no `file` argument
        was provided), or nothing.
    """
    # Choose default session if not specified.
    individuals_or_session = (
        individuals_or_session or Session.get_default_session()
    )

    # Check the validity of the requested format and raise useful exceptions.
    try:
        get_plugin(format, RDFLib_Serializer)
    except AttributeError as e:
        if "/" not in format:
            raise ValueError(
                f"Unsupported format {format}. The supported formats are "
                f"the ones supported by RDFLib "
                f"`https://rdflib.readthedocs.io/en/latest"
                f"/plugin_serializers.html`."
            ) from e
        else:
            raise ValueError(
                f"Unsupported mime-type {format}. The supported mime-types"
                f" are the ones supported by RDFLib. Unfortunately, the "
                f"latter are not documented, but can be checked directly "
                f"on its source code "
                f"`https://github.com/RDFLib/rdflib/blob/master"
                f"/rdflib/plugin.py`. Look for lines of the form "
                f'`register(".*", Parser, ".*", ".*")`.'
            ) from e

    # Compute main individual triple if applicable
    if isinstance(individuals_or_session, OntologyIndividual) and not main:
        main = individuals_or_session
    if main:
        if isinstance(main, str):
            main = URIRef(main)
        elif isinstance(main, OntologyIndividual):
            main = main.identifier
        main = (
            main,
            simphony_namespace.main,
            Literal("true", datatype=XSD.boolean),
        )

    # Export the individuals
    if isinstance(individuals_or_session, Session):
        buffer_graph = Graph()
        buffer_graph += individuals_or_session.graph
        if main:
            buffer_graph.add(main)
        for ns in individuals_or_session.namespaces:
            buffer_graph.bind(ns.name, ns.iri)
        result = buffer_graph.serialize(
            format=format, encoding="utf-8"
        ).decode("utf-8")
    else:
        if isinstance(individuals_or_session, OntologyIndividual):
            individuals_or_session = {individuals_or_session}

        buffer_session = Session()

        # Bind namespaces
        first_individual = next(iter(individuals_or_session))
        for ns in first_individual.session.namespaces:
            buffer_session.bind(ns.name, ns.iri)
        individuals_or_session = chain(
            {first_individual}, individuals_or_session
        )

        # Add individuals and main individual triple
        buffer_session.add(individuals_or_session, all_triples=all_triples)
        if main:
            buffer_session.graph.add(main)

        result = buffer_session.graph.serialize(
            format=format, encoding="utf-8"
        ).decode("utf-8")

    # Either save the result to a file or return it as a string.
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
