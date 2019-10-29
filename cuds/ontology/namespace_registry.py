# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import os
import pickle
import cuds

ONTOLOGY_NAMESPACE_REGISTRY = None
MAIN_ONTOLOGY_NAMESPACE = "CUBA"
MAIN_ONTOLOGY_PATH = os.path.join("yml", "ontology.cuba.yml")
INSTALLED_ONTOLOGY_PATH = os.path.join("installed.pkl")
CORE_PACKAGE = cuds


class NamespaceRegistry():
    def __init__(self):
        assert ONTOLOGY_NAMESPACE_REGISTRY is None
        self._namespaces = dict()

    def __getattr__(self, name):
        return self.get(name)

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name):
        return self._namespaces[name]

    def add_namespace(self, namespace):
        """Add a namespace to the registry

        :param namespace: The namespace to add
        :type namespace: OntologyNamespace
        :raises ValueError: The namespaces added first must have name CUBA
        """
        from cuds.ontology.namespace import OntologyNamespace
        assert isinstance(namespace, OntologyNamespace)
        self._namespaces[namespace.name] = namespace
        setattr(CORE_PACKAGE, namespace.name, namespace)

    def get_main_namespace(self):
        """Get the main namespace (CUBA)

        :return: The main namespace
        :rtype: OntologyNamespace
        """
        return self._namespaces[MAIN_ONTOLOGY_NAMESPACE]


# initialize registry singleton
if ONTOLOGY_NAMESPACE_REGISTRY is None:

    # load from installation
    if os.path.exists(INSTALLED_ONTOLOGY_PATH):
        with open(INSTALLED_ONTOLOGY_PATH, "rb") as f:
            ONTOLOGY_NAMESPACE_REGISTRY = pickle.load(f)

    else:  # parse main ontology
        from cuds.ontology.parser import Parser
        ONTOLOGY_NAMESPACE_REGISTRY = NamespaceRegistry()
        p = Parser()
        path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(path, MAIN_ONTOLOGY_PATH)
        namespace = p.parse(path)
