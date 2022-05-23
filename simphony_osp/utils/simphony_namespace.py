"""This method contains an RDFLib namespace for the CUBA namespace."""

from pathlib import Path

from rdflib import OWL, RDF, Graph
from rdflib.namespace import ClosedNamespace

file = Path(__file__).parent.parent / "ontology" / "files" / "simphony.ttl"

graph = Graph().parse(file.absolute())

namespace_iri = next(graph.subjects(RDF.type, OWL.Ontology))

entities = (
    IRI[len(namespace_iri) :]
    for type_ in (
        OWL.Class,
        OWL.ObjectProperty,
        OWL.DatatypeProperty,
        OWL.AnnotationProperty,
    )
    for IRI in graph.subjects(RDF.type, type_)
)

simphony_namespace = ClosedNamespace(namespace_iri, entities)
del file, graph, namespace_iri, entities
