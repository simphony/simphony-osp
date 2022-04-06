"""Visualize a CUDS structure using graphviz."""

import logging

import graphviz

from osp.core.namespaces import cuba

logger = logging.getLogger(__name__)


class Cuds2dot:
    """Utility for creating a dot and png representation of CUDS objects."""

    label = (
        "<<TABLE BORDER='0' CELLBORDER='0'>"
        "<TR><TD>{}</TD></TR>"
        "{}"
        "</TABLE>>"
    )
    attribute = "<TR ALIGN='left'><TD>{}: {}</TD></TR>"

    def __init__(self, root):
        """Initialize the class.

        Initializes the graph.

        Args:
            root (Cuds): root cuds_object to represent.
        """
        self._root = root
        self._visited = set()
        self._root_uid = self.shorten_uid(root.uid)
        self._graph = self._initialize_graph()

    def _initialize_graph(self):
        """Initialize a directed graph with some default settings."""
        graph = graphviz.Digraph(format="png", name=str(self._root.uid))
        # graph.node_attr['shape'] = 'circle'
        return graph

    def render(self, filename=None, **kwargs):
        """Create the graph and save it to a dot and png file."""
        filename = filename or (self._graph.name + ".gv")
        logger.info("Writing file %s" % filename)
        self._add_node(self._root, self._root_uid)
        self._visited.add(self._root.uid)
        self._add_directly_related(self._root)
        self._graph.render(filename=filename, **kwargs)

    def _add_directly_related(self, current):
        """Recursively add the directly related entities to a current root.

        Args:
            current: root of the entities to add.
        """
        from osp.core.utils.general import get_relationships_between

        current_uid = self.shorten_uid(current.uid)
        for cuds_object in current.iter(rel=cuba.relationship):
            cuds_object_uid = self.shorten_uid(cuds_object.uid)
            # Add the relationships
            relationship_set = get_relationships_between(current, cuds_object)
            for relationship in relationship_set:
                self._add_edge(current_uid, cuds_object_uid, relationship)
            # Add the node if new
            if cuds_object.uid not in self._visited:
                self._add_node(cuds_object, cuds_object_uid)
                self._visited.add(cuds_object.uid)
                self._add_directly_related(cuds_object)

    def _add_node(self, cuds_object, uid):
        """Add a node to the graph.

        Args:
            cuds_object (Cuds): cuds_object of the node.
            uid (str): string with the node id
        """
        attr = self.attribute.format("class", cuds_object.oclass)
        for key, value in cuds_object.get_attributes().items():
            attr += self.attribute.format(key.argname, str(value))
        if uid == self._root_uid:
            attr += self.attribute.format(
                "session", type(self._root.session).__name__
            )
            label = self.label.format(uid, attr)
            self._graph.node(
                uid, label=label, color="lightblue", style="filled"
            )
        else:
            label = self.label.format(uid, attr)
            self._graph.node(uid, label=label)

    def _add_edge(self, start, end, relationship):
        """Add an edge between two nodes.

        Ignores the possible passive relationships returned by loops.

        Arg:
            start (str): start node
            end (str): end node
            relationship(OntologyRelationship): relationship between start and
                end.
        """
        self._graph.edge(start, end, label=str(relationship))

    @staticmethod
    def shorten_uid(uid):
        """Shortens the string of a given uid.

        Args:
            uid (UUID): uuid to shorten.

        Returns:
            str: 8 first and 3 last characters separated by '...'.
        """
        uid = str(uid)
        return uid[:8] + "..." + uid[-3:]
