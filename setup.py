import os
import pickle
import traceback
from setuptools import setup, find_namespace_packages
from setuptools.command.install import install
from packageinfo import VERSION, NAME

# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()


def reset_ontology():
    import osp.core
    from osp.core.ontology.namespace_registry import \
        INSTALLED_ONTOLOGY_PATH, ONTOLOGY_NAMESPACE_REGISTRY, \
        MAIN_ONTOLOGY_NAMESPACE

    # remove from namespace registry
    for name in set(ONTOLOGY_NAMESPACE_REGISTRY._namespaces.keys()):
        if name == MAIN_ONTOLOGY_NAMESPACE:
            continue
        del ONTOLOGY_NAMESPACE_REGISTRY._namespaces[name]
        delattr(osp.core, name)

    if os.path.exists(INSTALLED_ONTOLOGY_PATH):
        os.remove(INSTALLED_ONTOLOGY_PATH)


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
    except ValueError:
        traceback.print_exc()
        print("Ontology namespace already installed!")


class Install(install):
    # The format is (long option, short option, description).
    user_options = install.user_options + [
        ('ontology=', 'o', 'The ontology to install: stable / city / toy / '
         'path to yaml file. Default: stable'),
        ('reset', 'r', 'Reset the installed ontologies.')
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.ontology = ''
        self.reset = False

    def run(self):
        if self.reset:
            reset_ontology()

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
    package_data={
        "osp.core.ontology.yml": ["*.yml"],
        "osp.core.ontology": ["*.pkl"]
    },
    cmdclass={
        'install': Install,
        'develop': Install
    },
    test_suite='tests'
)
