"""Visualize an ontology, an individual or a session using graphviz."""

import argparse
import logging
import os
from typing import Optional, Set, Union
from uuid import UUID

import graphviz

from simphony_osp.namespaces import owl
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.utils.datatypes import UID

logger = logging.getLogger(__name__)


class Semantic2Dot:
    """Utility for creating a dot and png representation semantic data."""

    _label = (
        "<<TABLE BORDER='0' CELLBORDER='0'>"
        "<TR><TD>{}</TD></TR>"
        "{}"
        "</TABLE>>"
    )

    _attribute = "<TR ALIGN='left'><TD>{}: {}</TD></TR>"

    _visited: Set

    def __init__(
        self,
        *elements: Union[
            OntologyIndividual,
            OntologyNamespace,
            Session,
            # Wrapper, # TODO,
        ],
        group: bool = False,
    ):
        """Initialize the class."""
        self._elements = elements
        self._visited = set()
        self._graph = self._initialize_graph()
        self._group = group
        self._sub_graphs = dict()

    def render(self, filename: str = None, **kwargs):
        """Create the graph and save it to a dot and png file."""
        if filename is None:
            raise ValueError("Please specify a file name to save your graph.")
        filename = filename
        logger.info("Writing file %s" % filename)
        for element in self._elements:
            if isinstance(element, OntologyIndividual):
                self._render_individual(element)
            elif isinstance(element, Session):
                self._render_session(element)
            elif isinstance(element, OntologyNamespace):
                self._render_namespace(element)
        for subgraph in self._sub_graphs.values():
            self._graph.subgraph(subgraph)
        logger.info("Writing file %s" % filename)
        self._graph.render(filename=filename, **kwargs)

    def _render_individual(self, individual: OntologyIndividual):
        self._add_individual_recursively(individual)

    def _render_namespace(self, namespace: OntologyNamespace):
        for entity in namespace:
            self._add_ontology_entity(entity)

    def _render_session(self, session: Session):
        # Render ontology and all individuals in the session.
        pass

    def _initialize_graph(self):
        """Initialize a directed graph with some default settings."""
        name = ", ".join(self._element_label(x) for x in self._elements)
        graph = graphviz.Digraph(format="png", name=name)
        # graph.node_attr['shape'] = 'circle'
        return graph

    def _get_subgraph(self, namespace: OntologyNamespace):
        if not self._group:
            return self._graph
        if namespace in self._sub_graphs:
            return self._sub_graphs[namespace]
        cluster_name = "cluster_" + namespace.name or namespace.iri
        if namespace in self._elements:
            self._sub_graphs[namespace] = graphviz.Digraph(name=cluster_name)
            self._sub_graphs[namespace].attr(
                label=namespace.name or namespace.iri
            )
            return self._sub_graphs[namespace]
        self._sub_graphs[namespace] = graphviz.Digraph(name=cluster_name)
        self._sub_graphs[namespace].attr(penwidth="0")
        return self._sub_graphs[namespace]

    @staticmethod
    def _element_label(
        element: Union[
            OntologyEntity,
            Session,
            # Wrapper, # TODO
            OntologyNamespace,
        ]
    ):
        if isinstance(element, OntologyEntity):
            name = Semantic2Dot._ontology_label(element)
        elif isinstance(element, Session):
            name = f"Session {hex(id(Session))}"
        elif isinstance(element, OntologyNamespace):
            name = f"Namespace {element}"
        else:
            raise TypeError(f"Unsupported element type {type(element)}.")
        return str(name)

    @staticmethod
    def _ontology_label(element: OntologyEntity):
        if element.label is not None:
            name = element.label
        else:
            suffixes = (
                element.iri[len(ns.iri) :]
                for ns in element.session.namespaces
                if element in ns
            )
            name = next(suffixes, None)
            if name is None:
                if isinstance(element.uid.data, UUID):
                    name = Semantic2Dot._shorten_uid(element.uid)
                else:
                    name = element.identifier
        return name

    @staticmethod
    def _shorten_uid(uid: UID):
        """Shortens the string of a given uid.

        Args:
            uid: UID to shorten
        Returns:
            str: 8 first and 3 last characters separated by '...'.
        """
        uid = str(uid)
        return uid[:8] + "..." + uid[-3:]

    def _add_namespace(self, namespace: OntologyNamespace):
        """Add the entities of the given namespace.

        Args:
            namespace (OntologyEntity): The entity to add.
        """
        for entity in namespace:
            self._add_ontology_entity(entity)

    def _add_ontology_entity(
        self,
        entity: Union[
            OntologyClass,
            OntologyIndividual,
            OntologyRelationship,
            OntologyAttribute,
        ],
    ):
        """Add an entity to the graph.

        Args:
            entity: The entity to add.
        """
        if entity in self._visited:
            return
        self._visited.add(entity)
        entity_namespace = next(
            (ns for ns in entity.session.namespaces if entity in ns), None
        )
        graph = self._get_subgraph(entity_namespace)
        if isinstance(entity, OntologyClass):
            self._add_node_oclass(entity, graph)
        elif isinstance(entity, OntologyRelationship):
            self._add_node_relationship(entity, graph)
        elif isinstance(entity, OntologyAttribute):
            self._add_node_attribute(entity, graph)

        for superclass in entity.direct_superclasses:
            self._add_ontology_entity(superclass)
            self._add_edge(entity, superclass, label="is_a")

    def _add_individual_recursively(self, entity):
        if entity not in self._visited:
            self._visited.add(entity)
            self._add_node_individual(entity)
            for other, rel in entity.relationships_iter(
                rel=owl.topObjectProperty, return_rel=True
            ):
                self._add_edge_individual_relationship(entity, other, rel)
                self._add_individual_recursively(other)

    def _add_node_individual(self, individual: OntologyIndividual):
        """Add an ontology individual as a node to the graph.

        Args:
            individual: Ontology individual to draw.
        """
        attributes = self._attribute.format("class", individual.oclass)

        for key, value in individual.attributes().items():
            label = self._element_label(key)
            if len(value) == 1:
                value = value.pop()
            elif len(value) == 0:
                value = None
            else:
                value = str(value).replace(":", "_").replace("/", "_")
            attributes += self._attribute.format(label, str(value))

        if individual in self._elements:
            attributes += self._attribute.format("session", individual.session)
            label = self._label.format(
                self._element_label(individual), attributes
            )
            self._graph.node(
                str(individual.identifier).replace(":", "_").replace("/", "_"),
                label=label,
                color="lightblue",
                style="filled",
            )
        else:
            label = self._label.format(
                self._element_label(individual), attributes
            )
            self._graph.node(
                str(individual.identifier).replace(":", "_").replace("/", "_"),
                label=label,
            )

    def _add_edge_individual_relationship(self, start, end, relationship):
        """Add an edge between two nodes.

        Ignores the possible passive relationships returned by loops.

        Arg:
            start (str): start node
            end (str): end node
            relationship(OntologyRelationship): relationship between start and
                end.
        """
        self._graph.edge(
            start.identifier.replace(":", "_").replace("/", "_"),
            end.identifier.replace(":", "_").replace("/", "_"),
            label=self._element_label(relationship),
        )

    def _add_edge(self, start: OntologyEntity, end: OntologyEntity, **kwargs):
        """Add an edge between two nodes.

        Ignores the possible passive relationships returned by loops

        Args:
            start (str): start node
            end (str): end node
            label (str): The label of the edge
        """
        self._graph.edge(
            str(start.identifier).replace(":", "_").replace("/", "_"),
            str(end.identifier).replace(":", "_").replace("/", "_"),
            **kwargs,
        )

    def _add_node_oclass(
        self, oclass: OntologyClass, graph: Optional[graphviz.Digraph] = None
    ):
        attr = ""
        for key, value in oclass.attributes.items():
            attr += self._attribute.format(
                self._element_label(key),
                value.pop() if len(value) > 0 else None,
            )
        label = self._label.format(self._element_label(oclass), attr)
        graph.node(
            str(oclass.identifier).replace(":", "_").replace("/", "_"),
            color="#EED5C6",
            style="filled",
            label=label,
        )

    def _add_node_relationship(
        self,
        rel: OntologyRelationship,
        graph: Optional[graphviz.Digraph] = None,
    ):
        attr = ""
        label = self._label.format(self._element_label(rel), attr)
        graph.node(
            str(rel.identifier).replace(":", "_").replace("/", "_"),
            label=label,
            color="#AFABEB",
            style="filled",
        )

    def _add_node_attribute(
        self,
        attribute: OntologyAttribute,
        graph: Optional[graphviz.Digraph] = None,
    ):
        attr = self._attribute.format("datatype", attribute.datatype)
        label = self._label.format(self._element_label(attribute), attr)
        graph.node(
            str(attribute.identifier).replace(":", "_").replace("/", "_"),
            label=label,
            color="#7EB874",
            style="filled",
        )


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
        try:
            namespaces.append(Session.default_ontology.get_namespace(x))
            logger.warning("Using installed version of namespace %s" % x)
            continue
        except KeyError:
            pass
        parser = OntologyParser.get_parser(x)
        for iri in parser.namespaces.values():
            try:
                namespaces.append(Session.default_ontology.get_namespace(iri))
                logger.warning("Using installed version of namespace %s" % iri)
            except KeyError:
                Session.default_ontology.load_parser(parser)
                namespaces.append(Session.default_ontology.get_namespace(iri))

    # Convert the ontology to dot
    converter = Semantic2Dot(*namespaces, group=args.group)
    converter.render(filename=args.output_filename)


if __name__ == "__main__":
    run_from_terminal()
