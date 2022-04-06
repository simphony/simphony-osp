"""Visualize an ontology using graphviz."""

import argparse
import logging
import os

import graphviz

from osp.core.ontology import (
    OntologyAttribute,
    OntologyClass,
    OntologyRelationship,
)
from osp.core.ontology.namespace_registry import namespace_registry
from osp.core.ontology.parser import OntologyParser

logger = logging.getLogger(__name__)


class Ontology2Dot:
    """Utility for creating a dot and png representation of an ontology."""

    label = (
        "<<TABLE BORDER='0' CELLBORDER='0'>"
        "<TR><TD>{}</TD></TR>"
        "{}"
        "</TABLE>>"
    )
    attribute = "<TR ALIGN='left'><TD>{}: {}</TD></TR>"

    def __init__(self, namespaces, output_filename, group=False):
        """Initialize the graph.

        Args:
            namespaces (List[str]): The namespaces to print.
            output_filename (str): The path to save the resulting dot file.
            group (bool): Whether to group the entities by namespace.
        """
        self._namespaces = list()
        for namespace in namespaces:
            if isinstance(namespace, str):
                namespace = namespace_registry[namespace]
            self._namespaces.append(namespace)
        self._output_filename = output_filename
        self._visited = set()
        self._subgraphs = dict()
        self._group = group
        self._graph = self._initialize_graph()

    def _initialize_graph(self):
        """Initialize a directed graph with some default settings."""
        graph = graphviz.Digraph(format="png", name="ONTOLOGY")
        graph.node_attr["shape"] = "rectangle"
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

        Args:
            namespace (OntologyEntity): The entity to add.
        """
        for entity in namespace:
            self._add_entity(entity)

    def _add_entity(self, entity):
        """Add an entity to the graph.

        Args:
            entity: The entity to add.
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
        """Add a node to the graph.

        Args:
            oclass (OntologyClass): The ontology class to add.
            graph (graphviz.Digraph): The graphviz graph to add the node to.
        """
        attr = ""
        for key, value in oclass.attributes.items():
            attr += self.attribute.format(key.argname, value[0])
        label = self.label.format(str(oclass), attr)
        if oclass.namespace in self._namespaces:
            graph.node(
                str(oclass), label=label, color="#EED5C6", style="filled"
            )
        else:
            graph.node(str(oclass), label=label)

    def _add_relationship(self, rel, graph):
        """Add a node to the graph.

        Args:
            rel (OntologyRelationship): The ontology class for the node.
            graph (graphviz.Digraph): The graphviz graph to add the node to.
        """
        attr = ""
        label = self.label.format(str(rel), attr)
        if rel.namespace in self._namespaces:
            graph.node(str(rel), label=label, color="#AFABEB", style="filled")
        else:
            graph.node(str(rel), label=label)
        if (
            not rel.inverse.name.startswith("INVERSE_OF")
            and rel.inverse not in self._visited
        ):
            self._add_entity(rel.inverse)
            self._add_edge(
                str(rel),
                str(rel.inverse),
                style="dashed",
                dir="none",
                label="inverse",
            )

    def _add_attribute(self, attribute, graph):
        """Add a node to the graph.

        Args:
            attribute (OntologyAttribute): The ontology attribute to add.
            graph (graphviz.Digraph): The graphviz graph to add the node to.
        """
        attr = self.attribute.format("datatype", attribute.datatype)
        label = self.label.format(str(attribute), attr)
        if attribute.namespace in self._namespaces:
            graph.node(
                str(attribute), label=label, color="#7EB874", style="filled"
            )
        else:
            graph.node(str(attribute), label=label)

    def _add_edge(self, start, end, **kwargs):
        """Add an edge between two nodes.

        Ignores the possible passive relationships returned by loops

        Args:
            start (str): start node
            end (str): end node
            label (str): The label of the edge
        """
        self._graph.edge(start, end, **kwargs)


def run_from_terminal():
    """Run ontology2dot from the terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Convert an ontology in OWL format to "
        "an ontology in YAML format."
    )
    parser.add_argument(
        "to_plot",
        metavar="to_plot",
        type=str,
        nargs="+",
        help="Either installed namespaces or paths " "to yaml ontology files",
    )
    parser.add_argument(
        "--output-filename",
        "-o",
        type=os.path.abspath,
        default=None,
        help="The name of the output file",
    )
    parser.add_argument(
        "--group",
        "-g",
        action="store_true",
        help="Whether to organize each namespace in a " "separate cluster",
    )
    args = parser.parse_args()

    namespaces = list()
    for x in args.to_plot:
        if x in namespace_registry:
            namespaces.append(x)
            continue
        parser = OntologyParser.get_parser(x)
        for n in parser.namespaces.keys():
            if n in namespace_registry:
                logger.warning("Using installed version of namespace %s" % n)
                namespaces.append(namespace_registry[n])
            else:
                namespace_registry.load_parser(parser)
                namespaces.append(namespace_registry[n])

    # Convert the ontology to dot
    converter = Ontology2Dot(
        namespaces=namespaces,
        output_filename=args.output_filename,
        group=args.group,
    )
    converter.render()


if __name__ == "__main__":
    run_from_terminal()
