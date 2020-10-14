"""An example explaining how to access an installed ontology."""

# Please install the city ontology: $pico install city

from osp.core.namespaces import city  # This imports the namespace city

# Basic operations on entities

print("\nYou can use the namespace to access its entities")
print(city.LivingBeing)

print("\nYou can also use index noteation")
print(city.LivingBeing == city["LivingBeing"][0])

print("\nYou can access the namespace of an entity")
print(city is city.LivingBeing.namespace)

print("\nYou can access the superclasses and the subclasses")
print(city.LivingBeing.superclasses)
print(city.LivingBeing.subclasses)

print("\nYou can access the direct superclasses and subclasses")
print(city.LivingBeing.direct_superclasses)
print(city.LivingBeing.direct_subclasses)

print("\nYou can access a description of the entities")
print(city.LivingBeing.description)

print("\nYou can test if one entity is a subclass / superclass of another")
print(city.Person.is_subclass_of(city.LivingBeing))
print(city.LivingBeing.is_superclass_of(city.Person))

# Get entities by string
from osp.core.namespaces import get_entity  # noqa: E402

print("\nYou can get an entity with a string")
print(get_entity("city.LivingBeing"))
print(get_entity("city.LivingBeing") == city.LivingBeing)

# cuba namespace
# This is the main namespace that is always available
from osp.core.namespaces import cuba  # noqa: E402

# These are the classes for the ontology entities
from osp.core.ontology import (  # noqa: F401, E402
    OntologyEntity,
    OntologyClass,
    OntologyRelationship,
    OntologyAttribute
)

print("\nYou can test if an entity is a class")
print(isinstance(city.LivingBeing, OntologyClass))
print(not city.LivingBeing.is_subclass_of(cuba.relationship)
      and not city.LivingBeing.is_subclass_of(cuba.attribute))

print("\nYou can test if an entity is a relationship")
print(isinstance(city.hasInhabitant, OntologyRelationship))
print(city.hasInhabitant.is_subclass_of(cuba.relationship))

print("\nYou can test if an entity is a attribute")
print(isinstance(city.name, OntologyAttribute))
print(city.name.is_subclass_of(cuba.attribute))

# Type specific operations
print("\nYou can get the attributes of an ontology class and their defaults")
print(city.Citizen.attributes)

print("\nYou can get the non-inherited attributes and their defaults")
print(city.Citizen.own_attributes)
print(city.LivingBeing.own_attributes)

print("\nYou can get the inverse of a relationship")
print(city.hasInhabitant.inverse)

print("\nYou can get the argument name of an attribute. "
      "The argument name is used when instantiating CUDS objects")
print(city.age.argname)

print("\nYou can get the datatype of attributes")
print(city.age.datatype)

print("\nYou can use the attribute to convert values "
      "to the datatype of the attribute")
print(city.age.convert_to_datatype("10"))

# CUDS
print("\nYou can instantiate CUDS objects using ontology classes")
print(city.Citizen(name="Test Person", age=42))
print("Take a look at api_example.py for a description of the CUDS API")

print("\nYou can check if a CUDS object is an instace of an ontology class")
print(city.Citizen(name="Test Person", age=42).is_a(city.Citizen))
print(city.Citizen(name="Test Person", age=42).is_a(city.LivingBeing))

print("\nYou can get the ontology class of a CUDS object.")
print(city.Citizen(name="Test Person", age=42).oclass)
