import os
import subprocess
import logging
import rdflib

logger = logging.getLogger(__name__)

RESULT_FILE = "inferred_ontology.owl"


class OwlApi():
    def __init__(self):
        pass

    def reason(self, *owl_files):
        """Merge the given owl and generate the inferred axioms

        Args:
            owl_files (os.path): The owl files two merge
        """
        self._run(*owl_files, command="--run-reasoner")

    def merge(self, *owl_files):
        """Merge the given owl files and its import closure

        Args:
            owl_files (os.path): The owl files two merge
        """
        self._run(*owl_files, command="--merge-only")

    def _run(self, *owl_files, command):
        """Run the Java script

        Args:
            owl_files (str): Path to owl files to load
        """
        java_base = os.path.abspath(
            os.path.join(os.path.dirname(__file__),
                         "..", "java")
        )
        cmd = [
            "java", "-cp",
            java_base + "/lib/jars/*",
            "-Djava.library.path="
            + java_base + "/lib/so", "org.simphony.OntologyLoader"
        ] + ["--%s" % command] + list(owl_files)
        logger.info("Running Reasoner")
        logger.debug(" ".join(cmd))
        subprocess.run(cmd, check=True)

        graph = rdflib.Graph()
        graph.parse(RESULT_FILE)
        os.remove(RESULT_FILE)
        return graph
