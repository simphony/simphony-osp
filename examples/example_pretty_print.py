"""An example explaining the use of the pretty_print function."""

# Please install the city ontology: $pico install city

from osp.core.namespaces import city
from osp.core.tools import pretty_print

# Let's build an EMMO compatible city!
emmo_town = city.City(name="EMMO town", coordinates=[42, 42])

emmo_town.connect(
    city.Citizen(name="Emanuele Ghedini", age=15), rel=city.hasInhabitant
)
emmo_town.connect(
    city.Citizen(name="Adham Hashibon", age=15), rel=city.hasInhabitant
)
emmo_town.connect(
    city.Citizen(name="Jesper Friis", age=15),
    city.Citizen(name="Gerhard Goldbeck", age=15),
    city.Citizen(name="Georg Schmitz", age=15),
    city.Citizen(name="Anne de Baas", age=15),
    rel=city.hasInhabitant,
)

emmo_town.connect(city.Neighborhood(name="Ontology", coordinates=[1, 2]))
emmo_town.connect(city.Neighborhood(name="User cases", coordinates=[3, 4]))

ontology_uid = None
for neighborhood in emmo_town.get(oclass=city.Neighborhood):
    if neighborhood.name == "Ontology":
        ontology_uid = neighborhood.uid
        neighborhood.connect(
            city.Street(name="Relationships", coordinates=[5, 6]),
            rel=city.hasPart,
        )
        neighborhood.connect(
            city.Street(name="Entities", coordinates=[7, 8]), rel=city.hasPart
        )
pretty_print(emmo_town)
