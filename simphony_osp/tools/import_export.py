"""Tools for importing and exporting data."""
from __future__ import annotations

import io
import json
import logging
import pathlib
from itertools import chain
from typing import Iterable, List, Optional, Set, TextIO, Union

from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal, URIRef
from rdflib.parser import Parser as RDFLib_Parser
from rdflib.plugin import get as get_plugin
from rdflib.serializer import Serializer as RDFLib_Serializer
from rdflib.term import Identifier
from rdflib.util import guess_format

from simphony_osp.ontology import OntologyIndividual, OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.utils.simphony_namespace import simphony_namespace

__all__ = ["export_file", "import_file"]

logger = logging.getLogger(__name__)


def import_file(
    file: Union[str, TextIO, dict, List[dict]],
    session: Optional[Session] = None,
    format: str = None,
    all_triples: bool = False,
    all_statements: bool = False,
) -> Union[OntologyIndividual, Set[OntologyIndividual]]:
    """Imports ontology individuals from a file and load them into a session.

    Note: If you are reading the SimPhoNy documentation API Reference, it
    is likely that you cannot read this docstring. As a workaround, click
    the `source` button to read it in its raw form.

    Args:
        file: either,
            (str) the path of a file to import;
            (Union[List[dict], dict]) a dictionary representing the contents of
             a json file;
            (TextIO) any file-like object  (in string mode) that provides a
            `read()` method. Note that it is possible to get such an object
            from any `str` object using the python standard library. For
            example, given the `str` object `string`, `import io;
            filelike = io.StringIO(string)` would create such an object.
            If not format is specified, it will be guessed.
        session: the session in which the imported data will be stored.
        format: the format of the content to import. The supported formats
            are the ones supported by RDFLib. See
            `https://rdflib.readthedocs.io/en/latest/plugin_parsers.html`.
            If no format is specified, then it will be guessed. Note that in
            some specific cases, the guess may be wrong. In such cases, try
            again specifying the format.
        all_triples: By default, SimPhoNy imports only ontology individuals.
            Moreover, not all information about such individuals is imported,
            but only the details that are relevant from an ontological point
            of view: the individual's attributes, the classes it belongs to,
            and its connections to other ontology individuals that are also
            being copied at the same time.

            However, in some cases, it is necessary to keep all the information
            about an individual, even if it cannot be understood by SimPhoNy.
            Set this option to `True` to copy all RDF statements describing
            ontology individuals, that is, all RDF statements where the
            individuals are the subject.

            One example of a situation where this option is useful is
            when an individual is attached through an object property to
            another one which is not properly defined (i.e. has no type
            assigned). This situation commonly arises when using the
            `dcat:accessURL` object property.
        all_statements: SimPhoNy imports only ontology individuals by default.
            Moreover, not all information about such individuals is imported,
            but only the details that are relevant from an ontological point
            of view.

            Set this option to `True` to import all RDF statements contained in
            the file, even if they cannot be understood by SimPhoNy. Note that
            this option differs from `all_triples` because it is more general:
            the latter imports all triples where an ontology individual is the
            subject. This one imports all RDF statements, regardless of whether
            the subjects of the statements are individuals or not.

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
    if isinstance(file, (dict, list)):  # JSON document
        if not (
            format is None or format in ("json-ld", "application/ld+json")
        ):
            raise ValueError(
                f"The file to be imported do not match the specified format: "
                f"{format}."
            )
        contents = json.dumps(file)
    else:  # Path to a file or file-like object.
        # Read the contents of the object.
        if isinstance(file, str):  # Path.
            if not pathlib.Path(file).is_file():
                raise ValueError(f"{file} is not a file or does not exist.")
            with open(file, "r") as file_object:
                contents = file_object.read()
        else:  # File-like object.
            if "read" not in file.__dir__():
                raise TypeError(
                    f"{file} is neither a path" f"or a file-like object."
                )
            contents = file.read()

        # Guess or validate the format.
        if format is None:
            # Let RDFLib guess (it can only guess for files)
            if isinstance(file, str):
                format = guess_format(file)
            else:
                raise ValueError(
                    "Could not guess the file format. Please "
                    'specify it using the "format" keyword '
                    "argument."
                )

    # Import the contents of the file.
    session = session or Session.get_default_session()
    buffer_session = Session()
    buffer_session.graph.parse(io.StringIO(contents), format=format)
    individuals = set(
        individual
        for individual in buffer_session
        if isinstance(individual, OntologyIndividual)
    )
    identifiers = set(individual.identifier for individual in individuals)
    if not all_statements:
        """Import only ontology individuals from the file."""

        # Raise error/warning when individuals with undefined types are found.
        class_types = frozenset(
            {
                # owl:Class
                OWL.Class,
                RDFS.Class,
            }
        )
        other_types = frozenset(
            {
                # owl:AnnotationProperty
                OWL.AnnotationProperty,
                RDF.Property,
                # owl:DatatypeProperty
                OWL.DatatypeProperty,
                # owl:ObjectProperty
                OWL.ObjectProperty,
                # owl:Restriction
                OWL.Restriction,
            }
        )
        for s, p, o in buffer_session.graph.triples((None, None, None)):
            if p == RDF.type:
                assertional = any(
                    (o, RDF.type, entity_type) in session.ontology.graph
                    for entity_type in class_types
                )
                terminological = o in other_types | class_types
                if not (assertional or terminological):
                    text = (
                        f"Subject {s} is declared to be of type {o}, which "
                        f"does not match any class from the installed "
                        f"ontologies."
                    )
                    if not all_triples:
                        raise RuntimeError(
                            text
                            + " Set the keyword argument `all_triples` to "
                            "`True` to ignore this error."
                        )
                    else:
                        logger.warning(
                            "Accepting uninterpretable RDF statement: " + text
                        )
                elif terminological:
                    text = (
                        f"Subject {s} is declared to be of type {o}, meaning "
                        f"that it is part of the terminological knowledge of "
                        f"an ontology. Importing terminological knowledge is "
                        f"not supported by SymPhoNy. You can ignore this "
                        f"error setting the keyword argument `all_statements` "
                        f"to `True`, but it will likely lead to errors."
                    )
                    raise RuntimeError(text)
            elif not all_triples:
                try:
                    relationship = session.ontology.from_identifier_typed(
                        p, typing=OntologyRelationship
                    )
                except (KeyError, TypeError):
                    relationship = None
                if relationship and o not in identifiers:
                    raise RuntimeError(
                        f"Individual {s} is the subject of an RDF statement "
                        f"involving the ontology relationship {relationship}. "
                        f"However, SimPhoNy was unable to find an ontology"
                        f"individual with identifier {o} within the file to be"
                        f"imported. You can ignore this error setting the "
                        f"keyword argument `all_triples` to `True`."
                    )

        session.add(
            individuals, exists_ok=False, merge=False, all_triples=all_triples
        )
    else:
        """Import all triples from the file."""
        session.graph.addN(
            (s, p, o, session.graph) for s, p, o in buffer_session.graph
        )

    # Find the "main" exported item.
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
    all_statements: bool = False,
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
            (None) returns the exported file as a string, or
            (str) a path, to save the ontology individuals to, or
            (TextIO) any file-like object (in string mode) that provides a
            `write()` method. If this argument is not specified, a string with
            the results will be returned instead.
        main: the identifier of an ontology individual to be marked as the
            "main" individual using the SimPhoNy ontology.
        format: the target format. Defaults to triples in turtle syntax.
        all_triples: By default, SimPhoNy exports only ontology individuals.
            Moreover, not all information about such individuals is exported,
            but only the details that are relevant from an ontological point
            of view: the individual's attributes, the classes it belongs to,
            and its connections to other ontology individuals that are also
            being copied at the same time.

            However, in some cases, it is necessary to keep all the information
            about an individual, even if it cannot be understood by SimPhoNy.
            Set this option to `True` to export all RDF statements describing
            ontology individuals, that is, all RDF statements where the
            individuals are the subject.

            One example of a situation where this option is useful is
            when an individual is attached through an object property to
            another one which is not properly defined (i.e. has no type
            assigned). This situation commonly arises when using the
            `dcat:accessURL` object property.
        all_statements: SimPhoNy exports only ontology individuals by default.
            Moreover, not all information about such individuals is exported,
            but only the details that are relevant from an ontological point
            of view.

            Set this option to `True` to export all RDF statements contained in
            a session, even if they cannot be understood by SimPhoNy. Note that
            this option differs from `all_triples` because it is more general:
            the latter exports all triples where an ontology individual is the
            subject. This one exports all RDF statements, regardless of whether
            the subjects of the statements are individuals or not.


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
    if isinstance(individuals_or_session, OntologyIndividual):
        individuals_or_session = {individuals_or_session}
    if not isinstance(individuals_or_session, Session):
        individuals_or_session = iter(individuals_or_session)
        first_individual = next(individuals_or_session)
        session = first_individual.session
        individuals_or_session = chain(
            {first_individual}, individuals_or_session
        )
    else:
        session = individuals_or_session
    if not all_statements:
        buffer_session = Session()

        if isinstance(individuals_or_session, Session):
            class_types = frozenset(
                {
                    # owl:Class
                    OWL.Class,
                    RDFS.Class,
                }
            )
            other_types = frozenset(
                {
                    # owl:AnnotationProperty
                    OWL.AnnotationProperty,
                    RDF.Property,
                    # owl:DatatypeProperty
                    OWL.DatatypeProperty,
                    # owl:ObjectProperty
                    OWL.ObjectProperty,
                    # owl:Restriction
                    OWL.Restriction,
                }
            )
            for s, p, o in individuals_or_session.graph.triples(
                (None, None, None)
            ):
                if p == RDF.type:
                    assertional = any(
                        (o, RDF.type, entity_type) in session.ontology.graph
                        for entity_type in class_types
                    )
                    terminological = o in other_types | class_types
                    if not (assertional or terminological):
                        text = (
                            f"Subject {s} is declared to be of type {o}, "
                            f"which does not match any class from the "
                            f"installed ontologies."
                        )
                        if not all_triples:
                            raise RuntimeError(
                                text
                                + " Set the keyword argument `all_triples` to "
                                "`True` to ignore this error."
                            )
                        else:
                            logger.warning(
                                "Exporting uninterpretable RDF statement: "
                                + text
                            )
                    elif terminological:
                        text = (
                            f"Subject {s} is declared to be of type {o}, "
                            f"meaning that it is part of the terminological "
                            f"knowledge of an ontology. Exporting "
                            f"terminological knowledge is not supported by "
                            f"SymPhoNy. You can ignore this error setting the "
                            f"keyword argument `all_statements` to `True`, "
                            f"but it will likely lead to errors."
                        )
                        raise RuntimeError(text)
                elif not all_triples:
                    try:
                        relationship = session.ontology.from_identifier_typed(
                            p, typing=OntologyRelationship
                        )
                    except (KeyError, TypeError):
                        relationship = None
                    if relationship:
                        try:
                            (
                                individuals_or_session.from_identifier_typed(
                                    o, typing=OntologyIndividual
                                )
                            )
                        except (KeyError, TypeError) as e:
                            raise RuntimeError(
                                f"Individual {s} is the subject of an RDF "
                                f"statement involving the ontology "
                                f"relationship {relationship}. However, "
                                f"SimPhoNy was unable to find an ontology "
                                f"individual with identifier {o} within the "
                                f"set of individuals to be exported. You can "
                                f"ignore this error setting the keyword "
                                f"argument `all_triples` to `True`."
                            ) from e
        elif not all_triples:
            individuals_or_session = set(individuals_or_session)
            for s, p, o in (
                triple
                for individual in individuals_or_session
                for triple in individual.triples
            ):
                try:
                    relationship = session.ontology.from_identifier_typed(
                        p, typing=OntologyRelationship
                    )
                except (KeyError, TypeError):
                    relationship = None
                if relationship:
                    try:
                        session.from_identifier_typed(
                            o, typing=OntologyIndividual
                        )
                    except (KeyError, TypeError) as e:
                        raise RuntimeError(
                            f"Individual {s} is the subject of an RDF "
                            f"statement involving the ontology "
                            f"relationship {relationship}. However, "
                            f"SimPhoNy was unable to find an ontology "
                            f"individual with identifier {o} within the "
                            f"session from which the individuals are being"
                            f"exported. You can "
                            f"ignore this error setting the keyword "
                            f"argument `all_triples` to `True`."
                        ) from e

        buffer_session.add(individuals_or_session, all_triples=all_triples)
        buffer_graph = Graph()
        buffer_graph += buffer_session.graph
    else:
        buffer_graph = Graph()
        if isinstance(individuals_or_session, Session):
            buffer_graph += session.graph
        else:
            buffer_graph.addN(
                (s, p, o, buffer_graph)
                for individual in individuals_or_session
                for s, p, o in individual.triples
            )

    for ns in session.namespaces:
        buffer_graph.bind(ns.name, ns.iri)

    if main:
        buffer_graph.add(main)

    result = buffer_graph.serialize(format=format, encoding="utf-8").decode(
        "utf-8"
    )

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
