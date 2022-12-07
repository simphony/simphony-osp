"""Install OSP-core."""

import os

from setuptools import find_packages, setup

from packageinfo import NAME, VERSION

# Read `README.md` file.
with open("README.md", "r", encoding="utf8") as readme:
    README_TEXT = readme.read()

# Copy `packageinfo.py` to the `osp.core` module.
with open("packageinfo.py", "r", encoding="utf8") as packageinfo:
    with open(
        os.path.join("osp", "core", "packageinfo.py"), "w", encoding="utf8"
    ) as f:
        for line in packageinfo:
            print(line, file=f, end="")
        for i in range(10):
            print(
                "# DO NOT MODIFY. Modify the file in the repository's root.",
                file=f,
            )


setup(
    name=NAME,
    version=VERSION,
    description="The native implementation of the SimPhoNy CUDS objects",
    long_description=README_TEXT,
    long_description_content_type="text/markdown",
    url="https://github.com/simphony",
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
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: Unix",
    ],
    keywords="owl ontology interoperability materials-science osp simphony "
    "wrappers cuds open-simulation-platform",
    download_url="https://pypi.python.org/pypi/osp-core",
    project_urls={
        "Tracker": "https://github.com/simphony/osp-core/issues",
        "Documentation": "https://simphony.readthedocs.io",
        "Source": "https://github.com/simphony/osp-core",
    },
    packages=find_packages(exclude=("examples", "tests")),
    install_requires=[
        "graphviz",
        "numpy",
        "PyYaml",
        "rdflib >= 6.0.0, < 7.0.0; python_version >= '3.7'",
        "requests",
        "websockets >= 9, < 11",
        "websockets >= 10; python_version >= '3.10'",
        # ↓ --- Python 3.6 support. --- ↓ #
        "pyparsing < 3.0.0; python_version < '3.7'",
        "rdflib >= 5.0.0, < 6.0.0; python_version < '3.7'",
        "rdflib-jsonld == 0.6.1; python_version < '3.7'",
        # 🠕 Required by rdflib >= 5.0.0, < 6.0.0, otherwise no SPARQL support.
        # ↑ --- Python 3.6 support. --- ↑ #
    ],
    python_requires=">=3.6",
    package_data={
        "osp.core.ontology.docs": ["*.yml", "*.ttl", "*.xml"],
    },
    data_files=[(".", ["packageinfo.py"])],
    include_package_data=True,
    entry_points={
        "wrappers": "osp-core = osp.core.session.core_session:CoreSession",
        "console_scripts": {
            "owl2yml = osp.core.tools.owl2yml:run_from_terminal",
            "pico = osp.core.pico:terminal",
            "ontology2dot = osp.core.tools.ontology2dot:run_from_terminal",
            "yaml2camelcase = osp.core.tools.yaml2camelcase:run_from_terminal",
        },
    },
)
