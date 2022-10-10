"""An example showing how to access and navigate terminological knowledge.

> In an ontological framework, ontology entities are used as a knowledge
> representation form. Those can be further categorized in two groups:
> ontology individuals (assertional knowledge), and ontology classes,
> relationships, attributes and annotations (terminological knowledge).
> This page focuses on how to access and navigate the terminological knowledge
> of an ontology using SimPhoNy.
-- [Terminological knowledge - SimPhoNy documentation](https://simphony.readthedocs.io/en/v4.0.0rc4/usage/terminological_knowledge.html)

Before running this example, make sure that the city and emmo ontologies are
installed. If it is not the case, install them running the following code:
>>> from simphony_osp.tools.pico import install
>>> install("city", "emmo")
"""

from simphony_osp.namespaces import city, emmo, owl, rdfs
from simphony_osp.ontology import (
    COMPOSITION_OPERATOR,
    RESTRICTION_QUANTIFIER,
    RESTRICTION_TYPE,
    Composition,
    OntologyAnnotation,
    OntologyAttribute,
    OntologyClass,
    OntologyRelationship,
)

# ----- Namespace objects -----
print("\n`city` namespace object")
print(
    "- IRI:",
    city.iri,
)
print("- retrieve the 'Living Being' class by suffix:", city.LivingBeing)
print("- retrieve the 'Living Being' class by label:", city["Living Being"])
print("\n`emmo` namespace object")
print(
    "- retrieve the 'Integer' class by label:",
    emmo.from_iri(
        "http://emmo.info/emmo#EMMO_f8bd64d5_5d3e_4ad4_a46e_c30714fecb7f"
    ),
)

# ----- Ontology entity objects  -----
print("\n`City` ontology entity object from the `city` namespace")
# - accessing labels
print(
    "- main label:", city.City.label
)  # see documentation for the meaning of "main" label
print("- language of main label", city.City.label_lang)
print("- main label as an RDFLib literal", city.City.label_literal)
print("- all labels as RDFLib literal(s)", list(city.City.iter_labels()))
# - accessing identifier and namespace
print("\n`Real` ontology entity object from the `emmo` namespace")
print("- identifier:", emmo.Real.identifier)
print("\n`Equation` ontology entity object from the `emmo` namespace")
print("- namespace:", emmo.Equation.namespace)
# - accessing super- and subclasses
print("\n`LivingBeing` ontology entity object from the `city` namespace")
print("- superclasses:", city.LivingBeing.superclasses)
print("- subclasses:", city.LivingBeing.subclasses)
print("- direct superclasses :", city.LivingBeing.direct_superclasses)
print("- direct subclasses:", city.LivingBeing.direct_subclasses)

print(
    '- subclass of "Living Being"?',
    city.Person.is_subclass_of(city.LivingBeing),
)
print(
    '- superclass of "Person"?', city.LivingBeing.is_superclass_of(city.Person)
)
# - type of entity
print("\n`LivingBeing` ontology class object from the `city` namespace")
print(
    "- is a class?",
    isinstance(city.LivingBeing, OntologyClass)  # one way
    and city.LivingBeing.is_subclass_of(owl.Thing)  # another way
    and (
        not city.LivingBeing.is_subclass_of(owl.topObjectProperty)  # yet
        and not city.LivingBeing.is_subclass_of(owl.topDataProperty)
    ),  # other
)
print(
    "\n`hasInhabitant` ontology relationship object from the `city` namespace"
)
print(
    "- is a relationship?",
    isinstance(city.hasInhabitant, OntologyRelationship)  # one way
    and city.hasInhabitant.is_subclass_of(
        owl.topObjectProperty
    ),  # another way
)
print("\n`name` ontology attribute object from the `city` namespace")
print(
    "- is an attribute?",
    isinstance(city["name"], OntologyAttribute)  # one way
    and city["name"].is_subclass_of(owl.topDataProperty),  # another way
)
print("\n`label` ontology annotation object from the `city` namespace")
print("- is an annotation?", isinstance(rdfs.label, OntologyAnnotation))

# ----- Ontology class objects  -----
# they are subclasses of ontology entity objects
print("\n`citizen` ontology class object from the `city` namespace")
# - attributes
print("- attributes:", city.Citizen.attributes)
# - axioms
print("- attributes:", tuple(str(x) for x in city.Citizen.axioms))
restriction = next(iter(city.Citizen.axioms))
print("- a restriction axiom of the `citizen` ontology class:", restriction)
print("  - quantifier", restriction.quantifier)
print("  - target", restriction.target)
print("  - restriction type", restriction.rtype)
print(
    "  - affected predicate",
    restriction.attribute
    if restriction.rtype == RESTRICTION_TYPE.ATTRIBUTE_RESTRICTION
    else restriction.relationship,
)
print("\n`Integer` ontology class object from the `emmo` namespace")
composition = tuple(
    x for x in emmo.Integer.axioms if isinstance(x, Composition)
)[0]
print("- a composition axiom of the `Integer` ontology class:", restriction)
print("  - operator", composition.operator)
print("  - operands", composition.operands)

# ----- Ontology relationship objects  -----
# they are subclasses of ontology entity objects
print(
    "\n`hasInhabitant` ontology relationship object from the `city` namespace"
)
# - inverse
print("- inverse relationship (if exists):", city.hasInhabitant.inverse)

# ----- Ontology attribute objects  -----
# they are subclasses of ontology entity objects
print("\n`age` ontology attribute object from the `city` namespace")
# - inverse
print("- data type:", city.age.datatype)

# ----- Ontology attribute objects  -----
# they are subclasses of ontology entity objects
# an example is `rdfs.label`
# there is no specific extra functionality for these objects
