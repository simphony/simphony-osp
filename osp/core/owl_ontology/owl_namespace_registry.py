# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import logging

logger = logging.getLogger(__name__)

MAIN_ONTOLOGY_NAMESPACE = "CUBA".lower()
MAIN_ONTOLOGY_PATH = os.path.join(os.path.dirname(__file__),
                                  "yml", "ontology.cuba.yml")


class NamespaceRegistry():
    def __init__(self):
        self._namespaces = dict()

    def __iter__(self):
        """Iterate over the installed namespace.

        :return: An iterator over the namespaces.
        :rtype: Iterator[OntologyNamespace]
        """
        return iter(self._namespaces.values())

    def __getattr__(self, name):
        try:
            return self._get(name)
        except KeyError as e:
            raise AttributeError(str(e)) from e

    def __getitem__(self, name):
        return self._get(name)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __contains__(self, other):
        if isinstance(other, str):
            return other.lower() in self._namespaces.keys()
        return other in self._namespaces.values()

    def get(self, name, fallback=None):
        try:
            return self._get(name)
        except KeyError:
            return fallback

    def _get(self, name):
        try:
            return self._namespaces[name.lower()]
        except KeyError as e:
            raise KeyError("namespace %s not installed" % name) from e

    @property
    def default_rel(self):
        """Get the default relationship.

        :return: The default relationship.
        :rtype: OntologyRelationship
        """
        logger.warning("namespace_registry.default_rel() is deprecated!")
        rels = list()
        for namespace in self._namespaces.values():
            if namespace.default_rel is not None:
                rels.append(namespace.default_rel)
        if len(rels) == 1:
            return rels[0]

    def set_namespaces(self, namespaces, namespace_module=None):
        """Add a namespace to the registry

        :param namespace: The namespace to add
        :type namespace: OntologyNamespace
        :raises ValueError: The namespaces added first must have name CUBA
        """
        # TODO handle CUBA
        # from osp.core.ontology.namespace import OntologyNamespace
        # assert isinstance(namespace, OntologyNamespace)
        # assert (
        #     bool(namespace.name.lower() == MAIN_ONTOLOGY_NAMESPACE)
        #     != bool(self._namespaces)
        # ), ("CUBA namespace must be installed first. "
        #     "Installing %s. Already installed: %s"
        #     % (namespace.name, self._namespaces.keys()))
        self._namespaces = dict()
        for namespace in namespaces:
            if namespace.name.lower() in self._namespaces:
                raise ValueError("Namespace %s already added to namespace "
                                 "registry!" % namespace.name)
            self._namespaces[namespace.name.lower()] = namespace
            if namespace_module is None:
                import osp.core.namespaces as namespace_module
            setattr(namespace_module, namespace.name.upper(), namespace)
            setattr(namespace_module, namespace.name.lower(), namespace)

    # def get_main_namespace(self):
    #     """Get the main namespace (CUBA)

    #     :return: The main namespace
    #     :rtype: OntologyNamespace
    #     """
    #     return self._namespaces[MAIN_ONTOLOGY_NAMESPACE]
