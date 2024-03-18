"""An example on how to work with sessions.

> In SimPhoNy, assertional knowledge is stored in sessions. You may think of a
> session as a “box” were ontology individuals can be placed. But sessions go
> beyond just storing assertional knowledge. Sessions can be connected to
> SimPhoNy Wrappers. Each wrapper is a piece of software that seamlessly
> translates the assertional knowledge to a form that is compatible with a
> specific simulation engine, database, data repository or file format.
-- [Introduction (to sessions) - SimPhoNy documentation]
   (https://simphony.readthedocs.io/en/v4.0.0/usage/sessions
   /introduction.html)

This example deals, however, with sessions that are NOT connected to any
wrapper. It covers creating sessions, managing, querying, exporting their
contents as RDF files and importing RDF files into sessions.

Before running this example, make sure that the city ontology is
installed. If it is not the case, install them running the following code:
>>> from simphony_osp.tools.pico import install
>>> install("city")
"""

from simphony_osp.namespaces import city, owl
from simphony_osp.ontology import OntologyIndividual
from simphony_osp.session import Session, core_session
from simphony_osp.tools import export_file, import_file, pretty_print, search

# Every time an object from the `simphony_osp` package is imported, a session
# called "core session" is created and set as "default session".

# Newly instantiated individuals are stored in the session currently set
# as default,
thing = owl.Thing()
assert thing in core_session
# unless a different session is specified.
another_session = Session()
another_thing = owl.Thing(session=another_session)
assert another_thing in another_session
assert thing not in another_session
another_session.clear()  # clear the session's contents

"""
> Sessions actually work in a way similar to databases. To start using them,
> one first has to “open” or “connect” to them. After that, changes can be
> performed on the data they contain, but such changes are not made permanent
> until a “commit” is performed. When one finishes working with them, the
> connection should be “closed”. Unconfirmed changes are lost when the
> connection is “closed”.

> In SimPhoNy, all sessions are automatically “opened” when they are created.
> The “commit” and “close” operations are controlled manually.
-- [Introduction (to sessions) - SimPhoNy documentation]
   (https://simphony.readthedocs.io/en/v4.0.0/usage/sessions
   /introduction.html)

Note that despite the above, sessions that are not connected to a wrapper (the
ones being considered in this example) do not perform any action when asked to
commit the data (there is nowhere to persist the data) or when they are closed
(there is no file to close, database to disconnect from or any other resource
to release).
"""

# The default session can be temporarily changed by using it as a context
# manager.
another_session.locked = True
# Prevents the session from being closed when leaving its context.
with another_session:
    freiburg = city.City(name="Freiburg", coordinates=[47.997791, 7.842609])
    neighborhoods = {
        city.Neighborhood(name=name, coordinates=coordinates)
        for name, coordinates in [
            ("Altstadt", [47.99525, 7.84726]),
            ("Stühlinger", [47.99888, 7.83774]),
            ("Neuburg", [48.00021, 7.86084]),
            ("Herdern", [48.00779, 7.86268]),
            ("Brühl", [48.01684, 7.843]),
        ]
    }
    citizen_1 = city.Citizen(
        name="Nikola", age=35, iri="http://example.org/Nikola"
    )
    citizen_2 = city.Citizen(
        name="Lena", age=70, iri="http://example.org/Lena"
    )
    freiburg[city.hasPart] |= neighborhoods
    freiburg[city.hasInhabitant] += citizen_1, citizen_2
    pretty_print(freiburg)
    print()


# Assertional knowledge can be transferred from one session to another.
session = Session()
session.locked = True
freiburg_copy = session.add(freiburg)
assert freiburg not in session
assert freiburg_copy not in another_session
assert freiburg_copy in session
session.add(another_session, exists_ok=True, merge=False)  # copy whole session


# The session object is the basic way to query the session.
assert len(session) == 8
assert session.get("http://example.org/Lena").name == "Lena"
assert len(session.get(oclass=city.Citizen)) == 2


# The `find` function from the search module and its variants provide more
# advanced querying capabilities. They work by traversing the graph from a
# given initial ontology individual. Only `find` is briefly demonstrated here,
# check out the documentation to find out
# which variants are available and advanced usage.
assert {
    citizen.name
    for citizen in set(
        search.find(
            freiburg,
            rel=city.hasInhabitant,
            criterion=lambda individual: individual.is_a(city.Citizen),
        )
    )
} == {"Lena", "Nikola"}

# SPARQL queries are the most powerful method for getting information
# from the session
with session:
    result = search.sparql(
        f"""
        SELECT ?citizen ?age WHERE {{
            <{freiburg.identifier}> <{city.hasInhabitant.identifier}>
            ?citizen .
            ?citizen <{city.age.identifier}> ?age.
        }}
    """
    )(citizen=OntologyIndividual, age=int)
    for citizen, age in result:
        print(citizen.name, age)

# Session contents can be exported to RDF,
export_file(session, file="./session.ttl", format="turtle")
# and imported back.
session.clear()
assert len(session) == 0
import_file("./session.ttl", session=session)
assert len(session) == 8
