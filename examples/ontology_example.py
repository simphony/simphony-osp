# If you did not install the CITY ontology
# (pico install city),
# you have to execute these commands first:
# from osp.core import Parser
# p = Parser()
# p.parse("city")

from osp.core import city, CITY  # This imports the namespace city

# Basic operations on entities

print("\nYou can use UPPERCASE and lowercase to access a namespace")
print(city is CITY)

print("\nYou can use the namespace to access its entities")
print(city.living_being)

print("\nYou can use UPPERCASE, lowercase or CamelCase to access entities")
print(city.living_being is city.LIVING_BEING is city.LivingBeing)

print("\nYou can also use index noteation")
print(city.living_being is city["living_being"])

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
print(get_entity("city.LivingBeing") is city.LivingBeing)

# CUBA namespace
# This is the main namespace that is always available
from osp.core.namespaces import CUBA  # noqa: E402

# These are the classes for the ontology entities
from osp.core.ontology import (  # noqa: F401, E402
      OntologyEntity,
      OntologyClass,
      OntologyRelationship,
      OntologyAttribute
)

print("\nYou can test if an entity is a class")
print(isinstance(city.LivingBeing, OntologyClass))
print(not city.LivingBeing.is_subclass_of(cuba.Relationship)
      and not city.LivingBeing.is_subclass_of(cuba.Attribute))

print("\nYou can test if an entity is a relationship")
print(isinstance(city.HasInhabitant, OntologyRelationship))
print(city.HasInhabitant.is_subclass_of(cuba.Relationship))

print("\nYou can test if an entity is a attribute")
print(isinstance(city.Name, OntologyAttribute))
print(city.Name.is_subclass_of(cuba.Attribute))

# Type specific operations
print("\nYou can get the attributes of an ontology class and their defaults")
print(city.Citizen.attributes)

print("\nYou can get the non-inherited attributes and their defaults")
print(city.LivingBeing.own_attributes)

print("\nFurther interesting properties:")
print("\nSubclass of:",
      list(map(str, city.LivingBeing.subclass_of_expressions)))
print("\nEquivalent to:", city.LivingBeing.equivalent_to_expressions)  # empty
print("\nDisjoint with:", city.LivingBeing.disjoint_with_expressions)  # empty

print("\nYou can get the inverse of a relationship")
print(city.HasInhabitant.inverse)

print("\nYou can get the characteristics of a relationship")
print(city.HasPart.characteristics)

print("\nYou can get the domain and range of a relationship")
print(city.HasPart.domain_expressions)  # empty
print(city.HasPart.range_expressions)  # empty

print("\nYou can get the argument name of an attribute. "
      "The argument name is used when instantiating CUDS objects")
print(city.Age.argname)

print("\nYou can get the datatype of attributes")
print(city.Age.datatype)

print("\nYou can use the attribute to convert values "
      "to the datatype of the attribute")
print(city.Age.convert_to_datatype("10"))

# CUDS
print("\nYou can instantiate CUDS objects using ontology classes")
print(city.Citizen(name="Test Person", age=42))
print("Take a look at api_example.py for a description of the CUDS API")

print("\nYou can check if a CUDS object is an instace of a ontology class")
print(city.Citizen(name="Test Person", age=42).is_a(city.Citizen))
print(city.Citizen(name="Test Person", age=42).is_a(city.LivingBeing))

print("\nYou can get the ontology class of a CUDS object.")
print(city.Citizen(name="Test Person", age=42).oclass)

# NAMESPACE_REGISTRY
from osp.core import ONTOLOGY_NAMESPACE_REGISTRY as namespace_reg  # noqa: E402

print("\nAll namespaces are stored in the namespace registry")
print(namespace_reg)

print("\nYou can access the namespaces using dot or index notation")
print(namespace_reg.city)
print(namespace_reg["city"])
