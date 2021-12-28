"""Tests the wrapper as user-facing session management interface."""

import multiprocessing
import os
import socket
import tempfile
import time
import unittest
from typing import Optional

from osp.core.utils.datatypes import Vector
from osp.core.ontology.parser import OntologyParser
from osp.core.session.interfaces.remote.server import RemoteStoreServer
from osp.core.session.interfaces.sql import SQLStore
from osp.core.session.session import Session
from osp.interfaces.sqlite.interface import SQLiteInterface


class TestWrapper(unittest.TestCase):
    """Test the full end-user experience of using wrapper.

    The wrapper used for the test is the `sqlite` wrapper.
    """

    file_name: str = "TestSQLiteSession"

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        ontology = Session(identifier='test_tbox', ontology=True)
        for parser in (OntologyParser.get_parser('cuba'),
                       OntologyParser.get_parser('owl'),
                       OntologyParser.get_parser('rdfs'),
                       OntologyParser.get_parser('city')):
            ontology.load_parser(parser)
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
        from osp.core.namespaces import city
        from osp.wrappers import sqlite

        with sqlite(self.file_name) as wrapper:
            freiburg = city.City(name='Freiburg', coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(iri='http://example.org/citizens#Marco',
                                 name='Marco',
                                 age=50)
            matthias = city.Citizen(name='Matthias', age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            self.assertIn(marco, set(wrapper))
            self.assertIn(matthias, set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual({marco, matthias, freiburg}, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            self.assertEqual(freiburg.name, 'Freiburg')
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, 'Marco')
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, 'Matthias')
            self.assertEqual(matthias.age, 37)
            wrapper.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with sqlite(self.file_name) as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            citizens = list(freiburg[city.hasInhabitant])

            self.assertEqual('Freiburg', freiburg.name)
            self.assertEqual([20, 58], freiburg.coordinates)
            self.assertSetEqual(
                {'Marco', 'Matthias'},
                {citizen.name for citizen in citizens}
            )
            self.assertSetEqual(
                {50, 37},
                {citizen.age for citizen in citizens}
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

        pr = city.City(name='Paris', coordinates=[0, 0])

        with sqlite(self.file_name) as wrapper:
            self.assertEqual(len(wrapper), 0)
            wrapper.add(pr)
            wrapper.commit()

        with sqlite(self.file_name) as wrapper:
            self.assertEqual(len(wrapper), 1)
            paris = set(wrapper).pop()
            self.assertEqual(paris.name, 'Paris')

    def test_wrapper_root(self) -> None:
        """Test using an ontology entity as wrapper."""
        from osp.core.namespaces import city
        from osp.wrappers import sqlite

        fr = city.City(iri='http://example.org/Freiburg', name='Freiburg',
                       coordinates=[0, 0])

        with sqlite(self.file_name, root=fr) as freiburg_as_wrapper_1:
            marco = city.Citizen(iri='http://example.org/citizens#Marco',
                                 name='Marco',
                                 age=50)
            matthias = city.Citizen(name='Matthias', age=37)

            freiburg_as_wrapper_1[city.hasInhabitant] = {marco, matthias}

            freiburg_as_wrapper_1.commit()

        with sqlite(self.file_name, root='http://example.org/Freiburg') \
                as freiburg_as_wrapper_2:
            citizens = list(freiburg_as_wrapper_2[city.hasInhabitant])

            self.assertEqual('Freiburg', freiburg_as_wrapper_2.name)
            self.assertSetEqual(
                {'Marco', 'Matthias'},
                {citizen.name for citizen in citizens}
            )
            self.assertSetEqual(
                {50, 37},
                {citizen.age for citizen in citizens}
            )


class TestDataspaceWrapper(unittest.TestCase):
    """Test the full end-user experience of using wrapper.

    The wrapper used for the test is the `dataspace` wrapper.
    """

    server_proc = None
    host: str = "127.0.0.1"
    port: int = 4745
    db_file: str = 'public.db'
    server_files_dir: Optional[str] = None
    server_files_dir_object: Optional[tempfile.TemporaryDirectory] = None

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        ontology = Session(identifier='test_tbox', ontology=True)
        for parser in (OntologyParser.get_parser('cuba'),
                       OntologyParser.get_parser('owl'),
                       OntologyParser.get_parser('rdfs'),
                       OntologyParser.get_parser('city')):
            ontology.load_parser(parser)
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def setUp(self) -> None:
        """Start a RemoteStoreServer for a new test."""
        self.start_server(files_uid=True)

    def tearDown(self):
        """Stop a RemoteStoreServer after a test."""
        self.stop_server()
        for file in os.listdir():
            if 'test_wrapper_dataspace_db' in file:
                os.remove(file)

    @staticmethod
    def server_store_generator(configuration_string: str) -> SQLStore:
        """Produces a store for the server from a configuration string."""
        interface = SQLiteInterface()
        store = SQLStore(interface=interface)
        store.open(configuration_string or f"{TestDataspaceWrapper.db_file}")
        return store

    def start_server(self, files_uid: bool = False):
        """Start a RemoteStoreServer."""
        if self.server_proc:
            self.server_proc.terminate()
            self.server_proc.join(30)
            self.server_proc.kill()
            self.server_proc.join()
            self.server_proc.close()
        self.server_files_dir_object = tempfile.TemporaryDirectory()
        self.server_files_dir = self.server_files_dir_object.name
        self.server_proc = multiprocessing.Process(
            target=self.launch_server, kwargs={'files_uid': files_uid})
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

    def launch_server(self, files_uid: bool = False):
        """Launch a RemoteStoreServer."""
        server = RemoteStoreServer(host=self.host,
                                   port=self.port,
                                   generate_store=self.server_store_generator,
                                   file_destination=self.server_files_dir,
                                   file_uid=files_uid)
        server.start()
        exit(0)

    def stop_server(self):
        """Stop a running RemoteStoreServer."""
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

    def test_wrapper_city(self) -> None:
        """Test adding some entities from the city ontology."""
        from osp.core.namespaces import city
        from osp.wrappers import dataspace

        with dataspace(f'ws://username:password@{self.host}:{self.port}',
                       'test_wrapper_dataspace_db_main.db'
                       ) as wrapper:
            freiburg = city.City(name='Freiburg', coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(iri='http://example.org/citizens#Marco',
                                 name='Marco',
                                 age=50)
            matthias = city.Citizen(name='Matthias', age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

            self.assertIn(marco, set(wrapper))
            self.assertIn(matthias, set(wrapper))
            self.assertIn(freiburg, set(wrapper))
            self.assertSetEqual({marco, matthias, freiburg}, set(wrapper))
            self.assertTrue(len(wrapper), 3)

            self.assertEqual(freiburg.name, 'Freiburg')
            self.assertEqual(freiburg.coordinates, [20, 58])
            self.assertEqual(marco.name, 'Marco')
            self.assertEqual(marco.age, 50)
            self.assertEqual(matthias.name, 'Matthias')
            self.assertEqual(matthias.age, 37)
            wrapper.commit()
            freiburg.coordinates = Vector([22, 58])
            self.assertEqual(freiburg.coordinates, [22, 58])

        with dataspace(f'ws://username:password@{self.host}:{self.port}',
                       'test_wrapper_dataspace_db_main.db'
                       ) as wrapper:
            freiburg = wrapper.from_identifier(freiburg_identifier)
            citizens = list(freiburg[city.hasInhabitant])

            self.assertEqual('Freiburg', freiburg.name)
            self.assertEqual([20, 58], freiburg.coordinates)
            self.assertSetEqual(
                {'Marco', 'Matthias'},
                {citizen.name for citizen in citizens}
            )
            self.assertSetEqual(
                {50, 37},
                {citizen.age for citizen in citizens}
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

        pr = city.City(name='Paris', coordinates=[0, 0])

        with dataspace(f'ws://username:password@{self.host}:{self.port}',
                       'test_wrapper_dataspace_db_main.db'
                       ) as wrapper:
            self.assertEqual(len(wrapper), 0)
            wrapper.add(pr)
            wrapper.commit()

        with dataspace(f'ws://username:password@{self.host}:{self.port}',
                       'test_wrapper_dataspace_db_main.db'
                       ) as wrapper:
            self.assertEqual(len(wrapper), 1)
            paris = set(wrapper).pop()
            self.assertEqual(paris.name, 'Paris')

        with dataspace(f'ws://username:password@{self.host}:{self.port}') \
                as wrapper:
            self.assertEqual(len(wrapper), 0)


if __name__ == "__main__":
    unittest.main()
