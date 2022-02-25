"""Install SimPhoNy."""

import os

from setuptools import setup, find_packages

from packageinfo import VERSION, NAME


# Read description
with open('README.md', 'r', encoding="utf8") as readme:
    README_TEXT = readme.read()

with open("packageinfo.py", "r", encoding="utf8") as package_info:
    with open(os.path.join("simphony_osp", "core", "packageinfo.py"),
              "w", encoding="utf8") as f:
        for line in package_info:
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
        "simphony_osp.core.ontology.files": ["*.yml", "*.ttl", "*.xml",
                                             "*.owl"],
    },
    include_package_data=True,
    python_requires=">=3.7",
    entry_points={
        'console_scripts': {
            'pico = simphony_osp.core.utils.pico:pico',
            'semantic2dot = simphony_osp.core.tools.semantic2dot'
            ':run_from_terminal',
        }
    },
    install_requires=[
        "PyYaml",
        "websockets < 10",
        "requests",
        "numpy",
        "graphviz",
        "rdflib >= 6.0.2, < 7.0.0",
        "rdflib-sqlalchemy >= 0.5.0",
    ],
    setup_requires=[
    ],
)
