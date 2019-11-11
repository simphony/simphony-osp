from osp.core import CITY
from cuds.cuds2dot import Cuds2dot

city = CITY.CITY(name="Freiburg", uid='f3a6eb24-bfda-4c95-8a23-799c2bab2004')
neighbourhood = CITY.NEIGHBOURHOOD(name="Zähringen")
city.add(neighbourhood)


for i in range(10):
    street = neighbourhood.add(CITY.STREET(name="Street %s" % i))
    street.add(CITY.BUILDING(name="Building %s" % i))


Cuds2dot(city).render()
