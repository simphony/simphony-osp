from cuds.classes import (
    City, Citizen, Neighbourhood, Street,
    HasPart, HasInhabitant,
    CUBA
)
from cuds.utils import pretty_print


# Let's build an EMMO compatible city!
emmo_town = City('EMMO town', coordinates=[42, 42])

emmo_town.add(Citizen(name='Emanuele Ghedini'), rel=HasInhabitant)
emmo_town.add(Citizen(name='Adham Hashibon'), rel=HasInhabitant)
emmo_town.add(Citizen(name='Jesper Friis'), Citizen(name='Gerhard Goldbeck'),
              Citizen(name='Georg Schmitz'), Citizen(name='Anne de Baas'),
              rel=HasInhabitant)

emmo_town.add(Neighbourhood("Ontology"))
emmo_town.add(Neighbourhood("User cases"))

ontology_uid = None
for neighbourhood in emmo_town.get(cuba_key=CUBA.NEIGHBOURHOOD):
    if neighbourhood.name == "Ontology":
        ontology_uid = neighbourhood.uid
        neighbourhood.add(Street("Relationships"), rel=HasPart)
        neighbourhood.add(Street("Entities"), rel=HasPart)
pretty_print(emmo_town)
