# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import argparse
import os

from parser import Parser


class Cuds2Dot:
    """
    Class that parses a YAML file and finds information about the
    entities contained. It can also save it to a dot format file.
    """

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

    def create_dot_file(self):
        """
        Creates the dot file from the parsed YAML file.
        """
        dot = "digraph class_graph{\n"
        dot += "  node [shape = plaintext]\n"
        dot += "  rankdir = BT;\n"
        dot += "  splines = ortho;\n"
        self.add_elements_under_node()
        # Add the provided node(s)
        self._elements.update(self._node)
        # Check if empty, for the root there are no higher elements
        if self._node:
            self.add_elements_over_node()
        # Split the nodes and their relationships for better readability
        dot_attributes = "\n  // ----- Nodes and attributes -----\n"
        dot_relationships = "\n  // ----- Relationships -----\n"
        for item in self._elements:
            dot_attributes += "  " + self.attributes_to_dot(item)
            dot_relationships += "  " + self.relationships_to_dot(item)
        dot += dot_attributes
        dot += dot_relationships
        dot += "}"
        dot_file = open(os.path.splitext(self._filename)[0] + ".dot", "w")
        dot_file.write(dot)

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
                    if parent is "":
                        break
                    self._elements.add(parent)
                    current_level += 1

    def attributes_to_dot(self, item):
        """
        Generates the dot formatted string of an item with its attributes.

        :param item: item for which to compute and format the parameters
        :return: dot formatted string of the attributes
        """
        attributes = "\"" + item + "\"\n    [label=\n    <<table border='1' "
        attributes += "cellborder='0' cellspacing='0'>\n"
        attributes += "      <tr><td bgcolor='grey'>" + item + "</td></tr>\n"
        for att in self._parser.get_attributes(item, self._inheritance):
            attributes += "      <tr><td align='left' >" + att + "</td></tr>\n"
        attributes += "    </table>>];\n"
        return attributes

    def relationships_to_dot(self, item):
        """
        Dot formatted string of an item with the relationship to the parent.

        :param item: item for which to compute and format the parent
        :return: dot formatted string of the relationship with the parent
        """
        relationships = ""
        parent = self._parser.get_parent(item)
        if parent in self._elements:
            relationships += "\"" + item + "\" -> \"" + parent + "\";\n"
        return relationships


def main():
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
    parser = Cuds2Dot(args.filename, args.n, args.d, args.u, args.i)
    parser.create_dot_file()

    filename_clean = os.path.splitext(args.filename)[0]
    directory = os.path.dirname(args.filename)

    # Call the command to create the graph from the file
    command = "dot -Tpng " + filename_clean + ".dot -o " + filename_clean
    command += ".png"
    os.system(command)
    print(".png and .dot files successfully added to " + directory + "!")


if __name__ == "__main__":
    main()
