"""Visualize an ontology using graphviz."""

import os
import graphviz
import argparse
import logging
from osp.core.namespaces import _namespace_registry
from osp.core.ontology.parser import Parser
from osp.core.ontology import OntologyClass, OntologyRelationship, \
    OntologyAttribute

logger = logging.getLogger(__name__)


class Ontology2Dot():
    """Utility for creating a dot and png representation of an ontology."""

    label = ("<<TABLE BORDER='0' CELLBORDER='0'>"
             "<TR><TD>{}</TD></TR>"
             "{}"
             "</TABLE>>")
    attribute = "<TR ALIGN='left'><TD>{}: {}</TD></TR>"

    def __init__(self, namespaces, output_filename, group=False):
        """Initialize the graph.

        :param namespaces: The namespaces to print.
        :type namespaces: List[str]
        :param output_filename: The path to save the resulting dot file
        :type output_filename: str
        """
        self._namespaces = list()
        for namespace in namespaces:
            if isinstance(namespace, str):
                namespace = _namespace_registry[namespace]
            self._namespaces.append(namespace)
        self._output_filename = output_filename
        self._visited = set()
        self._subgraphs = dict()
        self._group = group
        self._graph = self._initialize_graph()

    def _initialize_graph(self):
        """Initializes a directed graph with some default settings."""
        graph = graphviz.Digraph(format="png", name="ONTOLOGY")
        graph.node_attr['shape'] = 'rectangle'
        return graph

    def _get_subgraph(self, namespace):
        if not self._group:
            return self._graph
        if namespace in self._subgraphs:
            return self._subgraphs[namespace]
        cluster_name = "cluster_" + namespace._name
        if namespace in self._namespaces:
            self._subgraphs[namespace] = graphviz.Digraph(name=cluster_name)
            self._subgraphs[namespace].attr(label=namespace._name)
            return self._subgraphs[namespace]
        self._subgraphs[namespace] = graphviz.Digraph(name=cluster_name)
        self._subgraphs[namespace].attr(penwidth="0")
        return self._subgraphs[namespace]

    def render(self):
        """Create the graph and save it to a dot and png file."""
        for namespace in self._namespaces:
            self._add_namespace(namespace)
        for subgraph in self._subgraphs.values():
            self._graph.subgraph(subgraph)
        logger.info("Writing file %s" % self._output_filename)
        self._graph.render(filename=self._output_filename)

    def _add_namespace(self, namespace):
        """Add the entities of the given namespace.

        :param namespace: The entity to add
        :type entity: OntologyEntity
        """
        for entity in namespace:
            self._add_entity(entity)

    def _add_entity(self, entity):
        """Add an entity to the graph.

        :param entity: The entity to add
        :type entity: OntologyEntity
        """
        if entity in self._visited:
            return
        self._visited.add(entity)
        graph = self._get_subgraph(entity.namespace)
        if isinstance(entity, OntologyClass):
            self._add_oclass(entity, graph)
        elif isinstance(entity, OntologyRelationship):
            self._add_relationship(entity, graph)
        elif isinstance(entity, OntologyAttribute):
            self._add_attribute(entity, graph)

        for superclass in entity.direct_superclasses:
            self._add_entity(superclass)
            self._add_edge(str(entity), str(superclass), label="is_a")

    def _add_oclass(self, oclass, graph):
        """Adds a node to the graph.

        :param oclass: The ontology class to add
        :type oclass: OntologyClass
        """
        attr = ""
        for key, value in oclass.attributes.items():
            attr += self.attribute.format(key.argname, value)
        label = self.label.format(str(oclass), attr)
        if oclass.namespace in self._namespaces:
            graph.node(str(oclass), label=label,
                       color="#EED5C6", style="filled")
        else:
            graph.node(str(oclass), label=label)

    def _add_relationship(self, rel, graph):
        """Adds a node to the graph.

        :param rel: The ontology class for the node
        :type rel: OntologyRelationship
        """
        attr = ""
        label = self.label.format(str(rel), attr)
        if rel.namespace in self._namespaces:
            graph.node(str(rel), label=label,
                       color="#AFABEB", style="filled")
        else:
            graph.node(str(rel), label=label)
        if not rel.inverse.name.startswith("INVERSE_OF") \
                and rel.inverse not in self._visited:
            self._add_entity(rel.inverse)
            self._add_edge(str(rel), str(rel.inverse),
                           style="dashed", dir="none", label="inverse")

    def _add_attribute(self, attribute, graph):
        """Adds a node to the graph.

        :param rel: The ontology attribute to add
        :type rel: OntologyAttribute
        """
        attr = self.attribute.format("datatype", attribute.datatype)
        label = self.label.format(str(attribute), attr)
        if attribute.namespace in self._namespaces:
            graph.node(str(attribute), label=label,
                       color="#7EB874", style="filled")
        else:
            graph.node(str(attribute), label=label)

    def _add_edge(self, start, end, **kwargs):
        """Adds an edge between two nodes.

        Ignores the possible passive relationships returned by loops

        :param start: start node
        :type start: str
        :param end: end node
        :type end: str
        :param label: The label of the edge
        :type label: str
        """
        self._graph.edge(start, end, **kwargs)


def run_from_terminal():
    """Run ontology2dot from the terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Convert an ontology in OWL format to "
                    "an ontology in YAML format."
    )
    parser.add_argument("to_plot", metavar="to_plot",
                        type=str, nargs="+",
                        help="Either installed namespaces or paths "
                        "to yaml ontology files")
    parser.add_argument("--output-filename", "-o",
                        type=os.path.abspath, default=None,
                        help="The name of the output file")
    parser.add_argument("--group", "-g",
                        action="store_true",
                        help="Whether to organize each namespace in a "
                        "separate cluster")
    args = parser.parse_args()

    namespaces = list()
    parser = Parser(_namespace_registry._graph)
    for x in args.to_plot:
        if x in _namespace_registry:
            namespaces.append(x)
            continue
        for n in Parser.get_namespace_names(x):
            if n in _namespace_registry:
                logger.warning("Using installed version of namespace %s" % n)
                namespaces.append(_namespace_registry[n])
            else:
                parser.parse(x)
                _namespace_registry.update_namespaces()
                namespaces.append(_namespace_registry[n])

    # Convert the ontology to dot
    converter = Ontology2Dot(
        namespaces=namespaces,
        output_filename=args.output_filename,
        group=args.group
    )
    converter.render()


if __name__ == "__main__":
    run_from_terminal()
