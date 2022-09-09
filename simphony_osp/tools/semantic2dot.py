"""Visualize an ontology, an individual or a session using graphviz."""

import argparse
import logging
import os
from pathlib import Path
from typing import FrozenSet, Iterable, Optional, Union
from uuid import UUID

from graphviz import Digraph

from simphony_osp.namespaces import owl
from simphony_osp.ontology.attribute import OntologyAttribute
from simphony_osp.ontology.entity import OntologyEntity
from simphony_osp.ontology.individual import OntologyIndividual
from simphony_osp.ontology.namespace import OntologyNamespace
from simphony_osp.ontology.oclass import OntologyClass
from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.ontology.relationship import OntologyRelationship
from simphony_osp.session.session import Session
from simphony_osp.tools.search import find
from simphony_osp.utils.datatypes import UID

logger = logging.getLogger(__name__)


class Semantic2Dot:
    """Class for ojects returned by the `semantic2dot` plotting tool.

    Objects of this class produced as outcome of calling the `semantic2dot`
    plotting tool. They hold the graph information and can be used either to
    display it in a Jupyter notebook or render the graph to a file.
    """

    def __init__(
        self,
        *elements: Union[
            OntologyIndividual,
            OntologyNamespace,
            Session,
        ],
        rel: Optional[
            Union[OntologyRelationship, Iterable[OntologyRelationship]]
        ] = None,
    ):
        """Initializes the class."""
        if rel is not None:
            rel = {rel} if isinstance(rel, OntologyRelationship) else set(rel)

        # Classify items to be drawn
        classes = {OntologyIndividual, OntologyNamespace, Session}
        class_identified = (
            (class_, element)
            for element in elements
            for class_ in classes
            if isinstance(element, class_)
        )
        classification = {
            OntologyIndividual: set(),
            OntologyNamespace: set(),
            Session: set(),
        }
        for class_, element in class_identified:
            classification[class_].add(element)
        unclassified = set(elements) - set(
            item for items in classification.values() for item in items
        )
        if unclassified:
            raise TypeError(
                f"The object{'s' if len(unclassified) > 2 else ''} "
                f"{','.join(str(x) for x in unclassified)} "
                f"cannot be drawn."
            )

        # Save nodes requested to be drawn
        supported_classes = (
            OntologyIndividual,
            OntologyClass,
            OntologyAttribute,
            OntologyRelationship,
        )
        self._requested_individuals = frozenset(
            classification[OntologyIndividual]
        )
        self._requested = frozenset(
            {
                part
                for individual in classification[OntologyIndividual]
                for part in (
                    find(individual, rel=rel, find_all=True)
                    if rel is not None
                    else (individual,)
                )
            }
            | {
                entity
                for namespace in classification[OntologyNamespace]
                for entity in namespace
                if isinstance(entity, supported_classes)
            }
            | {
                entity
                for session in classification[Session]
                for entity in session
            }
        )

        self._graph = Digraph(format="png", name="SimPhoNy semantic2dot")
        self._draw_all()

    def render(self, filename: str = None, **kwargs) -> None:
        """Save the graph to a dot and png file."""
        if filename is None:
            raise ValueError("Please specify a file name to save your graph.")
        logger.info("Writing file %s" % filename)
        self._graph.render(filename=filename, **kwargs)

    def _repr_mimebundle_(
        self,
        include: Optional[Iterable[str]],
        exclude: Optional[Iterable[str]],
    ):
        """Render the graph as an image on IPython (e.g. Jupyter notebooks)."""
        return self._graph._repr_mimebundle_(include, exclude)

    _label = (
        "<<TABLE BORDER='0' CELLBORDER='0'>"
        "<TR><TD>{}</TD></TR>"
        "{}"
        "</TABLE>>"
    )

    _attribute = "<TR ALIGN='left'><TD>{}: {}</TD></TR>"

    _requested: FrozenSet[OntologyEntity]
    _requested_individuals: FrozenSet[OntologyIndividual]

    def _draw_all(self) -> None:
        """Draws all the requested items.

        Goes over all the requested items, draws them, also draws any
        complementary items (e.g. superclasses) and finally draws the edges.

        REMARK: This method should be run ONLY ONCE.
        """
        # keep track of ontology individual relationships
        edges = {
            "individual_relationships": set(),
            "complementary_superclasses": set(),
            "inverse_relationships": set(),
        }
        nodes = self._requested
        complementary_nodes = set()

        # draw nodes, compute edges and complementary node
        for node in nodes:
            if isinstance(node, OntologyIndividual):
                edges["individual_relationships"] |= {
                    (node, relationship, target)
                    for target, relationship in node.relationships_iter(
                        return_rel=True
                    )
                    if target in nodes
                }
            elif isinstance(node, OntologyRelationship):
                superclasses = set(node.direct_superclasses)
                if not superclasses and owl.topObjectProperty != node:
                    superclasses |= {owl.topObjectProperty}
                complementary_nodes |= superclasses
                edges["complementary_superclasses"] |= {
                    (node, superclass) for superclass in superclasses
                }
                inverse = node.inverse
                if inverse in nodes:
                    edges["inverse_relationships"].add(
                        frozenset({node, inverse})
                    )
            elif isinstance(node, OntologyAttribute):
                superclasses = set(node.direct_superclasses)
                if not superclasses and owl.topDataProperty != node:
                    superclasses |= {owl.topDataProperty}
                complementary_nodes |= superclasses
                edges["complementary_superclasses"] |= {
                    (node, superclass) for superclass in superclasses
                }
            elif isinstance(node, OntologyClass):
                superclasses = set(node.direct_superclasses)
                if not superclasses and owl.Thing != node:
                    superclasses |= {owl.Thing}
                complementary_nodes |= superclasses
                edges["complementary_superclasses"] |= {
                    (node, superclass) for superclass in superclasses
                }

            self._draw_node(node, complementary=False)

        complementary_nodes = complementary_nodes - nodes

        # draw complementary nodes
        for node in complementary_nodes:
            self._draw_node(node, complementary=True)

        # draw edges
        # - direct superclasses
        for node, superclass in edges["complementary_superclasses"]:
            self._draw_edge(node, superclass, label="is_a")
        # - relationships between individuals
        for start, rel, end in edges["individual_relationships"]:
            self._draw_edge(
                start,
                end,
                label=(
                    self._get_element_label(rel) + f" ({rel.namespace.name})"
                    if rel.namespace
                    else ""
                ),
            )
        # - inverse relationships
        for node1, node2 in edges["inverse_relationships"]:
            self._draw_edge(
                node1, node2, label="inverse", dir="none", style="dashed"
            )

    @staticmethod
    def _get_element_label(
        element: Union[
            OntologyEntity,
            Session,
            OntologyNamespace,
        ]
    ) -> str:
        """Compute a label for an ontology entity, session or namespace."""
        if isinstance(element, OntologyEntity):
            name = Semantic2Dot._get_ontology_entity_label(element)
        elif isinstance(element, Session):
            name = f"{hex(id(Session))}"
        elif isinstance(element, OntologyNamespace):
            name = f"{element.name}"
        else:
            raise TypeError(f"Unsupported element type {type(element)}.")
        return str(name)

    @staticmethod
    def _get_ontology_entity_label(element: OntologyEntity) -> str:
        """Compute a label for an ontology entity."""
        # Try label
        name = element.label

        if name is None:
            # Try suffix
            name = (
                element.iri[len(element.namespace.iri) :]
                if element.namespace is not None
                else None
            )

        # Try UUID or identifier
        if name is None:
            if isinstance(element.uid.data, UUID):
                name = Semantic2Dot._shorten_uid(element.uid)
            else:
                name = element.identifier

        return name

    @staticmethod
    def _shorten_uid(uid: UID) -> str:
        """Shortens the string of a given uid.

        Args:
            uid: UID to shorten
        Returns:
            str: 8 first and 3 last characters separated by '...'.
        """
        uid = str(uid)
        return uid[:8] + "..." + uid[-3:]

    def _draw_node(
        self, entity: OntologyEntity, complementary: bool = False
    ) -> None:
        """Choose the method to draw an ontology entity and call it.

        Selects the correct method to draw an ontology entity according to
        its type and calls it.

        Args:
            entity: The ontology entity to draw.

        Raises:
            TypeError: Unsupported entity type.
        """
        if isinstance(entity, OntologyIndividual):
            self._draw_node_individual(entity, complementary=complementary)
        elif isinstance(entity, OntologyRelationship):
            self._draw_node_relationship(entity, complementary=complementary)
        elif isinstance(entity, OntologyAttribute):
            self._draw_node_attribute(entity, complementary=complementary)
        elif isinstance(entity, OntologyClass):
            self._draw_node_class(entity, complementary=complementary)
        else:
            raise TypeError(f"Cannot draw {type(entity)}.")

    def _draw_node_individual(
        self,
        individual: OntologyIndividual,
        complementary: bool = False,
    ) -> None:
        """Add an ontology individual as a node to the graph.

        Args:
            individual: Ontology individual to draw.
            complementary: Whether the drawn entity is complementary or not.
        """
        attributes = self._attribute.format(
            "classes",
            ",".join(
                str(x) + (f" ({x.namespace.name})" if x.namespace else "")
                for x in individual.classes
            ),
        )

        for key, value in individual.attributes.items():
            label = self._get_element_label(key)
            if len(value) == 1:
                value = list(value)[0]
            elif len(value) == 0:
                value = None
            else:
                value = str(set(value)).replace(":", "_").replace("/", "_")
            attributes += self._attribute.format(label, str(value))

        if individual in self._requested_individuals:
            attributes += self._attribute.format(
                "session", self._get_element_label(individual.session)
            )
            extra_kwargs = {"color": "lightblue", "style": "filled"}
        else:
            extra_kwargs = dict()

        if complementary:
            extra_kwargs |= {
                "shape": "rectangle",
            }

        label = self._label.format(
            self._get_element_label(individual), attributes
        )

        self._graph.node(
            str(individual.identifier).replace(":", "_").replace("/", "_"),
            label=label,
            **extra_kwargs,
        )

    def _draw_node_class(
        self,
        class_: OntologyClass,
        complementary: bool = False,
    ) -> None:
        """Add an ontology class as a node to the graph.

        Args:
            class_: Ontology class to draw.
            complementary: Whether the drawn entity is complementary or not.
        """
        attr = ""
        for key, value in class_.attributes.items():
            attr += self._attribute.format(
                self._get_element_label(key),
                value if value else None,
            )
        label = (
            f"{self._get_element_label(class_)} "
            f'({class_.namespace.name if class_.namespace else ""})'
        )
        label = self._label.format(label, attr)

        if complementary:
            extra_kwargs = {
                "color": "#EEE4DD",
                "shape": "rectangle",
            }
        else:
            extra_kwargs = {"color": "#EED5C6"}

        self._graph.node(
            str(class_.identifier).replace(":", "_").replace("/", "_"),
            style="filled",
            label=label,
            **extra_kwargs,
        )

    def _draw_node_relationship(
        self,
        rel: OntologyRelationship,
        complementary: bool = False,
    ) -> None:
        """Add an ontology relationship as a node to the graph.

        Args:
            rel: Ontology class to draw.
            complementary: Whether the drawn entity is complementary or not.
        """
        attr = ""
        label = (
            f"{self._get_element_label(rel)} "
            f'({rel.namespace.name if rel.namespace else ""})'
        )
        label = self._label.format(label, attr)

        if complementary:
            extra_kwargs = {
                "color": "#DCDBEB",
                "shape": "rectangle",
            }
        else:
            extra_kwargs = {"color": "#AFABEB"}

        self._graph.node(
            str(rel.identifier).replace(":", "_").replace("/", "_"),
            label=label,
            style="filled",
            **extra_kwargs,
        )

    def _draw_node_attribute(
        self,
        attribute: OntologyAttribute,
        complementary: bool = False,
    ) -> None:
        """Add an ontology attribute as a node to the graph.

        Args:
            attribute: Ontology attribute to draw.
            complementary: Whether the drawn entity is complementary or not.
        """
        try:
            datatype = attribute.datatype
        except NotImplementedError:
            datatype = "multiple"
        attr = self._attribute.format("datatype", datatype)
        label = (
            f"{self._get_element_label(attribute)} "
            f'({attribute.namespace.name if attribute.namespace else ""})'
        )
        label = self._label.format(label, attr)

        if complementary:
            extra_kwargs = {
                "color": "#ADB8AB",
                "shape": "rectangle",
            }
        else:
            extra_kwargs = {"color": "#7EB874"}

        self._graph.node(
            str(attribute.identifier).replace(":", "_").replace("/", "_"),
            label=label,
            style="filled",
            **extra_kwargs,
        )

    def _draw_edge(
        self, start: OntologyEntity, end: OntologyEntity, **kwargs
    ) -> None:
        """Add an edge between two nodes.

        Args:
            start: start node
            end: end node
        """
        self._graph.edge(
            str(start.identifier).replace(":", "_").replace("/", "_"),
            str(end.identifier).replace(":", "_").replace("/", "_"),
            **kwargs,
        )


