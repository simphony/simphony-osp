# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import argparse
import os
import graphviz

from cuds.ontology.tools.parser import Parser


class Cuds2Dot:
    """
    Class that parses a YAML file and finds information about the
    entities contained. It can also save it to a dot format file.
    """
    entity_header = ("<<TABLE BORDER='1' CELLBORDER='0' CELLSPACING='0'>"
                     "<TR><TD BGCOLOR='grey'>{}</TD></TR>"  # For the entity
                     "{}"  # For the attributes
                     "</TABLE>>")
    entity_attribute = "<TR><TD ALIGN='left' >{}</TD></TR>"

    def __init__(self, filename, node, depth=-1, height=-1, inheritance=False):
        """
        Constructor. Receives the name of the file with the ontology.

        :param filename: name of the YAML file with the ontology
        :param node: set with the nodes to be represented
        :param depth: starting from given node(s), of elements to graph (down)
        :param height: starting from given node(s), of elements to graph (up)
        :param inheritance: whether to show the inherited attributes or not
        """
        self._filename = filename
        self._parser = Parser(self._filename)
        self._node = node if node is not None else set()
        self._depth = depth
        self._height = height
        self._inheritance = inheritance
        self._elements = set()
        self._graph = self._initialise_graph()

    def _initialise_graph(self):
        """Initialises a directed graph with some default settings"""
        filename = os.path.splitext(self._filename)[0] + ".dot"
        graph = graphviz.Digraph(format='png',
                                 filename=filename)
        graph.graph_attr['rankdir'] = 'BT'
        graph.graph_attr['splines'] = 'ortho'
        graph.node_attr['shape'] = 'plaintext'

        return graph

    def create_dot_file(self):
        """
        Creates the dot file from the parsed YAML file.
        """
        self.add_elements_under_node()
        # Add the provided node(s)
        self._elements.update(self._node)
        # Check if empty, for the root there are no higher elements
        if self._node:
            self.add_elements_over_node()
        for item in self._elements:
            self.attributes_to_dot(item)
            self.relationships_to_dot(item)
        self._graph.render()

    def add_elements_under_node(self):
        """
        Filters the elements to be considered based on the node and depth.
        """
        for entity in self._parser.get_entities():
            current_level = 0
            # Set the entity to the initial parent for the loop
            parent = entity
            while True if self._depth == -1 else current_level < self._depth:
                parent = self._parser.get_parent(parent)
                # Add all if there are no nodes specified
                if not self._node:
                    if parent == "":
                        self._elements.add(entity)
                elif parent in self._node:
                    self._elements.add(entity)
                    break
                if parent == "":
                    break
                current_level += 1

    def add_elements_over_node(self):
        """
        Filters the elements to be considered based on the node and height.
        """
        for node in self._node:
            if self._height == -1:
                self._elements.update(self._parser.get_ancestors(node))
            else:
                current_level = 0
                parent = node
                while current_level < self._height:
                    parent = self._parser.get_parent(parent)
                    if parent == "":
                        break
                    self._elements.add(parent)
                    current_level += 1

    def attributes_to_dot(self, item):
        """
        Adds the node with an item with its attributes.

        :param item: item for which to compute and format the parameters
        """
        attributes = ""
        for att in self._parser.get_attributes(item, self._inheritance):
            attributes += self.entity_attribute.format(att)
        node = self.entity_header.format(item, attributes)
        self._graph.node(item, node)

    def relationships_to_dot(self, item):
        """
        Adds the edge from item to its parent.

        :param item: item for which to compute and format the parent
        """
        parent = self._parser.get_parent(item)
        if parent in self._elements:
            self._graph.edge(item, parent)


def main():
    """ Main function to run Cuds2Dot as a script. """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("filename", help="Input YAML file")
    arg_parser.add_argument("-n", help="node(s) to be inspected", type=str,
                            nargs='*', default=[])
    arg_parser.add_argument("-d", help="depth of the nodes to show", type=int,
                            default=-1)
    arg_parser.add_argument("-u", help="height of the nodes to show", type=int,
                            default=-1)
    arg_parser.add_argument("-i", help="show inheritance of properties",
                            action="store_true", default=False)
    args = arg_parser.parse_args()

    # Convert to upper case the root(s)
    args.n = {word.upper() for word in args.n}

    # Create the object
    try:
        parser = Cuds2Dot(args.filename, args.n, args.d, args.u, args.i)
        parser.create_dot_file()

        directory = os.path.dirname(args.filename)
        print(".png and .dot files successfully added to " + directory + "!")
    except Exception:
        print("An unexpected error occurred. Exiting.")


if __name__ == "__main__":
    main()
