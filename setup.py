"""Install SimPhoNy."""

from setuptools import find_packages, setup

# Read description
with open("README.md", "r", encoding="utf8") as readme:
    README_TEXT = readme.read()

NAME = "simphony-osp"
VERSION = "4.0.0"

# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author="SimPhoNy, EU FP7 Project (Nr. 604005)",
    url="www.simphony-project.eu",
    description="The native implementation of the SimPhoNy cuds objects",
    keywords="simphony, cuds, Fraunhofer IWM",
    long_description=README_TEXT,
    packages=find_packages(exclude=("examples", "tests")),
    package_data={
        "simphony_osp.ontology.files": [
            "*.yml",
            "*.ttl",
            "*.xml",
            "*.owl",
        ],
    },
    include_package_data=True,
    python_requires=">=3.7",
    entry_points={
        "simphony_osp.wrappers": {
            "SQLAlchemy = simphony_osp.interfaces.sqlalchemy:SQLAlchemy",
            "SQLite = simphony_osp.interfaces.sqlite:SQLite",
            "Dataspace = simphony_osp.interfaces.dataspace:Dataspace",
            "Remote = simphony_osp.interfaces.remote:Remote",
        },
        "simphony_osp.ontology.operations": {
            "File = simphony_osp.ontology.operations.file:File",
            "Container = simphony_osp.ontology.operations.container:Container",
        },
        "console_scripts": {
            "pico = simphony_osp.tools.pico:terminal",
            "semantic2dot = simphony_osp.tools.semantic2dot:terminal",
        },
    },
    install_requires=[
        "graphviz",
        "numpy",
        "PyYaml",
        "rdflib >= 6.0.2, < 7.0.0",
        "rdflib-sqlalchemy >= 0.5.0",
        "requests",
        "websockets < 11",
        "websockets >= 10; python_version >= '3.10'",
    ],
    setup_requires=[],
)
