import os

import re
from setuptools import setup
from subprocess import check_call, CalledProcessError
from setuptools.command.install import install
from setuptools.command.develop import develop
from packageinfo import VERSION, NAME

# Should be in install_requires, but needed for ClassGenerator import
try:
    check_call(["pip3", "install", "-r", "requirements.txt"])
except (FileNotFoundError, CalledProcessError):
    check_call(["pip", "install", "-r", "requirements.txt"])

from cuds.generator.class_generator import ClassGenerator

# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()


def create_ontology_classes(ontology):
    ontology_file = ontology
    if not ontology.endswith(".yml"):
        ontology_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'cuds', 'ontology', 'ontology.' + ontology + '.yml')
    entity_template = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'cuds', 'generator', 'template_entity')
    relationship_template = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'cuds', 'generator', 'template_relationship')

    if not os.path.exists(ontology_file):
        text = 'Unrecoverable error. Cannot find ' + ontology + ' file in {}'
        raise RuntimeError(text.format(ontology_file))

    if not os.path.exists(entity_template):
        text = 'Unrecoverable error. Cannot find \'template\' file in {}'
        raise RuntimeError(text.format(entity_template))

    if not os.path.exists(relationship_template):
        text = 'Unrecoverable error. Cannot find \'template\' file in {}'
        raise RuntimeError(text.format(relationship_template))

    print('Building classes from ontology...')
    path = "cuds/classes/generated"
    ClassGenerator(ontology_file, entity_template, relationship_template, path)\
        .generate_classes()


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
        create_ontology_classes(self.ontology or "city")
        install.run(self)


class Develop(develop):
    def run(self):
        create_ontology_classes('ontology_stable.yml')
        develop.run(self)


# Create the directory for the classes, otherwise the package is not added

try:
    os.makedirs("cuds/classes/generated")
except OSError:
    pass

# We cannot use find_packages because we are generating files during build.
packages = [
    'cuds',
    'cuds.classes',
    'cuds.classes.generated',
    'cuds.session',
    'cuds.session.db',
    'cuds.session.transport',
    'cuds.generator',
    'cuds.ontology',
    'cuds.testing'
]

# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005)',
    url='www.simphony-project.eu',
    description='The native implementation of the SimPhoNy cuds objects',
    keywords='simphony, cuds, Fraunhofer IWM',
    long_description=README_TEXT,
    packages=packages,
    cmdclass={
        'install': Install,
        'develop': Develop
    },
    test_suite='cuds.testing',
    entry_points={
        'console_scripts': [
            'simphony-class-generator = cuds.generator.class_generator:main',
            'cuds2dot = cuds.ontology.utils.cuds2dot:main'],
        'wrappers': 'osp-core = cuds.classes:Cuds'
    }
)
