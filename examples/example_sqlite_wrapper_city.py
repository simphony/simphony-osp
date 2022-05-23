"""An example explaining the use of the SQLite Wrapper."""

# Please install the city ontology: $pico install city

import os

from osp.core.namespaces import city
from osp.core.tools import pretty_print
from osp.wrappers import sqlite

try:
    # Construct the Datastructure.
    c = city.City(name="Freiburg", coordinates=[0, 0])
    p1 = city.Citizen(name="Peter", age=25)
    p2 = city.Citizen(name="Hans", age=25)
    p3 = city.Citizen(name="Michel", age=25)
    n = city.Neighborhood(name="Zähringen", coordinates=[0, 0])
    s = city.Street(name="Le street", coordinates=[0, 0])
    b = city.Building(name="Theater")
    a = city.Address(postalCode=79123, name="Le street", number=12)
    c.connect(p1, p2, p3, rel=city.hasInhabitant)
    c.connect(n).connect(s).connect(b).connect(a)

    print("Connect to DB via sqlite session")
    with sqlite("test.db") as wrapper:
        wrapper.connect(c)
        wrapper.commit()

    print("Reconnect and check if data is still there")
    with sqlite("test.db") as wrapper:
        c = next(filter(lambda x: x.oclass == city.City, wrapper))
        pretty_print(c)

    print("Reconnect and make some changes")
    with sqlite("test.db") as wrapper:
        c = next(filter(lambda x: x.oclass == city.City, wrapper))
        c.name = "Paris"
        wrapper.commit()

    print("Reconnect and check if changes were successful")
    with sqlite("test.db") as wrapper:
        c = next(filter(lambda x: x.oclass == city.City, wrapper))
        pretty_print(c)

    print("Delete the city")
    with sqlite("test.db") as wrapper:
        c = next(filter(lambda x: x.oclass == city.City, wrapper))
        wrapper.delete(c)
        wrapper.commit()

    print("Reconnect and check if deletion was successful")
    with sqlite("test.db") as wrapper:
        cities = filter(lambda x: x.oclass == city.City, wrapper)
        print("All cities:", list(cities))

finally:
    if os.path.exists("test.db"):
        os.remove("test.db")
