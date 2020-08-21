import os
from setuptools import setup, find_packages
from packageinfo import VERSION, NAME


# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()

with open("packageinfo.py", "r") as packageinfo:
    with open(os.path.join("osp", "core", "packageinfo.py"), "w") as f:
        print("# DO NOT MODIFY", file=f)
        for line in packageinfo:
            print(line, file=f, end="")
        print("# DO NOT MODIFY", file=f)


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005)',
    url='www.simphony-project.eu',
    description='The native implementation of the SimPhoNy cuds objects',
    keywords='simphony, cuds, Fraunhofer IWM',
    long_description=README_TEXT,
    packages=find_packages(exclude=("examples", "tests")),
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
        "websockets",
        "requests",
        "numpy",
        "graphviz",
        "owlready2",
        "rdflib"
    ],
    setup_requires=[
        "PyYaml",
        "websockets",
        "requests",
        "numpy",
        "graphviz",
        "owlready2",
        "rdflib"
    ]
)
