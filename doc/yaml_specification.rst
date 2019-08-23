Description of YAML format Specification
========================================

Specification version: 1.90

**Status: Unstable, in development**

This document describes the specification of the format of the metadata description.
It is not meant to describe the concept of CUBA and CUDS or the ontology, these ar given elsewhere.
It merely  describes the logic on the YAML level.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL
NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED",  "MAY", and
"OPTIONAL" in this document are to be interpreted as described in
RFC 2119. [1]_


Changelog
---------

- Initial release (Stefano Borini ENT, Adham Hashibon IWM)
- Second Release for FORCE (Adham Hashibon). Working unstable specs.


Format description
------------------

The format is defined in one yaml format file:

- ontology_stable.yml: Describes the ontology and a mapping of the ontology objects to data models and relations and links
  to other objects, either as specialization or relationships.

The file format is case sensitive, the keys described in this format specification MUST be interpreted as case sensitive.


Terminology
-----------

The following terms are used in relation to the SimPhoNy ontology and metadata description:

- ``class``: an entity, a thing, a class in the ontology and corresponding data structure.
  Example: the Lennard Jones potential, a vector, a mode, etc.
- ``CUDS``: a Common Universal Data Structure, an entity that encodes an ontology ``Class``
  (sometimes called a concept) in the metadata.
- ``CUBA`` : a Common Universal Basic Attribute signifying a specific unique vocabulary to defined a CUDS class,
  it is the term used to define the class.
- ``CUBA Key``: the actual vocabulary in the yml specifications is referred to as the CUBA Key.


Characteristics and rules
--------------------------

The ``CUBA`` has the following characteristics:

- the vocabulary must be unique for each CUDS entity, and designates its meaning.
- it is the same as used in the ontology, where multiple keywords are joined by underscores ``_``,
  example ``LENNARD_JONES_6_12``.
- underscores should not be used as "name space" replacement, they are used only when necessary
  as part of the name of one entity.
- ``CUBA.`` (CUBA and a dot) is used as a prefix for already defined CUDS entity. See below.
- ``CUDS entity``: a concrete entity we define to represent a ``class`` that has relationships with other concepts.


The ``CUDS entity`` has the following characteristics:

- a unique vocabulary term defining its type (e.g. LENNARD_JONES_6_12), which is a CUBA.
- a unique identifier (e.g. a UUID which is going to be different for two distinct instances of a Lennard Jones potentials)
  to be able to distinguish specific instances of the ``CUDS entity``.
- is a ``container``: It contains semantic information in the form of other entities.
- a set of basic properties that are expressed as relations to other ``classes`` and to data model entities (the basic metadata).


Two types of ``CUDS entity`` properties exist:

- ``Class level fixed properties with instant level values``: Properties that depend only on the CUDS class type
  but may have values that are different for instances.
- ``Class level fixed properties and  properties``: Properties and values that are fixed at the ontology and class level.


The following terms are used in the remainder of this document and are prescriptive:

- ``(non-qualified) CUBA Key``: a fully capitalized, underscored name to refer to a CUDS entity
  (e.g. COMPUTATIONAL_MODEL).
- ``qualified CUBA key``: a CUBA key prefixed with the ``CUBA.`` string (e.g. CUBA.COMPUTATIONAL_MODEL).
- ``CUDS entry``: an entry defined in the simphony_stable.yml file under CUDS_ENTITY that represents a CUDS class.


``cuba.yml``
------------
*This file is removed, its content is replaced by the determinant branch of SimPhoNy-2.0 ontology-simphony_metadata*


``ontology_stable.yml`` Syntax
-------------------------------

The format MUST have a root level mapping with the following keys:

- ``VERSION``: string

  Contains semantic version Major.minor in format M.m with M and m positive integers.
  minor MUST be incremented when backward compatibility in the format is preserved.
  Major MUST be incremented when backward compatibility is removed.
  Due to the strict nature of the format, a change in minor is unlikely.

  **NOTE** that this is the version of the file format, _NOT_ of the described information (CUDS).
  the addition of new CUDS entries will not require a version change, as long as the layout of the file
  complies with the standard.

  **NOTE**: The value must be explicitly quoted, as it would otherwise be interpreted
  by the yaml parser as a floating point value.

