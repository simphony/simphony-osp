# Copyright (c) 2014-2019, Adham Hashibon, Materials Informatics Team,
# Fraunhofer IWM and Didrik Pinte, ENTHOUGHT Inc.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.


class RelationshipTree(dict):
    """
    A datastructure to store the relationships of a Cuds object hierarchically.
    """

    def __init__(self, root_relationship, children=None):
        """Initialize the datastructure.

        :param root_relationship: The root of this tree.
        :type root_relationship: Relationship.
        """
        self.root_relationship = root_relationship
        self.children = children or dict()

    def add(self, relationship):
        """Add the given relationship to the tree.

        :param relationship: The relationship to add.
        :type relationship: Relationship.
        """
        ancestor_rel = self._get_ancestor_rel(relationship)

        if ancestor_rel is None:
            self._add(relationship)
        elif ancestor_rel is not relationship:
            self.children[ancestor_rel].add(relationship)

    def remove(self, relationship):
        """Remove the given relationship from the tree.

        :param relationship: The relationship to remove.
        :type relationship: Relationship.
        :raises KeyError: Given relationship not found in the tree.
        """
        ancestor_rel = self._get_ancestor_rel(relationship)
        if ancestor_rel is relationship:
            self.children.update(self.children[ancestor_rel].children)
            del self.children[ancestor_rel]
        elif ancestor_rel is not None:
            self.children[ancestor_rel].remove(relationship)
        else:
            raise KeyError(("Cannot remove relationship %s,"
                            + "because it is not in the tree") % relationship)

    def get_subrelationships(self, relationship):
        """Get all relationships that are subclasses of the given relationship.

        :param relationship: Get all subclasses of this relationship.
        :type relationship: Relationship.
        :return: Set of subrelationships of the given relationship.
        :rtype: Set[Relationship]
        """
        ancestor_rel = self._get_ancestor_rel(relationship)
        predecessor_rels = self._get_predecessor_rels(relationship)

        if ancestor_rel is not None and not predecessor_rels:
            return self.children[ancestor_rel]. \
                get_subrelationships(relationship)

        result = set()
        for predecessor_rel in predecessor_rels:
            result |= self.children[predecessor_rel]._get_subrelationships()
        return result

    def _add(self, relationship):
        children = {subtree.root_relationship: subtree
                    for subtree in self.children.values()
                    if issubclass(subtree.root_relationship, relationship)}
        self.children[relationship] = RelationshipTree(relationship,
                                                       children=children)
        for child in children:
            del self.children[child]

    def _get_subrelationships(self):
        """Get all the relations that are subclasses of this tree's root.

        :return: The set of subrelationships.
        :rtype: Set[Relationship]
        """
        result = set([self.root_relationship])
        for child in self.children.values():
            result |= child._get_subrelationships()
        return result

    def _get_ancestor_rel(self, relationship):
        """Get the relationship of all the direct children of this node,
        that is a ancestor of the given relationship

        :param relationship: Get the ancestors of this relationship
        :type relationship: Relationship
        :return: The ancestor relationship or None, of none found
        :rtype: Relationship
        """
        for rel in self.children.keys():
            if issubclass(relationship, rel):
                return rel
        return None

    def _get_predecessor_rels(self, relationship):
        """Get the relationship of all the direct children of this node,
        that is a ancestor of the given relationship

        :param relationship: Get the ancestors of this relationship
        :type relationship: Relationship
        :return: The ancestor relationship or None, of none found
        :rtype: Relationship
        """
        result = []
        for rel in self.children.keys():
            if issubclass(rel, relationship):
                result.append(rel)
        return result
