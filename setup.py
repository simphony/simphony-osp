import os
import traceback
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.test import test
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
        if name.lower() == MAIN_ONTOLOGY_NAMESPACE:
            continue
        del ONTOLOGY_NAMESPACE_REGISTRY._namespaces[name]
        delattr(osp.core, name)

    if os.path.exists(INSTALLED_ONTOLOGY_PATH):
        os.remove(INSTALLED_ONTOLOGY_PATH)


def install_ontology(ontology):
    from osp.core.ontology.namespace_registry import \
        ONTOLOGY_NAMESPACE_REGISTRY
    from osp.core.ontology.parser import Parser
    p = Parser()
    try:
        p.parse(ontology)
        ONTOLOGY_NAMESPACE_REGISTRY.install()
    except ValueError:
        traceback.print_exc()
        print("Ontology namespace already installed!")


def parse_test_ontology():
    try:
        from osp.core.ontology.parser import Parser
        p = Parser()
        p.parse("osp/core/ontology/yml/ontology.city.yml")
    except ValueError:
        pass


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
        if self.ontology:
            install_ontology(self.ontology)
        install.run(self)


class Test(test):
    def run(self):
        parse_test_ontology()
        super().run()


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005)',
    url='www.simphony-project.eu',
    description='The native implementation of the SimPhoNy cuds objects',
    keywords='simphony, cuds, Fraunhofer IWM',
    long_description=README_TEXT,
    packages=find_packages(),
    python_requires=">=3.6",
    cmdclass={
        'install': Install,
        'develop': Install,
        'test': Test
    },
    entry_points={
        'wrappers': 'osp-core = osp.core.session.core_session:CoreSession',
        'console_scripts':
            'owl2yml = osp.core.tools.owl2yml:run_from_terminal'
    },
    install_requires=[
        "PyYaml",
        "websockets",
        "requests",
        "numpy",
        "graphviz",
        "owlready2"
    ],
    setup_requires=[
        "PyYaml",
        "websockets",
        "requests",
        "numpy",
        "graphviz",
        "owlready2"
    ]
)
