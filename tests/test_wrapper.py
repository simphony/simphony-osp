"""Tests the wrapper as user-facing session management interface."""

import filecmp
import multiprocessing
import os
import socket
import time
import unittest
from base64 import b64encode
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional

from rdflib import XSD, Literal

from simphony_osp.ontology.parser import OntologyParser
from simphony_osp.session.session import Session
from simphony_osp.session.wrapper import Wrapper
from simphony_osp.tools import host
from simphony_osp.utils.datatypes import Vector
from simphony_osp.wrappers import Dataspace, Remote, SQLite


class TestWrapper(unittest.TestCase):
    """Test the full end-user experience of using a wrapper.

    The wrapper used for the test is the `SQLite` wrapper.
    """

    file_name: str = "TestSQLiteSession"

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and City.
        """
        ontology = Session(identifier="test_tbox", ontology=True)
        ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def tearDown(self) -> None:
        """Remove the database file."""
        try:
            os.remove(self.file_name)
        except FileNotFoundError:
            pass

    def test_wrapper_city(self) -> None:
        """Test adding some entities from the city ontology."""
        from simphony_osp.namespaces import city
        from simphony_osp.wrappers import SQLite

        with SQLite(self.file_name, create=True) as wrapper:
            freiburg = city.City(name="Freiburg", coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(
                iri="http://example.org/citizens#Marco", name="Marco", age=50
            )
            matthias = city.Citizen(name="Matthias", age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            self.assertIn(marco, set(wrapper))
            self.assertIn(matthias, set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual({marco, matthias, freiburg}, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            self.assertEqual(freiburg.name, "Freiburg")
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, "Marco")
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, "Matthias")
            self.assertEqual(matthias.age, 37)
            wrapper.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with SQLite(self.file_name) as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            citizens = list(freiburg[city.hasInhabitant])

            self.assertEqual("Freiburg", freiburg.name)
            self.assertEqual([20, 58], freiburg.coordinates)
            self.assertSetEqual(
                {"Marco", "Matthias"}, {citizen.name for citizen in citizens}
            )
            self.assertSetEqual(
                {50, 37}, {citizen.age for citizen in citizens}
            )

            everything = {*citizens, freiburg}
            self.assertIn(citizens[0], set(wrapper))
            self.assertIn(citizens[1], set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual(everything, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            wrapper.delete(*citizens)
            self.assertEqual(len(wrapper), 1)
            self.assertEqual(len(freiburg[city.hasInhabitant]), 0)

            wrapper.delete(freiburg)
            self.assertEqual(len(wrapper), 0)

            wrapper.commit()

        pr = city.City(name="Paris", coordinates=[0, 0])

        with SQLite(self.file_name) as wrapper:
            self.assertEqual(len(wrapper), 0)
            wrapper.add(pr)
            wrapper.commit()

        with SQLite(self.file_name) as wrapper:
            self.assertEqual(len(wrapper), 1)
            paris = set(wrapper).pop()
            self.assertEqual(paris.name, "Paris")

    def test_wrapper_sparql(self) -> None:
        """Test SPARQL queries on wrappers."""
        from simphony_osp.namespaces import city, simphony
        from simphony_osp.tools import sparql
        from simphony_osp.wrappers import SQLite

        with SQLite(self.file_name, create=True) as wrapper:
            freiburg = city.City(name="Freiburg", coordinates=[20, 58])
            marco = city.Citizen(
                iri="http://example.org/citizens#Marco", name="Marco", age=50
            )
            matthias = city.Citizen(name="Matthias", age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            result = list(
                sparql(
                    f"""
                SELECT ?age WHERE {{
                    <{matthias.iri}> <{city.age.iri}> ?age .
                }}
            """
                )
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0]), 1)
            self.assertEqual(Literal("37", datatype=XSD.integer), result[0][0])


class TestDataspaceWrapper(unittest.TestCase):
    """Test the full end-user experience of using a wrapper.

    The wrapper used for the test is the `dataspace` wrapper.
    """

    prev_default_ontology: Session

    dataspace_directory: TemporaryDirectory

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and City.
        """
        ontology = Session(identifier="test_tbox", ontology=True)
        ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def setUp(self) -> None:
        """Create a temporary directory for files."""
        self.dataspace_directory = TemporaryDirectory()

    def tearDown(self) -> None:
        """Clean the temporary directory for files."""
        self.dataspace_directory.cleanup()

    def test_wrapper_city(self) -> None:
        """Test adding some entities from the city ontology."""
        from simphony_osp.namespaces import city

        with Dataspace(self.dataspace_directory.name, True) as wrapper:
            freiburg = city.City(name="Freiburg", coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(
                iri="http://example.org/citizens#Marco", name="Marco", age=50
            )
            matthias = city.Citizen(name="Matthias", age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            self.assertIn(marco, set(wrapper))
            self.assertIn(matthias, set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual({marco, matthias, freiburg}, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            self.assertEqual(freiburg.name, "Freiburg")
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, "Marco")
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, "Matthias")
            self.assertEqual(matthias.age, 37)
            wrapper.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with Dataspace(self.dataspace_directory.name, False) as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            citizens = list(freiburg[city.hasInhabitant])

            self.assertEqual("Freiburg", freiburg.name)
            self.assertEqual([20, 58], freiburg.coordinates)
            self.assertSetEqual(
                {"Marco", "Matthias"}, {citizen.name for citizen in citizens}
            )
            self.assertSetEqual(
                {50, 37}, {citizen.age for citizen in citizens}
            )

            everything = {*citizens, freiburg}
            self.assertIn(citizens[0], set(wrapper))
            self.assertIn(citizens[1], set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual(everything, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            wrapper.delete(*citizens)
            self.assertEqual(len(wrapper), 1)
            self.assertEqual(len(freiburg[city.hasInhabitant]), 0)

            wrapper.delete(freiburg)
            self.assertEqual(len(wrapper), 0)

            wrapper.commit()

        pr = city.City(name="Paris", coordinates=[0, 0])

        with Dataspace(self.dataspace_directory.name, False) as wrapper:
            self.assertEqual(len(wrapper), 0)
            wrapper.add(pr)
            wrapper.commit()

        with Dataspace(self.dataspace_directory.name, False) as wrapper:
            self.assertEqual(len(wrapper), 1)
            paris = set(wrapper).pop()
            self.assertEqual(paris.name, "Paris")
            wrapper.delete(paris)
            wrapper.commit()

        with Dataspace(self.dataspace_directory.name, False) as wrapper:
            self.assertEqual(len(wrapper), 0)

    def test_files(self):
        """Test handling files."""
        from simphony_osp.namespaces import simphony

        with NamedTemporaryFile("w", suffix=".txt") as os_file:
            os_file.write("text")

            # Test creating file object and filling it with a file.
            with Dataspace(self.dataspace_directory.name, True) as wrapper:
                file = simphony.File()
                file_identifier = file.identifier
                file.upload(os_file.name)
                file_name = b64encode(
                    bytes(file_identifier, encoding="UTF-8")
                ).decode("UTF-8")
                self.assertFalse(
                    (
                        Path(self.dataspace_directory.name)
                        / "files"
                        / file_name
                    ).is_file()
                )
                wrapper.commit()
                self.assertTrue(
                    filecmp.cmp(
                        os_file.name,
                        Path(self.dataspace_directory.name)
                        / "files"
                        / file_name,
                        shallow=False,
                    )
                )

            # Test recovering the previous file and downloading it.
            with Dataspace(self.dataspace_directory.name, False) as wrapper:
                file = wrapper.from_identifier(file_identifier)
                with TemporaryDirectory() as temp_dir:
                    destination = Path(temp_dir) / "filename"
                    self.assertFalse(destination.is_file())
                    file.download(destination)
                    self.assertTrue(destination.is_file())

            # Test deleting the file.
            with Dataspace(self.dataspace_directory.name, False) as wrapper:
                file = wrapper.from_identifier(file_identifier)
                wrapper.delete(file)
                wrapper.commit()
                self.assertFalse(
                    any(
                        (
                            Path(self.dataspace_directory.name) / "files"
                        ).iterdir()
                    )
                )
                self.assertRaises(
                    KeyError, wrapper.from_identifier, file_identifier
                )
                wrapper.commit()

            # Test that the file remains deleted.
            with Dataspace(self.dataspace_directory.name, False) as wrapper:
                self.assertRaises(
                    KeyError, wrapper.from_identifier, file_identifier
                )


class TestRemoteSQLite(unittest.TestCase):
    """Test the Remote wrapper.

    The wrapper used for the test on the remote side is the `sqlite` wrapper.
    """

    server_proc = None
    host: str = "127.0.0.1"
    port: int = 4745
    db_file: str = "test_db_file.db"
    server_files_dir: Optional[str] = None
    server_files_dir_object: Optional[TemporaryDirectory] = None

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains SimPhoNy, OWL, RDFS and City.
        """
        ontology = Session(identifier="test_tbox", ontology=True)
        ontology.load_parser(OntologyParser.get_parser("city"))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def setUp(self) -> None:
        """Start the InterfaceServer for a new test."""
        self.start_server()

    def tearDown(self):
        """Stop the InterfaceServer after a test."""
        self.stop_server()

    def start_server(self):
        """Start an InterfaceServer."""
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc.join(30)
            self.server_proc.kill()
            self.server_proc.join()
            self.server_proc.close()
        self.server_proc = multiprocessing.Process(target=self.launch_server)
        self.server_proc.start()
        s = socket.socket()
        connected = False
        tries = 0
        while not connected and tries < 1000:
            time.sleep(0.3)
            tries += 1
            try:
                s.connect((self.host, int(self.port)))
                connected = True
            except socket.error:
                pass
            finally:
                s.close()

    def launch_server(self):
        """Launch an InterfaceServer."""
        host(
            SQLite,
            TestRemoteSQLite.db_file,
            True,
            hostname=self.host,
            port=self.port,
            username="user",
            password="pass",
        )
        exit(0)

    def stop_server(self):
        """Stop a running InterfaceServer."""
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc.join(30)
            self.server_proc.kill()
            self.server_proc.join()
            self.server_proc.close()
        for file in os.listdir():
            if self.db_file in file:
                os.remove(file)
        if self.server_files_dir_object is not None:
            self.server_files_dir_object.cleanup()
            self.server_files_dir_object = None
            self.server_files_dir = None
        self.server_proc = None

    def wrapper_generator(self) -> Wrapper:
        """Generate a wrapper object using the Remote wrapper."""
        wrapper = Remote(f"ws://user:pass@{self.host}:{self.port}")
        return wrapper

    def test_city(self):
        """Test adding some entities from the city ontology."""
        from simphony_osp.namespaces import city

        with self.wrapper_generator() as wrapper:
            freiburg = city.City(name="Freiburg", coordinates=[0, 0])
            klaus = city.Citizen(name="Klaus", age=30)
            freiburg[city.hasInhabitant] = klaus
            freiburg_identifier = freiburg.identifier
            wrapper.commit()
        del freiburg

        with self.wrapper_generator() as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            klaus = freiburg[city.hasInhabitant].one()
            self.assertEqual(freiburg.name, "Freiburg")
            self.assertEqual(klaus.name, "Klaus")
            self.assertEqual(klaus.age, 30)
            wrapper.delete(klaus)
            self.assertIsNone(freiburg[city.hasInhabitant].any())
            wrapper.commit()
        del freiburg

        with self.wrapper_generator() as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            self.assertIsNone(freiburg[city.hasInhabitant].any())


if __name__ == "__main__":
    unittest.main()
