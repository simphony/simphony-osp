import os

from setuptools import setup
from subprocess import check_call
from setuptools.command.install import install
from setuptools.command.develop import develop
from packageinfo import VERSION, NAME

# Should be in install_requires, but needed for ClassGenerator import
check_call(["pip", "install", "-r", "requirements.txt"])
from cuds.metatools.class_generator import ClassGenerator

# Read description
with open('README.rst', 'r') as readme:
    README_TEXT = readme.read()


def create_ontology_classes(ontology):
    ontology_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'cuds', 'ontology', ontology)
    template_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'cuds', 'metatools', 'template')

    if not os.path.exists(ontology_file):
        message = 'Unrecoverable error. Cannot find ' + ontology + ' file in {}'
        raise RuntimeError(message.format(ontology_file))

    if not os.path.exists(template_file):
        message = 'Unrecoverable error. Cannot find \'template\' file in {}'
        raise RuntimeError(message.format(template_file))

    print('Building classes from ontology...')
    ClassGenerator(ontology_file, template_file, "cuds/classes/generated").generate_classes()


class Install(install):
    # The format is (long option, short option, description).
    user_options = install.user_options + [
        ('toy', 't', 'install using toy ontology')
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.toy = ''

    def run(self):
        if self.toy:
            create_ontology_classes('ontology_toy.yml')
        else:
            create_ontology_classes('ontology_stable.yml')
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
    'cuds.metatools',
    'cuds.classes.core',
    'cuds.classes.generated',
    'cuds.ontology',
    'cuds.ontology.tools',
    'testing'
]

# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005)',
    url='www.simphony-project.eu',
    description='The native implementation of the SimPhoNy cuds objects',
    keywords='simphony, cuds, Fraunhofer IWM, Marketplace',
    long_description=README_TEXT,
    packages=packages,
    cmdclass={
        'install': Install,
        'develop': Develop
    },
    test_suite='testing.api_test',
    entry_points={
        'console_scripts': [
            'simphony-class-generator = cuds.metatools.class_generator:main',
            'cuds2dot = cuds.ontology.tools.cuds2dot:main']
    }
)
