from cuds.classes import *

# Let's build an EMMO compatible city!
emmo_town = City('EMMO town')

emmo_town.add(Citizen('Emanuele Ghedini'))
emmo_town.add(Citizen('Adham Hashibon'))
emmo_town.add(Citizen('Jesper Friis'))
emmo_town.add(Citizen('Gerhard Goldbeck'))
emmo_town.add(Citizen('Georg Schmitz'))
emmo_town.add(Citizen('Anne de Baas'))

emmo_town.add(Neighbourhood("Ontology"), rel=Encloses)
emmo_town.add(Neighbourhood("User cases"), rel=Encloses)

ontology_uid = None
for neighbourhood in emmo_town.get(CUBA.NEIGHBOURHOOD):
    if neighbourhood.name == "Ontology":
        ontology_uid = neighbourhood.uid
        neighbourhood.add(Building("Relationships"), rel=HasPart)
        neighbourhood.add(Building("Entities"), rel=HasPart)

        # We can go through inverse relationships
        print(neighbourhood.get(rel=IsEnclosedBy)[0].name + ' is my city!')


