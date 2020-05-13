from osp.core import CITY
from osp.core.utils import pretty_print


# Let's build an EMMO compatible city!
emmo_town = CITY.CITY(name='EMMO town', coordinates=[42, 42])

emmo_town.add(CITY.CITIZEN(name='Emanuele Ghedini'), rel=CITY.HAS_INHABITANT)
emmo_town.add(CITY.CITIZEN(name='Adham Hashibon'), rel=CITY.HAS_INHABITANT)
emmo_town.add(CITY.CITIZEN(name='Jesper Friis'),
              CITY.CITIZEN(name='Gerhard Goldbeck'),
              CITY.CITIZEN(name='Georg Schmitz'),
              CITY.CITIZEN(name='Anne de Baas'),
              rel=CITY.HAS_INHABITANT)

emmo_town.add(CITY.NEIGHBORHOOD(name="Ontology"))
emmo_town.add(CITY.NEIGHBORHOOD(name="User cases"))

ontology_uid = None
for neighborhood in emmo_town.get(oclass=CITY.NEIGHBORHOOD):
    if neighborhood.name == "Ontology":
        ontology_uid = neighborhood.uid
        neighborhood.add(CITY.STREET(name="Relationships"), rel=CITY.HAS_PART)
        neighborhood.add(CITY.STREET(name="Entities"), rel=CITY.HAS_PART)
pretty_print(emmo_town)
