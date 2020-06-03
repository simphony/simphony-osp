import os
import logging
import yaml

logger = logging.getLogger(__name__)


class YmlParser():
    def __init__(self, graph):
        self.graph = graph

    def parse(self, *file_paths):
        """Parse the given YAML files

        Args:
            file_paths (str): path to the YAML file
        """

    def store(self, destination):
        pass
