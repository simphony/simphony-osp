# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

from cuds.generator.settings import get_parsed_settings
from cuds.parser import ONTOLOGY_KEY
from cuds.parser.ontology import Ontology
import yaml


class Parser:
    """
    Class that parses a YAML file and finds information about the entities
    contained.
    """

    def __init__(self, filename):
        """
        Constructor. Sets the filename.

        :param filename: name of the YAML file with the ontology
        """
        self._filename = filename
        self._ontology = None
        self._parsed_settings = {}
        self.parse()

    def parse(self):
        """
        Reads the YAML and extracts the dictionary with the CUDS.
        """
        with open(self._filename, 'r') as stream:
            try:
                yaml_doc = yaml.safe_load(stream)
                self._parsed_settings = get_parsed_settings(yaml_doc)
                self._ontology = Ontology(yaml_doc[ONTOLOGY_KEY])
                self._ontology.load()
            except yaml.YAMLError as exc:
                print(exc)

    def get_parsed_settings(self):
        return self._parsed_settings

    def get_ontology(self):
        return self._ontology
