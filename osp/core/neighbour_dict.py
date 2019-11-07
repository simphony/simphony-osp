# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import uuid
from osp.core.ontology.relationship import OntologyRelationship
from osp.core.ontology.oclass import OntologyClass


class NeighbourDict(dict):
    """A dictionary that notifies the session if
    any update occurs. Used to map uids to entitys
    for each relationship.
    """

    def __init__(self, dictionary, cuds_object, key_check, value_check):
        self.cuds_object = cuds_object
        self.key_check = key_check
        self.value_check = value_check

        invalid_keys = [k for k in dictionary.keys()
                        if not self.key_check(k)]
        if invalid_keys:
            raise ValueError("Invalid keys %s" % invalid_keys)
        invalid_values = [v for v in dictionary.values()
                          if not self.value_check(v)]

        if invalid_values:
            raise ValueError("Invalid values %s" % invalid_values)
        super().__init__(dictionary)

    def __iter__(self):
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return super().__iter__()

    def __getitem__(self, key):
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if not self.value_check(value):
            raise ValueError("Invalid value %s" % value)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        super().__setitem__(key, value)
        if self.cuds_object.session:
            self.cuds_object.session._notify_update(self.cuds_object)

    def __delitem__(self, key):
        if not self.key_check(key):
            raise ValueError("Invalid key %s" % key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_read(self.cuds_object)
        super().__delitem__(key)
        if self.cuds_object.session:
            self.cuds_object.session._notify_update(self.cuds_object)

    def update(self, E):
        self.cuds_object.session._notify_read(self.cuds_object)
        super().update(E)
        self.cuds_object.session._notify_update(self.cuds_object)


class NeighbourDictRel(NeighbourDict):
    def __init__(self, dictionary, cuds_object):
        super().__init__(
            dictionary, cuds_object,
            key_check=lambda k: isinstance(k, OntologyRelationship),
            value_check=lambda v: isinstance(v, NeighbourDictTarget)
        )


class NeighbourDictTarget(NeighbourDict):
    def __init__(self, dictionary, cuds_object, rel):
        self.rel = rel
        for uid, entity in dictionary.items():
            cuds_object._check_valid_add(entity, rel)
        super().__init__(
            dictionary, cuds_object,
            key_check=lambda k: isinstance(k, uuid.UUID),
            value_check=lambda v: isinstance(v, OntologyClass)
        )

    def __setitem__(self, uid, entity):
        self.cuds_object._check_valid_add(entity, self.rel)
        return super().__setitem__(uid, entity)
