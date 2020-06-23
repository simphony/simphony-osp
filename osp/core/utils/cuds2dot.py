import graphviz
import logging
from osp.core.namespaces import CUBA

logger = logging.getLogger(__name__)


class Cuds2dot():
    """Utility for creating a dot and png representation of the objects
    related to a given Cuds instance
    """
    label = ("<<TABLE BORDER='0' CELLBORDER='0'>"
             "<TR><TD>{}</TD></TR>"
             "{}"
             "</TABLE>>")
    attribute = "<TR ALIGN='left'><TD>{}: {}</TD></TR>"

    def __init__(self, root):
        """Constructor.
        Initializes the graph.

        :param root: root cuds_object to represent
        :type root: Cuds
        """
        self._root = root
        self._visited = set()
        self._root_uid = self.shorten_uid(root.uid)
        self._graph = self._initialize_graph()

    def _initialize_graph(self):
        """Initializes a directed graph with some default settings"""
        graph = graphviz.Digraph(format='png', name=str(self._root.uid))
        # graph.node_attr['shape'] = 'circle'
        return graph

    def render(self, filename=None, **kwargs):
        """Create the graph and save it to a dot and png file."""
        filename = filename or (self._graph.name + "gv")
        logger.info("Writing file %s" % filename)
        self._add_node(self._root, self._root_uid)
        self._visited.add(self._root.uid)
        self._add_directly_related(self._root)
        self._graph.render(filename=filename, **kwargs)

    def _add_directly_related(self, current):
        """Recursively add the directly related entities to a current root.

        :param current: root of the entities to add
        :type current: Cuds
        """
        from osp.core.utils import get_relationships_between
        current_uid = self.shorten_uid(current.uid)
        for cuds_object in current.iter(rel=CUBA.RELATIONSHIP):
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
        """
        Adds a node to the graph.

        :param cuds_object: cuds_object of the node
        :type cuds_object: Cuds
        :param uid: string with the node id
        :type uid: str
        """
        attr = self.attribute.format("class", cuds_object.oclass)
        for key, value in cuds_object.get_attributes().items():
            attr += self.attribute.format(
                key.argname, str(value)
            )
        if uid == self._root_uid:
            attr += self.attribute.format("session",
                                          type(self._root.session).__name__)
            label = self.label.format(uid, attr)
            self._graph.node(uid, label=label,
                             color="lightblue", style="filled")
        else:
            label = self.label.format(uid, attr)
            self._graph.node(uid, label=label)

    def _add_edge(self, start, end, relationship):
        """Adds an edge between two nodes.
        Ignores the possible passive relationships returned by loops

        :param start: start node
        :type start: str
        :param end: end node
        :type end: str
        :param relationship: relationship between start and end
        :type relationship: Cuds
        """
        self._graph.edge(start,
                         end,
                         label=str(relationship))

    @staticmethod
    def shorten_uid(uid):
        """Shortens the string of a given uid

        :param uid: uuid to shorten
        :type uid: UUID
        :return: 8 first and 3 last characters separated by '...'
        :rtype: str
        """
        uid = str(uid)
        return uid[:8] + '...' + uid[-3:]
