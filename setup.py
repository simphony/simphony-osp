"""Install osp-core."""

import os

from setuptools import setup, find_packages

from packageinfo import VERSION, NAME


# Read description
with open('README.md', 'r', encoding="utf8") as readme:
    README_TEXT = readme.read()

with open("packageinfo.py", "r", encoding="utf8") as packageinfo:
    with open(os.path.join("osp", "core", "packageinfo.py"),
              "w", encoding="utf8") as f:
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
        "osp.core.ontology.files": ["*.yml", "*.ttl", "*.xml", "*.owl"],
    },
    include_package_data=True,
    python_requires=">=3.7",
    entry_points={
        'console_scripts': {
            'pico = osp.core.utils.pico:pico',
            'semantic2dot = osp.core.tools.semantic2dot:run_from_terminal',
        }
    },
    install_requires=[
        "PyYaml",
        "websockets < 10",
        "requests",
        "numpy",
        "graphviz",
        "rdflib",  # Redundant, but some IDEs do not understand what is below.
        "rdflib >= 6.0.0, < 7.0.0",
    ],
    setup_requires=[
    ],
)
