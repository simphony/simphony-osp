"""An example explaining how to access an installed ontology."""

from osp.core.ontology.oclass_composition import Composition

# Please install the both the city ontology: $pico install city,
# and the European Materials & Modelling Ontology (EMMO): $pico install emmo.

# This imports the namespace city from the city ontology.
from osp.core.namespaces import city
# This imports the namespace math from the EMMO ontology.
from osp.core.namespaces import math


# Accessing entities by suffix.
print('The dot notation can be used to fetch entities by suffix given that '
      'the keyword reference_by_label is set to False in the ontology '
      'installation file.')
print(city.Citizen)

print('Alternative method useful for suffixes with special characters.')
print(city.get_from_suffix('Citizen'))

# Suffixes are case sensitive:
# city.citizen -> Fails.

# Accessing entities by label.
print('The dot notation can be used to fetch entities by label given that '
      'the keyword reference_by_label is set to True in the ontology '
      'installation file.')
print(math.Integer)

print('Alternative method useful for labels with special characters.')
print(math['Integer'])

# Accessing entities by IRI.

print(math.get_from_iri('http://emmo.info/emmo/middle/math#'
                        'EMMO_f8bd64d5_5d3e_4ad4_a46e_c30714fecb7f'))

# Accessing entitites using a string (only useful in rare cases).

from osp.core.namespaces import get_entity  # noqa: E402

print("\nYou can get an entity with a string")
print(get_entity("city.LivingBeing"))
print(get_entity("city.LivingBeing") == city.LivingBeing)


# Basic operations on entities

print("\nYou can access the name of an entity")
print(city.LivingBeing.name)

print("\nYou can access the IRI of an entity")
print(math.Real.iri)

print("\nYou can access the namespace of an entity")
print(math is math.Equation.namespace)

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


# CUBA namespace
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
print(city.Citizen.attribute_declaration)

print("\nYou can get the non-inherited attributes and their defaults")
print(city.Citizen._direct_attributes)
print(city.LivingBeing._direct_attributes)

print("\nWeb Ontology Language Restrictions and Compositions are supported."
      "The `axioms` property returns them.")
tuple(str(x) for x in city.Citizen.axioms)

print("\nAccessing a restriction")
restriction = city.Citizen.axioms[0]
print(restriction)
print(restriction.quantifier)
print(restriction.target)
print(restriction.rtype)
print(restriction.attribute)

print("\nAccessing a composition")
composition = tuple(x for x in math.Integer.axioms
                    if type(x) is Composition)[0]
print(composition)
print(composition.operator)
print(composition.operands)

print("\nYou can get the inverse of a relationship")
print(city.hasInhabitant.inverse)

print("\nYou can get the argument name of an attribute. "
      "The argument name is used when instantiating CUDS objects")
print(city.age.argname)

print("\nYou can get the datatype of attributes")
print(city.age.datatype)

print("\nYou can use the attribute to convert values "
      "to the datatype of the attribute")
result = city.age.convert_to_datatype("10")
print(type(result), result)


# CUDS
print("\nYou can instantiate CUDS objects using ontology classes")
print(city.Citizen(name="Test Person", age=42))
print("Take a look at api_example.py for a description of the CUDS API")

print("\nYou can check if a CUDS object is an instance of an ontology class")
print(city.Citizen(name="Test Person", age=42).is_a(city.Citizen))
print(city.Citizen(name="Test Person", age=42).is_a(city.LivingBeing))

print("\nYou can get the ontology class of a CUDS object.")
print(city.Citizen(name="Test Person", age=42).oclass)
