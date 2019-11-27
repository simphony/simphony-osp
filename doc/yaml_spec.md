# Description of YAML format Specification

This file describes the ontology format that is used by OSP core. 

## Info

Contact: [Matthias Urban](mailto:matthias.urban@iwm.fraunhofer.de) and  [Pablo de Andres](mailto:pablo.de.andres@iwm.fraunhofer.de) from the 
Material Informatics team, Fraunhofer IWM.

Version: 3.0 pending approval

## Introduction

In this file we will give a description of how an Ontology can be
represented in a yaml file format and how to interpret such files. For
simplicity reasons in the following we will give examples from the
**\* example ontology \*** file which can be found in osp/core/ontology/yml/ontology.city.yml.

What is an ontology?

An ontology defines a set of representational primitives with which to
model a domain of knowledge or discourse. The representational
primitives are typically classes (or sets), attributes (or properties),
and relationships (or relations among class members). The definitions of
the representational primitives include information about their meaning
and constraints on their logically consistent application. (Source:
<http://tomgruber.org/writing/ontology-definition-2007.htm>)

## Terminology

The following terms are used in relation to the SimPhoNy ontology and
metadata description:

1. `class`: a concept. E.g., 'City', 'Experiment'.
1. `attribute`: a property of a class that has a data type. E.g., 'name' of the type String which could be used as an attribute of 'City'.
1. `individual`: an instance of a class. E.g., an instance of the class 'City' can be used to represent the city of Freiburg in which case it would have the attribute 'name' with the value 'Freiburg'.
1. `relationship`: a type of a way in which one individual relates to another. E.g., 'Has-A' which could use to form the relationship 'Freiburg (City) Has-A Dreisam (River)'.
1. `entity`:  a general term that can refer to a class, a relationship, attribute, or an individual. E.g., 'City', 'name', 'Has-A', the Freiburg individual are all entities.
1. `ontology`: an explicit, formal specification of a shared conceptualization. See definition above.
1. `namespace`: an ontology identifier. E.g., 'CITY_ONTOLOGY' which could be used as a namespace for the ontology that consists of the entities 'City', 'name' and 'Has-A'.
    - Each entity is uniquely identified by its name and the namespace it is contained in. We call \<namespace name\>.\<entity name\> the `qualified entity name`.
1. `CUDS`:  Common Universal Data Structure. A data structure that is used to uniformly represent ontology concepts in programming code.
    - CUDS exposes an API that provides CRUD (Create, Read, Update and Delete) functionalities.
    - CUDS is a recursive data structure in that a CUDS object may contain other CUDS objects.
1. `CUDS class`: represents an ontology class and encodes its ontological information.
1. `CUDS object`: is an instance of a CUDS class represents and ontology individual.

CUDS is the fundamental data type of OSP-core, a framework that establishes interoperability between software systems that are built on top of ontologies.

Note that the terms  'CUDS object',  'CUDS instance', 'instance', 'individual' are sometimes used interchangeably.

## Naming of the files

Name any ontolgy `ontology.<name>.yml`, where `<name>` should be replaced by a user defined name.

## Syntax of the .yml ontology

`VERSION`: string

> Contains semantic version Major.minor in format M.m with M and m
> positive integers. minor MUST be incremented when backward
> compatibility in the format is preserved. Major MUST be incremented
> when backward compatibility is removed. Due to the strict nature of
> the format, a change in minor is unlikely.

`NAMESPACE`: string

> Defines the namespace of the current file. We recommend to use
  ALL_UPPERCASE for the namespace name, with underscore as separation.
  All entities defined in this file will live in the namespace defined here.

`ONTOLOGY`: dict

> Contains individual declarations for ontology entities as a mapping.
> Each key of the mapping is the name of an ontology entity.
> The key should be ALL_UPPERCASE, with underscore as separation.
> The value of the mapping is a mapping whose format is detailed in the
> [Ontology entities format](#ontology-entities-format).

## Ontology entities format

Every declaration of an ontology entity must have the following keys:

`description`: string
> For human consumption. An ontological short description of the carried
> semantics. Should have the form: entity is a superclass\_entity that
> has \<differentiating\> terms.
>
`subclass_of`: List[**\`\`qualified entity name\`\`**].
> Its value is fixed on the ontology level.
>
> The subclass keyword expresses an **ontological is-a**
> relation. MUST be a list of a fully qualified strings referring to another entity.
> Only the entity `ENTITY` is allowed to have no superclass. See [Special entities](#special-entities).
>
> If entity A is a subclass of B and B is subclass of C,
> then A is also subclass of C.

An ontology entity can be either a relationship, a cuds entity or an attribute.
Depending on that the mapping can have further keys.
For cuds entities these keys are described in
[CUDS entities format](#cuds-entities-format) section.
For relationship entities, these keys are described in
[Relationship format](#relationship-format) section.
For attributes, these keys are described in
[Attribute format](#attribute-format) section.

## The CUBA namespace

The CUBA namespace contains a set of Common Universal Basic entities, that have special meaning in OSP-core.
The CUBA namespace is always installed in OSP-core.

`CUBA.ENTITY`
> The entity is the root of the ontology. It is the only entity which does not have a superclass.
> Every other entity is a subclass of `ENTITY`.

`CUBA.NOTHING`
> An ontology class, that is not allowed to have individuals.

`CUBA.RELATIONSHIP`
> The root of all relationships. Its direct superclass is `ENTITY`.

`CUBA.ATTRIBUTE`
> The root of all attributes. Its direct superclass is `ENTITY`.

`CUBA.WRAPPER`
> The root of all wrappers. These are the bridge to simulation engines and databases. See the examples in examples/.

`CUBA.ACTIVE_RELATIONSHIP`
> The root of all active relationships. Active relationships express that one cuds object is in the container of another.

## Attribute format

Every attribute is a subclass of `ATTRIBUTE`.
The declaration of an attribute is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format). It furthermore can have the following keys:

`datatype`: string

> It is an attribute of an entity in cases when the datatype of said
> entity is important.
>
> Describes the datatype of the value that a certain entity can take. It
> can be one of the following:
>
> - `BOOL`: a form of data with only two possible values (usually
>   \"true\" or \"false\")
> - `INT`: a sequence of positive and negative digits
> - `FLOAT`: a digit containing values on both sides of the decimal
>   point
> - `STRING`: a set of characters that can also contain spaces and
>   numbers. The length can be specified with "STRING:LENGTH" (e.g.
>   STRING:20 means the length of the string should be maximum 20
>   characters).
> - `VECTOR:D1:D2:...:Dn`: a vector of the given dimensions, from the
>   outside inwards. For example, a VECTOR:4:2:1 would be:
>   { [(a), (b)],  [(c), (d)], [(e), (f)], [(g), (h)] } 
>   (the different delimiters are only used for visual purposes)
>
> In case a datatype is not specified the default datatype is assumed to
> be STRING
>
> For example: The datatype of entity NUMBER is INT.

## Class expressions

A class expression describes a subset of individuals.
They are similar to classes, but do not have a name in the ontology.
Class expressions will be used in [CUDS entities format](#CUDS-entities-format) and [Relationship format](#Relationship-format).
They can be either:

- A **\`\`qualified entity name\`\`** of a class. In this case it corresponds to all individuals of referenced class.
- Requirements on the individual's relationships. For example:

  ```yml
  CITY.HAS_INHABITANT:
    cardinality: 1+
    range: CITY.CITIZEN
    exclusive: false
  ```

  This describes the set of individuals that have at least one citizen as inhabitant.
  In general it describes the individuals which have some relationship to some object.
  It is a mapping from the **\`\`qualified entity name\`\`** of a relationship to the following keywords:

  `range`
  > A class expression describing the individuals which are object of the relationship.

  `cardinality`
  > The number of times individuals defined in `range` is allowed to be a object of the relationship.
  > To define the `cardinality` we use the following syntax:
  >
  > - many / * / 0+ (default): Zero to infinity target objects are allowed.
  > - some / \+ / 1+: At least one target object is required.
  > - ? / 0-1: At most one target object is allowed.
  > - a+: At least a target objects are required.
  > - a-b: At least a and at most b target objects are required (i.e. inclusive).
  > - a: Exactly a target objects are required.

  `exclusive`
  > Whether the given `target` is the only allowed object.
- A composition of several class expressions. For example:

  ```yml
  OR:
    - CITY.CITY
    - CITY.NEIGHBOURHOOD
  ```

  This is the union of all individuals that are a city or a neighbourhood.
  We use the keyword `OR` for union, `AND` for intersection and `NOT` for complement.
  After `OR` and `AND`, a list of  class expressions for the union / intersection is expected.
  After `NOT` a single class expression is expected.

The definition of class expressions is recursive. For example:

```yml
OR:
  - CITY.CITY
  - CITY.HAS_PART:
      cardinality: 1+
      range: CITY.NEIGHBOURHOOD
      exclusive: false
```

This describes the set of all individuals that are a city or have a neighbourhood.

## CUDS classes format

The declaration of a cuds entity is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format).
It can contain further information:

`attributes`: Dict[**\`\`qualified entity name\`\`**, default_value]
> Expects a mapping from the **\`\`qualified entity name\`\`** of an attribute to its default.
> Each key must correspond to a subclass of `ATTRIBUTE`. For example:
>
> ```yml
> ADDRESS:
>   ...
>   attributes:
>     CITY.NAME: "Street"
>     CITY.NUMBER:
> ```
>
> Here, an address has a name and a number.
> The default name is "Street", the number has no default.
> If no default is given, the user is forced to specify a value each time he creates an individual.

`subclass_of`: List[Class expression]
> In addition to qualified entity names of classes, class expressions are also allowed.
> These class expressions restrict the individuals allowed in the class. Only those
> individuals are allowed that are in the intersection of the class expressions. For example:
>
> ```yml
> POPULATED_PLACE:
>    description:
>    subclass_of:
>    - CITY.GEOGRAPHICAL_PLACE
>    - CITY.HAS_INHABITANT:
>        range: CITY.CITIZEN
>        cardinality: many
>        exclusive: true
> ```
>
> Here, a populated place is a geographical place which must have citizens as inhabitants.

`disjoint_with`: List[Class expression]
> A list of class expressions that are not allowed to share any individuals with the cuds entity.

`equivalent_to`: List[Class expression]
> A list of class expressions who contain the same individuals as the cuds entity. For example:
>
> ```yml
> POPULATED_PLACE:
>    description:
>    equivalent_to:
>    - CITY.GEOGRAPHICAL_PLACE
>    - CITY.HAS_INHABITANT:
>        range: CITY.CITIZEN
>        cardinality: many
>        exclusive: true
> ```
>
> Here every geographical place that has citizens as inhabitants is automatically a populated place.

## Relationship format

Every relationship is a subclass of `RELATIONSHIP`.
The declaration of a relationship is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format).
Furthermore, it mus have the following keys:

`inverse`: **\`\`qualified entity name\`\`** or empty (None)
> If CUDS object A is related to CUDS object B via relationship REL, then B is related
> with A via the inverse of REL.
>
> For example: The inverse of HAS\_PART is IS\_PART\_OF.
>
> If no inverse is given, OSP core will automatically create one.

`domain`: Class expression
> A class expression describing the individuals that are allowed to be a subject of the relationship.
> If multiple class expressions are given, the relationship's domain is the intersection of the class expressions.

`range`: Class expression
> A class expression describing the individuals that are allowed to be object of the relationship.
> If multiple class expressions are given, the relationship's range is the intersection of the class expression.

`characteristics`: String
> A list of characteristics of the relationship. The following characteristics are supported:
>
> - reflexive
> - symmetric
> - transitive
> - functional
> - irreflexive
> - asymmetric
> - inversefunctional

A subclass of a relationship is called a sub-relationship.