- ``CUDS``:  string

  Defines the type entities. The content is a free format string whose value has no semantic meaning.
  It can be used as a comment.

- ``Purpose``: string

  For human consumption. Free format string to describe the contents of the file.

- ``Resources``: string

  For human consumption. A mapping between a user meaningful entity and a string describing that entity,
  for example a link to a spec or an email address.

- ``comment``:

  To be rendered as a URI in next versions.

- ``CUDS_ONTOLOGY``:

  Contains individual declarations for CUDS entities, in the form of CUDS entries.
  Each key of the mapping is the name of a CUDS entry (the CUBA).

  The **Key MUST be all uppercase**, with underscore as separation. Numbers are not allowed.

  Each value of the mapping is a mapping whose format is detailed in the "CUDS entities format" section.


CUDS entries format
~~~~~~~~~~~~~~~~~~~

Each ``CUDS entry`` MUST contain a mapping.  The keys of the mapping represent properties of the ``CUDS Item``.

- ``class attributes`` use simple, lowercase names as keys and are attributes.
- ``Optional contained entities`` use ``qualified CUBA key`` as keys.
  These are hints on entities  that the CUDS entity (the container) can or must contain to exist
  and fulfill its intended functionality, or give additional semantic information.

The following ``Class attributes`` keys MUST be present:

- ``parent``: **``qualified CUBA key``** or empty (None). Its value is fixed on the ontology level.

  The parent CUDS is for inheritance relations, expressing an **ontological is-a** relation. MUST be either:

  - a fully qualified string referring to another CUDS entry. for example::

        parent: CUBA.PAIR_POTENTIAL


  - or, an empty entry (yaml meaning: None), for the start of the hierarchy (parentless).


Apart from the above keys, other class attribute keys MAY be present, and their content is specified in
"Class attributes format". They represent attributes whose value is either fixed and hardcoded on the class level
(class properties) or in real time by the instance.

These class attributes have particular semantic meaning and are commonly used.
Refer to "Semantic rules" for additional information.

The entry MAY contain optional properties in the form:

- **qualified CUBA key**: mapping
  Describe the existence of an ontological general **has-a** relation toward a specified ``CUDS entity``
  expressed as a SimPhoNy composition rule. Each key:

  - MUST be a ``qualified CUBA key``.
  - MUST have been defined in the ontology file.
  - SHOULD be specified only once in the ``CUDS entry`` (by nature of the mapping,
    only the last entry will be used).
  - when converted to non-qualified lowercase, MUST NOT be equal to a ``fixed property`` key.

for example:

.. code:: yaml

         PHYSICS_BASED_MODEL:
            definition: solvable set of one physics equation and one or more materials relations
            parent: CUBA.PHYSICS_BASED_EQUATION
            CUBA.PHYSICS_EQUATION:
                shape: (1)
            CUBA.MATERIAL_RELATION:
                shape: (:)

Is interpreted as: a PHYSICS_BASED_MODEL should contain one instance of a CUBA.PHYSICS_EQUATIONS, and one or more instances of CUBA.MATERIAL_RELATION.

``comment``: This is candidate to be removed for a new class attribute property:
"can_contain" and "must_contain", "cannot_contain", etc. if needed.


Class attribute entries format
--------------------------------

The content of a class attribute property can be either a mapping, or some other entity. In the case
of a mapping the following keys MAY be present:

- ``scope``: string

  Controlled dictionary. Allowed strings:

  - ``CUBA.USER``: Default if not specified. Indicates that this
    property is available for setting at construction. Its initial
    value is the appropriate default.
  - ``CUBA.SYSTEM``: Indicates that this property cannot be specified
    by the user (i.e. is not available for setting at construction)
    and its value is set by internal code. If this key is present,
    the ``default`` key MUST NOT be present. The generator will use
    the associated Property key to produce the appropriate
    initialization code. Examples of these properties are the
    Fixed property ``data`` and the Variable property CUBA.UID.


