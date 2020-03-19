import os
import subprocess
from setuptools import setup, find_packages
from packageinfo import VERSION, NAME
from setuptools.command.install import install
from setuptools.command.develop import develop


# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()

with open("packageinfo.py", "r") as packageinfo:
    with open(os.path.join("osp", "core", "packageinfo.py"), "w") as f:
        print("# DO NOT MODIFY", file=f)
        for line in packageinfo:
            print(line, file=f, end="")
        print("# DO NOT MODIFY", file=f)


def install_factplusplus():
    x = os.path.join(os.path.dirname(__file__), "install_factplusplus.sh")
    subprocess.run(["bash", x])
    try:
        subprocess.run(["mvn", "-Dmaven.test.skip=true",
                        "package", "-f", "osp/core/java/pom.xml"])
    except Exception as e:
        raise RuntimeError(
            "Error building parser. "
            "Make sure Maven and JDK is installed.") from e


class Install(install):
    def run(self):
        install_factplusplus()
        install.run(self)


class Develop(develop):
    def run(self):
        install_factplusplus()
        develop.run(self)


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
        "osp.core.ontology.yml": ["*.yml"],
        "osp.core.java.lib.so": ["*"],
        "osp.core.java.lib.jars": ["*.jar"],
        "osp.core.java.target": ["*.jar"]
    },
    python_requires=">=3.6",
    cmdclass={
        'install': Install,
        'develop': Develop
    },
    entry_points={
        'wrappers': 'osp-core = osp.core.session.core_session:CoreSession',
        'console_scripts': {
            'owl2yml = osp.core.tools.owl2yml:run_from_terminal',
            'pico = osp.core.ontology.installation:install_from_terminal',
            'ontology2dot = osp.core.tools.ontology2dot:run_from_terminal'
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
