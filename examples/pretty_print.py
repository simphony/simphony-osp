"""An example explaining the use of the pretty_print function."""

# Please install the city ontology: $pico install city

from osp.core.namespaces import city
from osp.core.utils import pretty_print


# Let's build an EMMO compatible city!
emmo_town = city.City(name='EMMO town', coordinates=[42, 42])

emmo_town.add(city.Citizen(name='Emanuele Ghedini'), rel=city.hasInhabitant)
emmo_town.add(city.Citizen(name='Adham Hashibon'), rel=city.hasInhabitant)
emmo_town.add(city.Citizen(name='Jesper Friis'),
              city.Citizen(name='Gerhard Goldbeck'),
              city.Citizen(name='Georg Schmitz'),
              city.Citizen(name='Anne de Baas'),
              rel=city.hasInhabitant)

emmo_town.add(city.Neighborhood(name="Ontology"))
emmo_town.add(city.Neighborhood(name="User cases"))

ontology_uid = None
for neighborhood in emmo_town.get(oclass=city.Neighborhood):
    if neighborhood.name == "Ontology":
        ontology_uid = neighborhood.uid
        neighborhood.add(city.Street(name="Relationships"), rel=city.hasPart)
        neighborhood.add(city.Street(name="Entities"), rel=city.hasPart)
pretty_print(emmo_town)
