"""An example explaining the RDF import and export functionality."""

# Please install the city ontology: $pico install city

# If you did not install the city ontology
# (pico install city),
# you have to execute these commands first:
# from osp.core import Parser
# p = Parser()
# p.parse("city")

import uuid
import re
import os
from rdflib import URIRef
from osp.wrappers.sqlite import SqliteSession
from osp.core.namespaces import city
from osp.core.utils import serialize_rdf_graph, branch, import_rdf_file, \
    pretty_print

uuid_re = re.compile(r".*(http://www\.osp-core\.com/cuds#"
                     r"([a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}"
                     r"-[a-z0-9]{4}-[a-z0-9]{12})).*")

# Create CUDS structure
c = branch(branch(city.City(name="Freiburg"),
                  city.City(name="Pablo"),
                  city.City(name="Yoav"),
                  rel=city.hasInhabitant),
           city.Neighborhood(name="Stühlinger"),
           city.Neighborhood(name="Herdern"))

# Export from Core Session
serialize_rdf_graph("test.rdf", format="ttl")

# Check output
with open("test.rdf") as f:
    print("Exported from Core Session")
    for line in f:
        print("\t", line.strip())

# Export from a Wrapper session
with SqliteSession(path="test.db") as session:
    w = city.CityWrapper(session=session)
    w.add(c)
    serialize_rdf_graph("test.rdf", format="ttl", session=session)

    # Check output
    with open("test.rdf") as f:
        print("Exported from SqliteSession")
        for line in f:
            print("\t", line.strip())

    # Usually, RDF data does not contain UUIDs as in the current output.
    # Replace UUIDs in the RDF file.
    # THIS IS JUST FOR DEMONSTRATION PURPOSES.
    # THIS ALLOWS US TO SHOW THAT OSP-CORE CAN IMPORT ANY RDF DATA,
    # AND NOT ONLY DATA THAT WAS PREVIOUSLY EXPORTED BY OSP CORE!
    # THIS IS NOTHING THAT YOU AS A USER WOULD EVER HAVE TO DO.

    print("Replace UUID in turtle file")
    with open("test.rdf") as f1:
        with open("test2.rdf", "w") as f2:
            for line in f1:
                match = uuid_re.match(line)
                if match:
                    uid = uuid.UUID(match[2])
                    line = line.replace(match[1], "http://city.com/"
                                        + session._registry.get(uid).name)
                print("\t", line, end="")
                print(line, end="", file=f2)

# Create new session and import file
with SqliteSession(path="test2.db") as session:
    w = city.CityWrapper(session=session)  # wrapper will be skiped for export
    import_rdf_file("test2.rdf", format="ttl", session=session)
    w.add(session.load_from_iri(URIRef("http://city.com/Freiburg")).one())
    print("Imported data:")
    pretty_print(w)

os.remove("test.db")
os.remove("test2.db")
os.remove("test.rdf")
os.remove("test2.rdf")
