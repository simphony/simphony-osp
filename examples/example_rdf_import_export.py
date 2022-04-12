"""An example explaining the RDF import and export functionality."""

# Please install the city ontology: $pico install city

import os

from osp.core.namespaces import city
from osp.core.tools import branch, export_cuds, import_cuds, pretty_print
from osp.wrappers import sqlite

# Create structure.
c = branch(
    branch(
        city.City(
            name="Freiburg",
            coordinates=[0, 0],
            iri="http://example.org/Freiburg",
        ),
        city.Citizen(name="Pablo", age=30, iri="http://example.org/Pablo"),
        city.Citizen(name="Yoav", age=23, iri="http://example.org/Yoav"),
        rel=city.hasInhabitant,
    ),
    city.Neighborhood(
        name="Stühlinger",
        coordinates=[0, 0],
        iri="http://example.org/Stühlinger",
    ),
    city.Neighborhood(
        name="Herdern", coordinates=[0, 0], iri="http://example.org/Stühlinger"
    ),
)

# Export from default session.
export_cuds(file="test.rdf", format="ttl")

# Check output
with open("test.rdf", encoding="utf-8") as f:
    print("Exported from Core Session")
    for line in f:
        print("\t", line.strip())

# Export from a wrapper
with sqlite("test.db") as wrapper:
    wrapper.add(c)
    export_cuds(wrapper, file="test.rdf", format="ttl")

    # Check output
    with open("test.rdf", encoding="utf-8") as f:
        print("Exported from SqliteSession")
        for line in f:
            print("\t", line.strip())

# Create new session and import file
with sqlite("test2.db") as wrapper:
    import_cuds("test.rdf", format="ttl", session=wrapper)
    c = next((x for x in wrapper if x.is_a(city.City)))
    pretty_print(c)

os.remove("test.db")
os.remove("test2.db")
os.remove("test.rdf")
