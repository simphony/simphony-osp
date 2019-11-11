# Description of YAML format Specification

This is the yaml file format, that has the ability to represent EMMO.
It is currently not supported by any version of osp-core.

## Info

Contact: [Matthias Urban](mailto:matthias.urban@iwm.fraunhofer.de) and  [Pablo de Andres](mailto:pablo.de.andres@iwm.fraunhofer.de) from the 
Material Informatics team, Fraunhofer IWM.

Version: 2.0 pending approval

## Introduction

In this file we will give a description of how an Ontology can be
represented in a yaml file format and how to interpret such files. For
simplicity reasons in the following we will give examples from the
**\* example ontology \*** file which can be found here **\*
provide the link to the file \***.

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

- `class`: an entity, a thing, a class in the ontology and
  corresponding data structure. Example: the Lennard Jones potential,
  a vector, a mode, etc.
- `CUDS`: a Common Universal Data Structure, an entity that encodes an
   ontology `Class` (sometimes called a concept) in the metadata.
- `CUBA` : a Common Universal Basic Attribute signifying a specific
  unique vocabulary to defined a CUDS class, it is the term used to
  define the class.
- `CUBA Key`: the actual vocabulary in the yml specifications is
  referred to as the CUBA Key.

## Naming of the files

Name any ontolgy `ontology.<name>.yml`, where `<name>` should be replaced by a user defined name.

## Syntax of the .yml ontology

`VERSION`: string

> Contains semantic version Major.minor in format M.m with M and m
> positive integers. minor MUST be incremented when backward
> compatibility in the format is preserved. Major MUST be incremented
> when backward compatibility is removed. Due to the strict nature of
> the format, a change in minor is unlikely.

`ONTOLOGY_MODE`: string

> Describes the mode in which the validity checks are performed while
working with osp-core. There
> are three values possible for the ONTOLOGY\_MODE:
>
> 1. strict: Error is raised as soon as any relationship that is not 
>    supported is added. Error is raised on commit if cardinalities are
>    violated.
> 2. minimum\_requirements: Error is raised on commit if cardinalities
>    are violated.
> 3. ignore: no validity checks are performed.
>
> An error is raised at commit means that an error is raised when a
> \"flush\" to the engine happens, example: a commit to a database or
> the execution of a simulation.

