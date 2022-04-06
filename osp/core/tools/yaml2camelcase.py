"""A script converting old ontologies to new ones.

Old ontology typically have entity names in ALL_UPPERCASE.
Newer ontology usually have entity names in CamelCase.
"""

import argparse
import logging
import os
import re
import shutil
from copy import deepcopy
from pathlib import Path

import yaml

from osp.core.ontology.parser.yml.keywords import (
    NAMESPACE_KEY,
    ONTOLOGY_KEY,
    REQUIREMENTS_KEY,
    SUPERCLASSES_KEY,
)

entity_name_regex = r"(_|[A-Z])([A-Z]|[0-9]|_)*"
entity_name_pattern = re.compile(r"^%s$" % entity_name_regex)
qualified_entity_name_pattern = re.compile(
    r"^%s\.%s$" % tuple([entity_name_regex] * 2)
)

logger = logging.getLogger(__name__)


class Yaml2CamelCaseConverter:
    """Tool that transforms entity names of  YAML ontologies.

    Input: YAML with with entity name in ALL_CAPS
    Output: YAML ontology in CamelCase.
    """

    def __init__(self, file_path):
        """Initialize the converter.

        Args:
            file_path (path): Path to the yaml file to convert
        """
        self.file_path = file_path
        with open(file_path, "r") as file:
            self.doc = yaml.safe_load(file)
            self.onto_doc = self.doc[ONTOLOGY_KEY]
            self.orig_onto_doc = deepcopy(self.onto_doc)
            self.namespace = self.doc[NAMESPACE_KEY].lower()
            self.ambiguity_resolution = dict()

    def convert(self):
        """Convert the yaml file to CamelCase."""
        self.doc[NAMESPACE_KEY] = self.namespace
        if REQUIREMENTS_KEY in self.doc:
            self.doc[REQUIREMENTS_KEY] = [
                x.lower() for x in self.doc[REQUIREMENTS_KEY]
            ]
        self.convert_nested_doc(self.onto_doc, pattern=entity_name_pattern)

    def convert_nested_doc(self, doc, pattern=qualified_entity_name_pattern):
        """Convert the document to CamelCase.

        Args:
            doc (Any): The document to convert
            pattern (re.Pattern, optional): The pattern for the entities.
                Defaults to qualified_entity_name_pattern.
        """
        if isinstance(doc, list):
            new = list()
            for elem in doc:
                if elem == "CUBA.ENTITY":
                    new.append("cuba.Entity")
                elif isinstance(elem, str) and pattern.match(elem):
                    new.append(self.toCamelCase(elem))
                else:
                    new.append(elem)
                    self.convert_nested_doc(elem)
            doc.clear()
            doc.extend(new)

        if isinstance(doc, dict):
            new = dict()
            for key, value in doc.items():
                if isinstance(key, str) and pattern.match(key):
                    new[self.toCamelCase(key)] = value
                    self.convert_nested_doc(value)
                elif value == "CUBA.ENTITY":
                    new[key] = "cuba.Entity"
                elif isinstance(value, str) and pattern.match(value):
                    new[key] = self.toCamelCase(value)
                else:
                    new[key] = value
                    self.convert_nested_doc(value)
            doc.clear()
            doc.update(new)

    def store(self, output):
        """Update the ontology on disc."""
        if not output:
            output = self.file_path
        if output == self.file_path:
            logger.info(f"Backing up original file at {output}.orig")
            orig_path = f"{output}.orig"
            orig_counter = 0
            while os.path.exists(orig_path):
                orig_path = f"{output}.orig[{orig_counter}]"
                orig_counter += 1
            shutil.copyfile(str(output), orig_path)

        logger.info(f"Writing camel case file to {output}")
        with open(output, "w") as f:
            yaml.safe_dump(self.doc, f)

    def get_first_letter_caps(self, word, internal=False):
        """Check whether a entity name should start with lower or uppercase.

        Args:
            word (str): The entity name to check
            internal (bool, optional): True iff this method has been
                called recursively. Defaults to False.

        Raises:
            ValueError: Undefined entity name

        Returns:
            Optional[bool]: True iff word should start with uppercase.
                Will always return a bool if internal is False.
        """
        # cuba cases
        if word in [
            "CUBA.RELATIONSHIP",
            "CUBA.ACTIVE_RELATIONSHIP",
            "CUBA.PASSIVE_RELATIONSHIP",
            "CUBA.ATTRIBUTE",
            "CUBA.PATH",
        ]:
            return False
        if word in ["CUBA.WRAPPER", "CUBA.NOTHING", "CUBA.FILE"]:
            return True
        if word == "CUBA.ENTITY":
            return None if internal else True

        # qualified cases
        if "." in word:
            namespace, name = word.split(".")
            if namespace.lower() == self.namespace:
                x = self.get_first_letter_caps(name, internal=True)
                return True if x is None and not internal else x
            if word in self.ambiguity_resolution:
                return self.ambiguity_resolution[word]
            ar = (
                input(f"Is {word} an ontology class (y/n)? ")
                .lower()
                .strip()
                .startswith("y")
            )
            self.ambiguity_resolution[word] = ar
            return ar

        # unqualified cases
        if word not in self.orig_onto_doc:
            raise ValueError(f"Undefined entity {word}")

        subclasses = self.orig_onto_doc[word][SUPERCLASSES_KEY]
        if any(isinstance(subclass, dict) for subclass in subclasses):
            return True
        if any(
            self.get_first_letter_caps(subclass, True) is False
            for subclass in subclasses
        ):
            return False
        if any(
            self.get_first_letter_caps(subclass, True) is True
            for subclass in subclasses
        ):
            return True

        return None if internal else True

    def toCamelCase(self, word):
        """Convert the given entity name to camel case.

        Args:
            word (str): The word to convert to CamelCase

        Returns:
            str: The entity name in CamelCase
        """
        first_letter_caps = self.get_first_letter_caps(word)
        result = ""
        if "." in word:
            result += word.split(".")[0].lower() + "."
            word = word.split(".")[1]
        result += word[0].upper() if first_letter_caps else word[0].lower()
        next_upper = False
        for c in word[1:]:
            if c == "_":
                next_upper = True
            elif next_upper:
                result += c.upper()
                next_upper = False
            else:
                result += c.lower()
        return result


def run_from_terminal():
    """Run yaml2camelcase from the terminal."""
    # Parse the user arguments
    parser = argparse.ArgumentParser(
        description="Convert a YAML ontology with ALL_CAPS entity names to a "
        "YAML ontology using CamelCase"
    )
    parser.add_argument("input", type=Path, help="The input yaml file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=False,
        default=None,
        help="The input yaml file.",
    )
    args = parser.parse_args()

    c = Yaml2CamelCaseConverter(args.input)
    c.convert()
    c.store(args.output)


if __name__ == "__main__":
    run_from_terminal()
