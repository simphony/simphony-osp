"""Test the interface API to communicate with external software."""

import filecmp
import multiprocessing
import os
import shutil
import socket
import tempfile
import time
import unittest
from typing import Optional

from rdflib import Graph

from osp.core.utils.datatypes import Vector
from osp.core.ontology.parser import OntologyParser
from osp.core.interfaces.interface import InterfaceDriver

from osp.core.interfaces.remote.client import RemoteStoreClient
from osp.core.interfaces.remote.server import RemoteStoreServer
from osp.core.session import Session
from osp.interfaces.sqlite.interface import SQLiteInterface
from osp.wrappers import sqlite


class TestWrapper(unittest.TestCase):
    """Test the full end-user experience of using a triplestore wrapper.

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
        ontology.load_parser(OntologyParser.get_parser('city'))
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

    def test_city(self) -> None:
        """Test adding some entities from the city ontology."""
        from osp.core.namespaces import city

        with sqlite(self.file_name, create=True) as wrapper:
            freiburg = city.City(name='Freiburg', coordinates=[20, 58])
            freiburg_identifier = freiburg.identifier
            marco = city.Citizen(name='Marco', age=50)
            matthias = city.Citizen(name='Matthias', age=37)
            freiburg[city.hasInhabitant] = {marco, matthias}

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
            freiburg = wrapper.session.from_identifier(freiburg_identifier)
            citizens = freiburg[city.hasInhabitant]

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


class TestRemoteStoreSQLite(unittest.TestCase):
    """Test the RemoteStoreClient store.

    The wrapper used for the test on the remote side is the `sqlite` wrapper.
    """

    server_proc = None
    host: str = "127.0.0.1"
    port: int = 4745
    db_file: str = 'test_db_file.db'
    server_files_dir: Optional[str] = None
    server_files_dir_object: Optional[tempfile.TemporaryDirectory] = None

    prev_default_ontology: Session

    @classmethod
    def setUpClass(cls):
        """Create a TBox and set it as the default ontology.

        The new TBox contains CUBA, OWL, RDFS and City.
        """
        ontology = Session(identifier='test_tbox', ontology=True)
        ontology.load_parser(OntologyParser.get_parser('city'))
        cls.prev_default_ontology = Session.ontology
        Session.ontology = ontology

    @classmethod
    def tearDownClass(cls):
        """Restore the previous default TBox."""
        Session.ontology = cls.prev_default_ontology

    def setUp(self) -> None:
        """Start a RemoteStoreServer for a new test."""
        self.start_server(files_uid=False)

    def tearDown(self):
        """Stop a RemoteStoreServer after a test."""
        self.stop_server()

    @staticmethod
    def server_store_generator(configuration_string: str) -> InterfaceDriver:
        """Produces a store for the server from a configuration string."""
        interface = SQLiteInterface()
        store = InterfaceDriver(interface=interface)
        store.open(configuration_string or f"{TestRemoteStoreSQLite.db_file}",
                   create=True)
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

    def client_session_generator(self) -> Session:
        """Generate sessions based on a RemoteStoreClient."""
        client_files_dir = tempfile.TemporaryDirectory()
        store = RemoteStoreClient(file_destination=client_files_dir.name)
        store.client_files_dir = client_files_dir
        graph = Graph(store=store)
        session = Session(base=graph)
        session.graph.open(f'ws://username:password@{self.host}:{self.port}')
        return session

    def test_city(self):
        """Test adding some entities from the city ontology."""
        from osp.core.namespaces import city

        with self.client_session_generator() as session:
            freiburg = city.City(name='Freiburg',
                                 coordinates=[0, 0])
            klaus = city.Citizen(name='Klaus', age=30)
            freiburg[city.hasInhabitant] = klaus
            freiburg_identifier = freiburg.identifier
            session.commit()
        del freiburg

        with self.client_session_generator() as session:
            freiburg = session.from_identifier(freiburg_identifier)
            klaus = freiburg[city.hasInhabitant].one()
            self.assertEqual(freiburg.name, 'Freiburg')
            self.assertEqual(klaus.name, 'Klaus')
            self.assertEqual(klaus.age, 30)
            session.delete(klaus)
            self.assertIsNone(freiburg[city.hasInhabitant].any())
            session.commit()
        del freiburg

        with self.client_session_generator() as session:
            freiburg = session.from_identifier(freiburg_identifier)
            self.assertIsNone(freiburg[city.hasInhabitant].any())

    def test_files(self):
        """Test handling files (no download)."""
        from osp.core.namespaces import cuba

        with tempfile.NamedTemporaryFile('w', suffix='.txt') as os_file:
            os_file.write('text')
            with self.client_session_generator() as session:
                file = cuba.File(path=os_file.name)
                file_identifier = file.identifier
                self.assertEqual(file.path, os_file.name)
                self.assertFalse(
                    os.path.exists(
                        os.path.join(self.server_files_dir,
                                     os.path.basename(os_file.name)))
                )
                session.commit()
                self.assertTrue(
                    filecmp.cmp(
                        os_file.name,
                        os.path.join(self.server_files_dir,
                                     os.path.basename(os_file.name)),
                        shallow=False
                    )
                )

            with self.client_session_generator() as session:
                file = session.from_identifier(file_identifier)
                self.assertEqual(file.path,
                                 os.path.join(
                                     session.graph.store.client_files_dir.name,
                                     os.path.basename(os_file.name)))
                file.path = None
                self.assertIsNone(file.path)
                self.assertIn(os.path.basename(os_file.name),
                              os.listdir(self.server_files_dir))
                session.commit()
                self.assertNotIn(os.path.basename(os_file.name),
                                 os.listdir(self.server_files_dir))
                session.delete(file)
                self.assertRaises(KeyError,
                                  session.from_identifier,
                                  file_identifier)
                session.commit()

            with self.client_session_generator() as session:
                self.assertRaises(KeyError,
                                  session.from_identifier,
                                  file_identifier)

            with tempfile.TemporaryDirectory() as temp_dir:
                with open(os.path.join(temp_dir, 'file1.txt'), 'w') as file_1:
                    file_1.write('CONTENT1')
                with open(os.path.join(temp_dir, 'file2.txt'), 'w') as file_2:
                    file_2.write('CONTENT2')

                with self.client_session_generator() as session:
                    file = cuba.File(path=os.path.join(temp_dir, 'file1.txt'))
                    self.assertEqual(file.path,
                                     os.path.join(temp_dir, 'file1.txt'))
                    session.commit()
                    self.assertEqual(file.path,
                                     os.path.join(temp_dir, 'file1.txt'))
                    self.assertTrue(
                        filecmp.cmp(
                            os.path.join(temp_dir, 'file1.txt'),
                            os.path.join(self.server_files_dir,
                                         'file1.txt'),
                            shallow=False
                        )
                    )
                    self.assertNotIn('file2.txt',
                                     os.listdir(self.server_files_dir))

                    file.path = os.path.join(temp_dir, 'file2.txt')
                    self.assertTrue(
                        filecmp.cmp(
                            os.path.join(temp_dir, 'file1.txt'),
                            os.path.join(self.server_files_dir,
                                         'file1.txt'),
                            shallow=False
                        )
                    )
                    self.assertNotIn('file2.txt',
                                     os.listdir(self.server_files_dir))

                    session.commit()
                    self.assertEqual(file.path,
                                     os.path.join(temp_dir, 'file2.txt'))
                    self.assertNotIn('file1.txt',
                                     os.listdir(self.server_files_dir))
                    self.assertTrue(
                        filecmp.cmp(
                            os.path.join(temp_dir, 'file2.txt'),
                            os.path.join(self.server_files_dir,
                                         'file2.txt'),
                            shallow=False
                        )
                    )

                    # Move the existing file, it should not be re-uploaded as
                    # the hash coincides. (TODO: test automatically that it is
                    #  actually not re-uploaded).
                    shutil.move(os.path.join(temp_dir, 'file2.txt'),
                                os.path.join(temp_dir, 'file.txt'))
                    file.path = os.path.join(temp_dir, 'file.txt')
                    session.commit()
                    self.assertEqual(os.path.join(temp_dir, 'file.txt'),
                                     file.path)
                    file_identifier = file.identifier

                with self.client_session_generator() as session:
                    file = session.from_identifier(file_identifier)
                    self.assertEqual(
                        os.path.join(session.graph.store.client_files_dir.name,
                                     'file.txt'),
                        file.path
                    )
                    session.delete(file)
                    session.commit()

                self.stop_server()
                self.start_server(files_uid=True)

                with self.client_session_generator() as session:
                    file = cuba.File(path=os.path.join(temp_dir, 'file.txt'))
                    self.assertEqual(
                        os.path.join(temp_dir, 'file.txt'),
                        file.path
                    )
                    self.assertNotIn('file.txt',
                                     os.listdir(self.server_files_dir))
                    self.assertNotIn(f'({file.uid.to_uuid()}) file.txt',
                                     os.listdir(self.server_files_dir))
                    session.commit()
                    self.assertNotIn('file.txt',
                                     os.listdir(self.server_files_dir))
                    self.assertIn(f'({file.uid.to_uuid()}) file.txt',
                                  os.listdir(self.server_files_dir))
                    self.assertEqual(
                        os.path.join(temp_dir, 'file.txt'),
                        file.path
                    )
                    file_identifier = file.identifier
                with self.client_session_generator() as session:
                    file = session.from_identifier(file_identifier)
                    self.assertEqual(
                        os.path.join(session.graph.store.client_files_dir.name,
                                     'file.txt'),
                        file.path
                    )

    def test_files_download_upload(self):
        """Test instant download and upload of files."""
        from osp.core.namespaces import cuba

        self.stop_server()
        self.start_server(files_uid=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            with open(os.path.join(temp_dir, 'file.txt'), 'w') as file:
                file.write('CONTENT')
            with open(os.path.join(temp_dir, 'file_other.txt'), 'w') as file:
                file.write('CONTENT')

            with self.client_session_generator() as session:
                file = cuba.File(path=os.path.join(temp_dir, 'file.txt'))
                file_identifier = file.identifier
                session.commit()

            with self.client_session_generator() as session:
                file = session.from_identifier(file_identifier)
                self.assertEqual(
                    session.graph.store.client_files_dir.name,
                    os.path.dirname(file.path)
                )
                self.assertFalse(os.path.exists(file.path))
                filepath = file.path
                file.download()
                self.assertTrue(os.path.exists(file.path))
                with tempfile.TemporaryDirectory() as download_dir:
                    file.download(
                        os.path.join(download_dir,
                                     os.path.basename(filepath))
                    )
                    self.assertTrue(os.path.exists(
                        os.path.join(download_dir,
                                     os.path.basename(file.path))
                    ))

            with self.client_session_generator() as session:
                file = cuba.File(path=os.path.join(temp_dir, 'file_other.txt'))
                self.assertFalse(os.path.exists(
                    os.path.join(self.server_files_dir,
                                 f'({file.uid.to_uuid()}) file_other.txt')
                ))
                file.upload()
                self.assertTrue(os.path.exists(
                    os.path.join(self.server_files_dir,
                                 f'({file.uid.to_uuid()}) file_other.txt')
                ))
                session.commit()
                self.assertTrue(os.path.exists(
                    os.path.join(self.server_files_dir,
                                 f'({file.uid.to_uuid()}) file_other.txt')
                ))


if __name__ == "__main__":
    unittest.main()
