# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

ONTOLOGY_NAMESPACE_REGISTRY = None
MAIN_ONTOLOGY_NAMESPACE = "CUBA"


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
        if not self._namespaces and namespace.name != MAIN_ONTOLOGY_NAMESPACE:
            raise ValueError("Namespace of the main ontology needs to be "
                             + MAIN_ONTOLOGY_NAMESPACE)
        self._namespaces[namespace.name] = namespace

    def get_main_namespace(self):
        """Get the main namespace (CUBA)

        :return: The main namespace
        :rtype: OntologyNamespace
        """
        return self._namespaces[MAIN_ONTOLOGY_NAMESPACE]


ONTOLOGY_NAMESPACE_REGISTRY = NamespaceRegistry()