Class attributes of Data types
------------------------------
``comment``: this is WIP, need review.

A major difference form version 1.0 is the inclusion of explicit data types (data model) that defines
REAL, INTEGER, STRING, VECTOR, TENSOR, and other related data type entities as part of the ontology.
These are used for the specification of the data type a specific value of a determinable entity can have.
They can be specified on the level of the ontology and classes to have default values,
and to have a specific range of values.

- ``default``: any

  Indicates the hardcoded default value for the property.
  The value is used as specified and one of the following can be present:

  - ``scope`` is ``CUBA.SYSTEM``, if present indicates a value that cannot change by the user.
  - ``scope`` is ``CUBA.USER``, this entry indicates the user present.

  Only one scope can be present.

If the content is not a mapping (e.g. string, list, numerical value), it is interpreted
as equivalent to a mapping-type specification where:

- ``default`` is the specified entity.
- ``scope`` is ``CUBA.USER``.
- ``shape``: sequence of positive ints or "colon" notation. **Can only be used for CUBA.DATA_TYPE**
  Specifies the shape of the container holding the contained value. Default is the list [1]. Examples:

  - ``[3]`` : A vector of three entities.
  - ``[3,3]`` : array of 3x3 CUBA entities.

  To define arrays of arbitrary length on one or multiple dimensions, the following "colon" notation is used.
  Note that parentheses are used instead of square brackets. This is due to how the colon would be interpreted
  by the yaml parser:

  - ``(:,:)`` : an arbitrary size matrix.
  - ``(3,:)`` : a 3xn matrix.
  - ``(:)`` : an arbitrary size vector.

- ``range``: indicates the possible range of types the property can take and must be a subclass of the property type.
  Used for Determinables to specify that subtypes of data type should be used.


Semantic format
---------------

Semantic rules
~~~~~~~~~~~~~~

This section details additional requirements that go beyond the low level file format, but should be considered
by the parser to validate the final format.

- ``CUDS parent``:

  - The file MUST contain one and only one parentless entry.
  - There MUST NOT be loops in the hierarchy.

- ``CUDS properties defaults``:
  When specifying a CUDS property (e.g. CLASS_A) default and the default is non-trivial (e.g. None)
  it MUST refer to a subclass (e.g. CLASS_A1) of the property type. In other words:

.. code:: yaml

        CLASS_A:
            parent: CUBA.SOMETHING

        CLASS_A1:
            parent: CUBA.CLASS_A

        CLASS_A2:
            parent: CUBA.CLASS_A

        CLASS_C:
            parent: CUBA.SOMETHING_ELSE
            CLASS_A:
                default: CLASS_A1


- ``CUDS properties defaults``:
  When specifying a CUDS property (e.g. CLASS_A) as range it MUST refer to a subclass of a DATA_TYPE as
  CUBA.REAL. CUBA.VECTOR, etc.

.. code:: yaml

        TIME:
            definition: A time quality, in units with origin t=0
            parent: CUBA.PHYSICAL_QUALITY
            CUBA.VALUE:
                range: CUBA.REAL


This means the TIME instance (a determinant) will have a .value attribute that accepts only REAL, and exactly REAL.

Semantically defined fixed property keys and their contents:

- ``definition``: string

  For human consumption. An ontological short description of the carried semantics. Should have the form:
  sub_entity is a parent_entity that has <differentiating> terms, example:

.. code:: yaml

        APPLE:
            parent: CUBA.FRUIT
            definition: An apple is a fruit that is sweet, edible and produced by an apple tree.


Parser behavior
---------------

An error MUST be reported, and parsing stopped when the following circumstances occur:

- non-compliance with the yaml format.
- non-compliance with the format described in this specification.
- Unrecognized keys.
- Duplicated keys.
- Violation of semantic rules.


Final notes
-----------
- Regarding the strings mentioned above:

  - They may only contain standard ASCII characters (no extended characters like ä, ö, ñ...).

  - The use of the colon ``:`` is also restricted, and it should not appear on a string

References
----------
.. [1] https://www.ietf.org/rfc/rfc2119.txt
