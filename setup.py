import os
import sys
import subprocess
import shutil
from setuptools import setup, find_packages
from packageinfo import VERSION, NAME
from setuptools.command.develop import develop
from setuptools.command.install import install


# Read description
with open('README.md', 'r') as readme:
    README_TEXT = readme.read()

with open("packageinfo.py", "r") as packageinfo:
    with open(os.path.join("osp", "core", "packageinfo.py"), "w") as f:
        print("# DO NOT MODIFY", file=f)
        for line in packageinfo:
            print(line, file=f, end="")
        print("# DO NOT MODIFY", file=f)


def build_dependencies(force_dependency_download):
    x = os.path.join(os.path.dirname(__file__), "download_dependencies.sh")
    if force_dependency_download:
        shutil.rmtree(os.path.join(os.path.dirname(__file__),
                                   "osp", "core", "java", "lib"))
    subprocess.run(["bash", x], check=True)
    try:
        subprocess.run(["mvn", "-Dmaven.test.skip=true",
                        "clean", "package", "-f", "osp/core/java/pom.xml"])
        target_dir = os.path.join("osp", "core", "java", "target")
        lib_dir = os.path.join("osp", "core", "java", "lib", "jars")
        for file in os.listdir(target_dir):
            if file.endswith(".jar"):
                os.replace(os.path.join(target_dir, file),
                           os.path.join(lib_dir, file))
    except Exception as e:
        raise RuntimeError(
            "Error building parser. "
            "Make sure Maven and JDK are installed.") from e


if (
    ("install" in sys.argv or "develop" in sys.argv)
    and "-h" not in sys.argv
    and "--help" not in sys.argv
):
    build_dependencies("--force-dependency-download" in sys.argv)


class Install(install):
    user_options = install.user_options + [
        ('force-dependency-download', None, 'Force the download of dependencies')
    ]

    def initialize_options(self):
        install.initialize_options(self)
        self.force_dependency_download = ""


class Develop(develop):
    user_options = develop.user_options + [
        ('force-dependency-download', None, 'Force the download of dependencies')
    ]

    def initialize_options(self):
        develop.initialize_options(self)
        self.force_dependency_download = ""


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
        "osp.core.java.lib.jars": ["*.jar"]
    },
    include_package_data=True,
    python_requires=">=3.6",
    cmdclass={
        'develop': Develop,
        'install': Install
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
