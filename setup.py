import os
import pickle
from setuptools import setup, find_namespace_packages
from subprocess import check_call, CalledProcessError
from setuptools.command.install import install
from packageinfo import VERSION, NAME

# Should be in install_requires, but needed for ClassGenerator import
try:
    check_call(["pip3", "install", "-r", "requirements.txt"])
except (FileNotFoundError, CalledProcessError):
    check_call(["pip", "install", "-r", "requirements.txt"])

# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()


def install_ontology(ontology):
    ontology_file = ontology
    if not ontology.endswith(".yml"):
        ontology_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "osp", "core", "ontology", "yml",
            "ontology.%s.yml" % ontology
        )
    from osp.core.ontology.namespace_registry import \
        ONTOLOGY_NAMESPACE_REGISTRY, INSTALLED_ONTOLOGY_PATH
    from osp.core.ontology.parser import Parser
    p = Parser()
    try:
        p.parse(ontology_file)
        with open(INSTALLED_ONTOLOGY_PATH, "wb") as f:
            pickle.dump(
                ONTOLOGY_NAMESPACE_REGISTRY, f
            )
    except ValueError as e:
        raise ValueError("Ontology namespace already installed") from e


class Install(install):
    # The format is (long option, short option, description).
    user_options = install.user_options + [
        ('ontology=', 'o', 'The ontology to install: stable / city / toy / '
         'path to yaml file. Default: stable'),
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.ontology = ''

    def run(self):
        install_ontology(self.ontology or "city")
        install.run(self)


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005)',
    url='www.simphony-project.eu',
    description='The native implementation of the SimPhoNy cuds objects',
    keywords='simphony, cuds, Fraunhofer IWM',
    long_description=README_TEXT,
    packages=find_namespace_packages(include=["osp.*"]),
    cmdclass={
        'install': Install
    },
    test_suite='tests'
)
