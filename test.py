import rdflib
import logging

from osp.core.namespaces import CITY

c = CITY.CITY(name="Hallo", coordinates="toll")
print(c)
print(c.name)
print(c.coordinates)
print(CITY.COORDINATES)
print(CITY.COORDINATES.datatype)
c.name = "Test"
print(c.name)
