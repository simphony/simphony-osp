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
    description="Framework for creating interfaces between ontologies "
    "and software such as simulation engines, databases and data "
    "repositories.",
    long_description=README_TEXT,
    long_description_content_type="text/markdown",
    url="https://github.com/simphony/simphony-osp/tree/v4.0.0",
    author="SimPhoNy, EU FP7 Project (Nr. 604005)",
    maintainer="Fraunhofer IWM",
    maintainer_email="simphony@iwm.fraunhofer.de",
    license="BSD-3-Clause",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: Unix",
    ],
    keywords="owl, ontology, interoperability, materials-science, osp, "
    "simphony, wrappers, open-simulation-platform, knowledge-graph"
    "Fraunhofer IWM",
    download_url="https://pypi.org/project/simphony-osp/4.0.0/",
    project_urls={
        "Tracker": "https://github.com/simphony/simphony-osp/issues",
        "Documentation": "https://simphony.readthedocs.io/en/v4.0.0/",
        "Source": "https://github.com/simphony/simphony-osp/tree/v4.0.0",
    },
    packages=find_packages(exclude=("examples", "tests")),
    install_requires=[
        "graphviz",
        "numpy",
        "PyYaml",
        "rdflib >= 6.0.2, < 7.0.0",
        "rdflib-sqlalchemy >= 0.5.0",
        "requests",
        "importlib-metadata >= 5, < 6; python_version <= '3.7'",
        "websockets >= 9, < 11",
        "websockets >= 10; python_version >= '3.10'",
    ],
    python_requires=">=3.7",
    package_data={
        "simphony_osp.ontology.files": [
            "*.yml",
            "*.ttl",
            "*.xml",
            "*.owl",
        ],
    },
    include_package_data=True,
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
)
