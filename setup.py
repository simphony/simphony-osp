from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.test import test
from packageinfo import VERSION, NAME

# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()


def parse_test_ontology():
    try:
        from osp.core import ONTOLOGY_INSTALLER
        p = ONTOLOGY_INSTALLER.parser
        p.parse("city")
    except ValueError:
        pass


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
    package_data={
        "osp.core.ontology.yml": ["*.yml"],
        "osp.core.ontology": ["*.pkl"]
    },
    python_requires=">=3.6",
    cmdclass={
        'test': Test
    },
    entry_points={
        'wrappers': 'osp-core = osp.core.session.core_session:CoreSession',
        'console_scripts': {
            'owl2yml = osp.core.tools.owl2yml:run_from_terminal',
            'pico = osp.core.ontology.installation:install_from_terminal'
        }
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