`CUDS_ONTOLOGY`: dict
> Contains individual declarations for ontology entities as a mapping.
> Each key of the mapping is the name of an ontology entity (the
> CUBA). The **Key MUST be all uppercase**, with underscore as separation.
> Numbers are not allowed. The value of the mapping is a mapping
> whose format is detailed in the [Ontology entities format](#ontology-entities-format).

## Ontology entities format

Every declaration of an ontology entity must have the following keys:

`definition`: string
> For human consumption. An ontological short description of the carried
> semantics. Should have the form: sub\_entity is a superclass\_entity that
> has \<differentiating\> terms.
>
`subclass_of`: List[**\`\`qualified CUBA key\`\`**].
> Its value is fixed on the ontology level.
>
> The superclass CUDS is for inheritance relations, expressing an **ontological is-a**
> relation. MUST be a list of a fully qualified strings referring to another CUDS entry.
> Only the cuds entry `ENTITY` is allowed to have no superclass. See [Special entities](#special-entities).
>
> If entity A is a subclass of B, we say that A is a sub-entity of B. \
> If entity A is a sub-entity of B and B is sub-entity of C,
> then A is also sub-entity of C.

An ontology entity can be either a relationship, a cuds entity or a value.
Depending on that the mapping can have further keys.
For cuds entities these keys are described in
[CUDS entities format](#cuds-entities-format) section.
For relationship entities, these keys are described in
[Relationship format](#relationship-format) section.
For values, these keys are described in
[Value format](#value-format) section.

## Special entities

`ENTITY`
> The entity is the root of the ontology. It is the only entity which does not have a superclass.
> Every other entity is a sub-entity of `ENTITY`.

`CUDS_ENTITY`
> This is the root for all entities that can have individuals. Its direct superclass is `ENTITY`.

`RELATIONSHIP`
> This is the root of all relationships. Its direct superclass is `ENTITY`.

`VALUE`
> This is the root of all values. A value is some kind of data, like a String or a Number. Its direct superclass is `ENTITY`.

## Value format

Every value is a sub-entity of `VALUE`.
The declaration of a value is a special case of the declaration of an entity.
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

- A **\`\`qualified CUBA key\`\`**. In this case it corresponds to all individuals of the CUBA key's class.
- A description of the individual's relationships. For example:

  ```yml
  CUBA.HAS_PART:
    cardinality: 1+
    target: CUBA.ATOM
    only: false
  ```

  This describes the set of individuals that have at least one atom.
  In general it describes the individuals which have some relationship to some object.
  It is a mapping from the **\`\`qualified CUBA key\`\`** of a relationship to the following keywords:

  `target`
  > A class expression describing the individuals which are object of the relationship.

  `cardinality`
  > The number of times the `target` is allowed to be a object of the relationship.
  > To define the `cardinality` we use the following syntax:
  >
  > - many / * / 0+ (default): Zero to infinity target objects are allowed.
  > - \+ / 1+: At least one target object is required.
  > - ? / 0-1: At most one target object is allowed.
  > - a+: At least a target objects are required.
  > - a-b: At least a and at most b target objects are required (i.e. inclusive).
  > - a: Exactly a target objects are required.

  `only`
  > Whether the given `target` is the only allowed object.
- A composition of several class expressions. For example:

  ```yml
  OR:
    - CUBA.ELEMENTARY
    - CUBA.PHYSICAL
  ```

  This is the union of all individuals that are elementary or physical.
  We use the keyword `OR` for union, `AND` for intersection and `NOT` for complement.
  After `OR` and `AND`, a list of  class expressions for the union / intersection is expected.
  After `NOT` a single class expression is expected.

The definition of class expressions is recursive. For example:

```yml
OR:
  - CUBA.ELEMENTARY
  - CUBA.HAS_PROPER_PART:
      cardinality: 1+
      target: CUBA.PHYSICAL
      only: false
```

This describes the subset of all individuals that are elementary or have at least one physical as proper part.

## CUDS classes format

Every cuds class is a sub-entity of `CUDS_ENTITY`.
The declaration of a cuds entity is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format).
It can contain further information:

`values`: Dict[**\`\`qualified CUBA key\`\`**, default_value]
> Expects a mapping from the **\`\`qualified CUBA key\`\`** to its default. Each key must correspond to a sub-entity of `VALUE`. For example:
>
> ```yml
> ADDRESS:
>   ...
>   values:
>     CUBA.NAME: "Street"
>     CUBA.NUMBER:
> ```
>
> Here, an address has a name and a number.
> The default name is "Street", the number has no default.
> If no default is given, the user is forced to specify a value each time he creates an individual.

`restrictions`: List[Class expression]
> A list of class expressions that restrict the individuals allowed in the class. Only those
> individuals are allowed that are in the intersection of the class expressions. For example:
>
> ```yml
> PHYSICAL:
>   ...
>   restrictions:
>   - OR:
>       - CUBA.ELEMENTARY
>       - CUBA.HAS_PROPER_PART:
>           cardinality: 1+
>           target: CUBA.PHYSICAL
>           only: false
> ```
>
> Here, a physical must be either a elementary or must have at least one physical as proper part.

`disjoints`: List[Class expression]
> A list of class expressions that are not allowed to share any individuals with the cuds entity.

`equivalent_to`: List[Class expression]
> A list of class expressions who contain the same individuals as the cuds entity. For example:
>
> ```yml
> PHYSICAL:
>   ...
>   equivalent_to:
>   - OR:
>       - CUBA.ELEMENTARY
>       - CUBA.HAS_PROPER_PART:
>           cardinality: 1+
>           target: CUBA.PHYSICAL
>           only: false
> ```
>
> Here, every elementary or everything that has a physical as proper part is automatically considered a physical.
> Also, as in the example before, every physical must be either a elementary or must have at least one physical as proper part.

## Relationship format

Every relationship is a sub-entity of `RELATIONSHIP`.
The declaration of a relationship is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format).
Furthermore, it mus have the following keys:

`inverse`: **\`\`qualified CUBA key\`\`** or empty (None)
> Every relationship except `RELATIONSHIP` must have an inverse.
> If CUDS object A is related to CUDS object B via relationship REL, then B is related
> with A via the inverse of REL.
>
> For example: The inverse of HAS\_PART is IS\_PART\_OF.

`domain`: List[Class expression]
> A list of class expressions describing the individuals that are allowed to be a subject of the relationship.
> If multiple class expressions are given, the relationship's domain is the intersection of the class expressions.

`range`: List[Class expression]
> A list of class expression describing the individuals that are allowed to be object of the relationship.
> If multiple class expressions are given, the relationship's range is the intersection of the class expression.

`characteristics`:
> A list of characteristics of the relationship. The following characteristics are supported:
>
> - reflexive
> - symmetric
> - transitive
> - functional
> - irreflexive
> - asymmetric
> - inversefunctional

A sub-entity of a relationship is called a sub-relationship.

## Special relationships

`ACTIVE_RELATIONSHIP`:

> The sub-relationships of `ACTIVE RELATIONSHIP` define directed acyclic subgraphs in the graph of the ontology.
