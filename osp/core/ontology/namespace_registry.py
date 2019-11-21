# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import pickle  # nosec
import os

ONTOLOGY_NAMESPACE_REGISTRY = None
MAIN_ONTOLOGY_NAMESPACE = "CUBA".lower()
MAIN_ONTOLOGY_PATH = os.path.join(os.path.dirname(__file__),
                                  "yml", "ontology.cuba.yml")
INSTALLED_ONTOLOGY_PATH = os.path.join(os.path.dirname(__file__),
                                       "installed-ontology.pkl")


class NamespaceRegistry():
    def __init__(self):
        self._namespaces = dict()

    def __getattr__(self, name):
        try:
            return self.get(name)
        except KeyError:
            raise AttributeError(name)

    def __getitem__(self, name):
        return self.get(name)

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__ = state

    def __contains__(self, other):
        if isinstance(other, str):
            return other.lower() in self._namespaces.keys()
        return other in self._namespaces.values()

    def get(self, name):
        return self._namespaces[name.lower()]

    @property
    def default_rel(self):
        """Get the default relationship.

        :return: The default relationship.
        :rtype: OntologyRelationship
        """
        rels = list()
        for namespace in self._namespaces.values():
            if namespace.default_rel is not None:
                rels.append(namespace.default_rel)
        if len(rels) == 1:
            return rels[0]

    def _add_namespace(self, namespace):
        """Add a namespace to the registry

        :param namespace: The namespace to add
        :type namespace: OntologyNamespace
        :raises ValueError: The namespaces added first must have name CUBA
        """
        from osp.core.ontology.namespace import OntologyNamespace
        assert isinstance(namespace, OntologyNamespace)
        assert (
            bool(namespace.name.lower() == MAIN_ONTOLOGY_NAMESPACE)
            != bool(self._namespaces)
        ), "CUBA namespace must be installed first"
        if namespace.name.lower() in self._namespaces:
            raise ValueError("Namespace %s already added to namespace "
                             "registry!" % namespace.name)
        self._namespaces[namespace.name.lower()] = namespace

        if (
            ONTOLOGY_NAMESPACE_REGISTRY is self
            and namespace.name.lower() != MAIN_ONTOLOGY_NAMESPACE
        ):
            import osp.core
            setattr(osp.core, namespace.name.upper(), namespace)
            setattr(osp.core, namespace.name.lower(), namespace)

    def get_main_namespace(self):
        """Get the main namespace (CUBA)

        :return: The main namespace
        :rtype: OntologyNamespace
        """
        return self._namespaces[MAIN_ONTOLOGY_NAMESPACE]

    def install(self):
        """Reset the namespace registry"""
        with open(INSTALLED_ONTOLOGY_PATH, "wb") as f:
            pickle.dump(self, f)


# initialize registry singleton
if ONTOLOGY_NAMESPACE_REGISTRY is None:

    # load from installation
    try:
        if os.path.exists(INSTALLED_ONTOLOGY_PATH):
            with open(INSTALLED_ONTOLOGY_PATH, "rb") as f:
                ONTOLOGY_NAMESPACE_REGISTRY = pickle.load(f)  # nosec
    except EOFError:
        pass

if ONTOLOGY_NAMESPACE_REGISTRY is None:
    from osp.core.ontology.parser import Parser
    ONTOLOGY_NAMESPACE_REGISTRY = NamespaceRegistry()
    p = Parser()
    namespace = p.parse(MAIN_ONTOLOGY_PATH)
