import yaml


class Parser:
    """
    Class that parses a YAML file and finds information about the entities
    contained.
    """

    def __init__(self, filename):
        """
        Constructor. Sets the filename.

        :param filename: name of the YAML file with the ontology
        """
        self._filename = filename
        self._ontology = {}
        self.parse()
        self._entities = frozenset(self._ontology.keys())

    def parse(self):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        with open(self._filename, 'r') as stream:
            try:
                self._ontology = yaml.load(stream)['CUDS_ONTOLOGY']
            except yaml.YAMLError as exc:
                print(exc)

    def get_entities(self):
        """
        Returns the entities in the ontology.

        :return: list(str) of the classes' names in the ontology
        """
        return self._ontology.keys()

    def get_definition(self, entity):
        """
        Getter for the definition associated to an entity.

        :param entity: entity whose definition to return
        :return: str with the definition
        """
        definition = self._ontology[entity]['definition']
        return definition if definition is not None else "To Be Determined"

    def get_parent(self, entity):
        """
        Computes the parent of an entity, if there is one.

        :param entity: entity whose parent to return
        :return: name of the parent class
        :raises KeyError: the queried entity does not exist
        """
        try:
            parent = self._ontology[entity]['parent']
        except KeyError:
            message = '{!r} does not exist. Try again.'
            raise KeyError(message.format(entity))
        # Erase "CUBA." prefix
        parent = "" if parent is None else parent.replace("CUBA.", "")
        return parent

    def get_attributes(self, entity, inheritance=True):
        """
        Computes a list of attributes of an entity.

        If inheritance is set, it will add the attributes from the parents

        :param entity: entity that has the wanted attributes
        :param inheritance: whether inherited attributes should be added or not
        :return: sorted list with the names of the attributes
        """
        attributes = self.get_own_attributes(entity)
        if inheritance:
            inherited = self.get_inherited_attributes(entity)
            attributes.update(inherited)
        return sorted(attributes)

    def get_own_attributes(self, entity):
        """
        Creates a list with the attributes particular to an entity.

        :param entity: entity whose own attributes should be computed
        :return: list of the names of the attributes
        """
        own_attributes = set()
        for key in self._ontology[entity].keys():
            key = key.replace("CUBA.", "")
            if key in self._entities:
                own_attributes.add(key.lower())
        return own_attributes

    def get_inherited_attributes(self, entity):
        """
        Creates a list with the attributes obtained through inheritance.

        :param entity: entity whose inherited attributes should be computed
        :return: list of the names of the inherited attributes
        """
        ancestors = self.get_ancestors(entity)
        attributes = set()
        for ancestor in ancestors:
            attributes_ancestor = self.get_own_attributes(ancestor)
            if attributes_ancestor:
                attributes.update(attributes_ancestor)
        return attributes

    def get_ancestors(self, leaf_entity):
        """
        Computes all the entities above a given one.
        
        :param leaf_entity: entity at the base
        :return: list(str) with the parent entity and its parent until the root
        """
        ancestors = []
        parent = self.get_parent(leaf_entity)
        while parent != "":
            ancestors.append(parent)
            parent = self.get_parent(parent)
        return ancestors

    def get_descendants(self, root_entity):
        """
        Computes all the entities under a given one.

        :param root_entity: entity at the top
        :return: list(str) with the child entity and its child until the leaf
        """
        descendants = [root_entity]
        for entity in self.get_entities():
            # Set the root_entity to the initial parent for the loop
            parent = entity
            while parent != "":
                parent = self.get_parent(parent)
                if parent in descendants:
                    descendants.append(entity)
                    break
        return descendants
