# Description of YAML format Specification

This is the YAML format currently supported by osp-core. It is not able to represent all aspects of the current EMMO version, so it might be updated in the future.

TODO naming of files

## Info

Contact: [Matthias Urban](mailto:matthias.urban@iwm.fraunhofer.de) and  [Pablo de Andres](mailto:pablo.de.andres@iwm.fraunhofer.de) from the 
Material Informatics team, Fraunhofer IWM.

Version: 2.0 pending approval

## Introduction

In this file we will give a description of how an Ontology can be
represented in a yaml file format and how to interpret such files. For
simplicity reasons in the following we will give examples from the
cuds\_ontology\_ontology\_city.yml file which can be found here **\*
provide the link to the file**\*.

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
> 1. strict: Error is raised as soon as any relationship is added, that
>    is not supported. Error is raised on commit if cardinalities are
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
> semantics. Should have the form: sub\_entity is a parent\_entity that
> has \<differentiating\> terms. (not sure about this)
>
`parent`: **\`\`qualified CUBA key\`\`** or empty (None).
> Its value is fixed on the ontology level.
>
> The parent CUDS is for inheritance relations, expressing an
> **ontological is-a** relation. MUST be either:
>
> - a fully qualified string referring to another CUDS entry.
> - or, an empty entry (yaml meaning: None), for the start of the
>   hierarchy (i.e. only for the cuds entry `ENTITY`, see [Special entities](#special-entities)).
>
> If entity B has parent A, we say that B is a sub-entity of A. \
> If entity D has parent C and C is is sub-entity of A,
> then D is also sub-entity of A.

An ontology entity can be either a relationship or a cuds entity or a value.
Depending on that the mapping can have further keys.
For cuds entities these keys are described in
[CUDS entities format](#cuds-entities-format) section.
For relationship entities, these keys are described in
[Relationship format](#relationship-format) section
For relationship entities, these keys are described in
[Value format](#value-format) section.

## Special entities

`ENTITY`
> The entity is the root of the ontology. It is the only entity which does not have a parent.
> Every other entity is a sub-entity of `ENTITY`.

`CUDS_ENTITY`
> This is the root for all entities that can have individuals. Its direct parent is `ENTITY`.

`RELATIONSHIP`
> This is the root of all relationships. Its direct parent is `ENTITY`.

`VALUE`
> This is the root of all values. A value is some kind of data, like a String or a Number. It can be an attribute of a cuds entity. Its direct parent is `ENTITY`.

## CUDS entities format

Every cuds entity is a sub-entity of `CUDS_ENTITY`.
The declaration of a cuds entity is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format).
Furthermore, it can contain information about its attributes and supported relationships.
The meaning of these supported relationships is determined by the `ONTOLOGY_MODE` described in section [Syntax of the .yml ontology](#syntax-of-the-.yml-ontology).

Supported relationships can be defined by giving the cuba-key of each supported
relationship as a key.
The value is a mapping from all allowed targets of the relationship to a mapping
that specifies details about the relationship to the target.
You can specify the `cardinality` of the relationship there.

`cardinality`: string/integer
> Gives a description (sometimes also limitation) of the number
> of times a relationship between two entities can occur. For example:
>
> ```yml
> CITY:
>   definition: ...
>   parent: CUBA.POPULATED_PLACE
>   CUBA.HAS_PART:
>     CUBA.NEIGHBOURHOOD:
>       cardinality: many
> ```

Here, a city can have many neighborhoods.

To define the `cardinality` we use the following syntax:

- many / * / 0+ (default): Zero to infinity target objects are allowed.
- \+ / 1+: At least one target object is required.
- ? / 0-1: At most one target object is allowed.
- a+: At least a target objects are required.
- a-b: At least a and at most b target objects are required (i.e. inclusive).
- a: Exactly a target objects are required.

The attributes of the cuds entity are sub entities of `VALUE`.
They can be specified similarly as supported relationships by skipping
the specification of the relationship. Instead of the cardinality a `default`
can be specified.

`default`: string/integer
> Gives a default value to an entity. For example:
>
> ```yml
> ADDRESS:
>   definition: ...
>   parent: CUBA.ENTITY
>   CUBA.NAME:
>     default: "Street"
>   CUBA.NUMBER:
>    ```

Here, an address has a name and a number. The default name is "Street", the number has no default. If no default is given, the user is forced to specify a value each time he creates an individual.

## Relationship format

Every relationship is a sub-entity of `RELATIONSHIP`.
The declaration of a relationship is a special case of the declaration of an entity.
It must have the keys described in [Ontology entities format](#ontology-entities-format).
Furthermore, it mus have the following keys:

`inverse`: **\`\`qualified CUBA key\`\`** or empty (None)
> Every (not sure about this) relationship except `RELATIONSHIP` must have an inverse.
> If CUDS object A is related to CUDS object B via relationship REL, then B is related
> with A via the inverse of REL.
>
> For example: The inverse of HAS\_PART is IS\_PART\_OF.

A sub-entity of a relationship is called a sub-relationship.

## Special relationships

`ACTIVE_RELATIONSHIP`:
> Is an entity the parent of which is RELATIONSHIP and the inverse is
> PASSIVE\_RELATIONSHIP. It has all the keys mentioned above.

`PASSIVE_RELATIONSHIP`:
> Is an entity the parent of which is RELATIONSHIP and the inverse is
> ACTIVE\_RELATIONSHIP. It has all the keys mentioned above.

The inverse of any sub-relationship of `ACTIVE RELATIONSHIP` must be a sub-relationship of `PASSIVE_RELATIONSHIP` and vice verse.

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
> - BOOL: a form of data with only two possible values (usually
>   \"true\" or \"false\")
> - INT: a sequence of positive and negative digits
> - FLOAT: a digit containing values on both sides of the decimal
>   point
> - STRING: a set of characters that can also contain spaces and
>   numbers. The length of the string can be specified as follows:
>   STRING:20, meaning the length of the string should be 20
>   characters.
>
> In case a datatype is not specified the default datatype is assumed to
> be STRING
>
> For example: The datatype of entity NUMBER is INT.
