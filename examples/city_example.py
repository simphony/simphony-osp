from cuds.classes import *

# Let's build an EMMO compatible city!
emmo_town = City('EMMO town')

emmo_town.add(Citizen('Emanuele Ghedini'), rel=HasPart)
emmo_town.add(Citizen('Adham Hashibon'))
emmo_town.add(Citizen('Jesper Friis'), Citizen('Gerhard Goldbeck'),
              Citizen('Georg Schmitz'), Citizen('Anne de Baas'))

emmo_town.add(Neighbourhood("Ontology"), rel=Encloses)
emmo_town.add(Neighbourhood("User cases"), rel=Encloses)

ontology_uid = None
for neighbourhood in emmo_town.get(cuba_key=CUBA.NEIGHBOURHOOD):
    if neighbourhood.name == "Ontology":
        ontology_uid = neighbourhood.uid
        neighbourhood.add(Building("Relationships"), rel=HasPart)
        neighbourhood.add(Building("Entities"), rel=HasPart)

onto = emmo_town.get(ontology_uid, rel=Encloses)[0]

# We can go through inverse relationships
print(onto.get(rel=IsEnclosedBy)[0].name + ' is my city!')

# Redefined the str() method
# print(emmo_town)

"""
    cuds_object = cuds.classes.CudsObject()
    a_relationship = cuds.classes.ARelationship
    
    cuds_object.add(*other_cuds, rel=a_relationship)
    cuds_object.add(yet_another_cuds)
    
    cuds_object.get()
    cuds_object.get(rel=a_relationship)
    cuds_object.get(*uids)
    cuds_object.get(*uids, rel=a_relationship)
    cuds_object.get(cuba_key=a_cuba_key)
    cuds_object.get(rel=a_relationship, cuba_key=a_cuba_key)
    

    cuds_object.remove()
    cuds_object.remove(*uids/cuds_objects)
    cuds_object.remove(*uids/cuds_objects, rel=a_relationship)
    cuds_object.remove(rel=a_relationship)
    cuds_object.remove(cuba_key=a_cuba_key)
    cuds_object.remove(rel=a_relationship, cuba_key=a_cuba_key)
    
    cuds_object.update(*cuds_objects)
    
    cuds_object.iter()
"""