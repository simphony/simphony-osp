"""Example showing how to access, edit and navigate assertional knowledge.

> In an ontological framework, ontology entities are used as a knowledge
> representation form. Those can be further categorized in two groups: ontology
> individuals (assertional knowledge), and ontology classes, relationships,
> attributes and annotations (terminological knowledge).
-- [Assertional knowledge - SimPhoNy documentation]
   (https://simphony.readthedocs.io/en/v4.0.0/usage/
   assertional_knowledge.html)

This example focuses on accessing, editing and navigating assertional
knowledge. In particular, a few ontology individuals that stand for a city,
some of its neighborhoods and inhabitants are instantiated, and are later
connected and navigated.

Before running this example, make sure that the city and emmo
ontologies are installed. If it is not the case, install them running the
following code:
>>> from simphony_osp.tools.pico import install
>>> install("city", "emmo")
"""

from simphony_osp.namespaces import city, emmo, rdfs
from simphony_osp.tools import pretty_print

# instantiate ontology individuals
person = city.Citizen(
    name="Martin",
    age=15,
)
person.classes = city.Citizen, emmo.Cogniser  # multi-class individuals
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
citizen_1 = city.Citizen(name="Nikola", age=35)
citizen_2 = city.Citizen(name="Lena", age=70)
pretty_print(freiburg)
print()

# edit relationships, attributes and/or annotations
freiburg[city.hasPart] |= neighborhoods
freiburg[city.hasInhabitant] += citizen_1, citizen_2, person
freiburg[rdfs.comment] = "A city in the southwest of Germany."

# navigate the assertional knowledge
can_drive = {
    citizen.name: "Yes" if (True if citizen.age >= 18 else False) else "No"
    for citizen in freiburg.get(rel=city.hasInhabitant, oclass=city.Citizen)
}
for name, drives in can_drive.items():
    print(f"Can {name} drive? {drives}")
