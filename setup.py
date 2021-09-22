"""Install osp-core."""

import os
from setuptools import setup, find_packages
from packageinfo import VERSION, NAME


# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()

with open("packageinfo.py", "r") as packageinfo:
    with open(os.path.join("osp", "core", "packageinfo.py"), "w") as f:
        for line in packageinfo:
            print(line, file=f, end="")
        for i in range(10):
            print("# DO NOT MODIFY. Modify the file in the repository's root.",
                  file=f)


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005)',
    url='www.simphony-project.eu',
    description='The native implementation of the SimPhoNy cuds objects',
    keywords='simphony, cuds, Fraunhofer IWM',
    long_description=README_TEXT,
    packages=find_packages(
        exclude=("examples",
                 "tests")),
    package_data={
        "osp.core.ontology.docs": ["*.yml", "*.ttl", "*.xml", "EMMO/*.owl"],
    },
    include_package_data=True,
    python_requires=">=3.6",
    entry_points={
        'wrappers': 'osp-core = osp.core.session.core_session:CoreSession',
        'console_scripts': {
            'owl2yml = osp.core.tools.owl2yml:run_from_terminal',
            'pico = osp.core.pico:install_from_terminal',
            'ontology2dot = osp.core.tools.ontology2dot:run_from_terminal',
            'yaml2camelcase = osp.core.tools.yaml2camelcase:run_from_terminal'
        }
    },
    install_requires=[
        "PyYaml",
        "websockets < 10",
        "requests",
        "numpy",
        "graphviz",
        "rdflib >= 5.0.0, < 6.0.0; python_version < '3.7'",
        "rdflib >= 6.0.0, < 7.0.0; python_version >= '3.7'",
        "rdflib-jsonld <= 0.5.0; python_version < '3.7'",
    ],
    setup_requires=[
        "PyYaml",
        "websockets < 10",
        "requests",
        "numpy",
        "graphviz",
        "rdflib >= 5.0.0, < 6.0.0; python_version < '3.7'",
        "rdflib >= 6.0.0, < 7.0.0; python_version >= '3.7'",
        "rdflib-jsonld <= 0.5.0; python_version < '3.7'",
    ],
)
