"""An example on how to work with SimPhoNy wrappers.

> In SimPhoNy, assertional knowledge is stored in sessions. You may think of a
> session as a “box” were ontology individuals can be placed. But sessions go
> beyond just storing assertional knowledge. Sessions can be connected to
> SimPhoNy Wrappers. Each wrapper is a piece of software that seamlessly
> translates the assertional knowledge to a form that is compatible with a
> specific simulation engine, database, data repository or file format.
-- [Introduction (to sessions) - SimPhoNy documentation]
   (https://simphony.readthedocs.io/en/v4.0.0rc4/usage/sessions
   /introduction.html)

This example demonstrates the use of teh SQLite wrapper, which is included with
SimPhoNy.

Before running this example, make sure that the city ontology is
installed. If it is not the case, install them running the following code:
>>> from simphony_osp.tools.pico import install
>>> install("city")
"""

from simphony_osp.namespaces import city
from simphony_osp.tools import pretty_print
from simphony_osp.wrappers import SQLite

# instantiate some individuals directly in an SQLite database
with SQLite("database.db", create=True) as sqlite:
    sqlite.clear()  # just in case you already ran this example
    freiburg = city.City(name="Freiburg", coordinates=[47.997791, 7.842609])
    peter = city.Citizen(name="Peter", age=30)
    anne = city.Citizen(name="Anne", age=20)
    freiburg[city.hasInhabitant] += peter, anne
    sqlite.commit()

# retrieve the saved individuals and show them using pretty_print
with SQLite("database.db", create=False) as sqlite:
    pretty_print(sqlite.get(oclass=city.City).one())