def terminal():
    """Run Semantic2Dot from the terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(description="Plot ontology namespaces.")
    parser.add_argument(
        "plot",
        metavar="plot",
        type=str,
        nargs="+",
        help="Either installed namespaces or paths to yaml ontology files",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=os.path.abspath,
        default=Path(os.getcwd()) / "semantic2dot",
        help="The path of the output file",
    )
    args = parser.parse_args()

    namespaces = set()
    for x in args.plot:

        try:
            namespaces.add(Session.default_ontology.get_namespace(x))
            logger.warning("Using installed version of namespace %s" % x)
            continue
        except KeyError:
            pass

        parser = OntologyParser.get_parser(x)
        logger.warning("Including all namespaces of package %s" % x)
        for iri in parser.namespaces.values():
            try:
                namespace = Session.default_ontology.get_namespace(iri)
            except KeyError:
                Session.default_ontology.load_parser(parser)
                namespace = Session.default_ontology.get_namespace(iri)
            namespaces.add(namespace)

    # Convert the ontology to dot
    converter = Semantic2Dot(*namespaces)
    converter.render(filename=args.output_filename)


def semantic2dot(
    *elements: Union[
        OntologyIndividual,
        OntologyNamespace,
        Session,
    ],
    rel: Optional[
        Union[OntologyRelationship, Iterable[OntologyRelationship]]
    ] = None,
) -> Semantic2Dot:
    """Utility for plotting ontology entities.

    Note: If you are reading the SimPhoNy documentation API Reference, it
    is likely that you cannot read this docstring. As a workaround, click
    the `source` button to read it in its raw form.

    Plot assertional knowledge (ontology individuals and the relationships
    between them), plot terminological knowledge
    (classes, relationships and attributes), or a combination of them.

    Args:
        elements: Elements to plot:
            (Session) plot the whole contents of a session;
            (OntologyNamespace) plot all the ontology entities contained
                in the ontology namespace;
            (OntologyIndividual) plots an ontology individual,
                or a collection of them, and the relationships between them if
                multiple are provided;
        rel: When not `None` and when plotting an ontology individual, calls
            uses the method `find(individual, rel=rel, find_all=True)` from
            `simphony_osp.tools.search` to additionally plot such individuals.
    """
    return Semantic2Dot(*elements, rel=rel)


if __name__ == "__main__":
    terminal()
