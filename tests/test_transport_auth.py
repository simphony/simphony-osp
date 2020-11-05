"""This test contains test for authentication in transport session."""

import os
import sys
import subprocess
import unittest2 as unittest
import hashlib
from osp.wrappers.sqlite import SqliteSession
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city

HOST = "127.0.0.1"
PORT1 = 8469
URI_CORRECT1 = f"ws://username:correct@{HOST}:{PORT1}"
URI_WRONG1 = f"ws://username:wrong@{HOST}:{PORT1}"
PORT2 = 8470
URI_CORRECT2 = f"ws://username:correct@{HOST}:{PORT2}"
URI_WRONG2 = f"ws://username:wrong@{HOST}:{PORT2}"
DB = "transport.db"


class AuthSession(SqliteSession):
    """Session used for testing authentication."""

    DB_SALT = "salt"
    DB_PW_HASH = hashlib.sha256(
        ("correct" + DB_SALT).encode("utf-8")).hexdigest()
    CONN_SALTS = dict()

    def __init__(self, *args, connection_id, auth, **kwargs):
        """Initialize the class.

        Args:
            connection_id (str): An identifier for thr
            auth (Any): An object used for authentication.

        Raises:
            PermissionError: Permission denied.
        """
        username, auth_string_user = auth
        conn_salt = AuthSession.CONN_SALTS[connection_id]
        auth_string_server = (
            AuthSession.DB_PW_HASH + conn_salt).encode("utf-8")
        auth_string_server = hashlib.sha256(auth_string_server).hexdigest()

        if auth_string_user != auth_string_server:
            raise PermissionError("Login failed")
        del AuthSession.CONN_SALTS[connection_id]
        super().__init__(*args, **kwargs)

    @staticmethod
    def handshake(username, connection_id):
        """Compute salt used to make authentication more secure.

        Args:
            username (str): The username.
            connection_id (str): An identifier for the connection.

        Returns:
            List[str]: Salts.
        """
        x = (str(username) + str(connection_id)).encode("utf-8")
        conn_salt = hashlib.sha256(x).hexdigest()
        AuthSession.CONN_SALTS[connection_id] = conn_salt
        return [conn_salt, AuthSession.DB_SALT]

    @staticmethod
    def compute_auth(username, password, handshake):
        """Compute string used for authentication.

        Args:
            username (str): The username.
            password (str): The password.
            handshake (Any): The result of the handshake method.

        Returns:
            List[str]: The username and password.
        """
        conn_salt, db_salt = handshake
        salted_pw = (password + db_salt).encode("utf-8")
        pwd_hash = hashlib.sha256(salted_pw).hexdigest()  # that's in the db
        auth = (pwd_hash + conn_salt).encode("utf-8")
        return [username, hashlib.sha256(auth).hexdigest()]


class SimpleAuthSession(SqliteSession):
    """A simple session for testing authentication."""

    DB_USERNAME = "username"
    DB_PASSWORD = "correct"

    def __init__(self, *args, connection_id, auth, **kwargs):
        """Initialize the class.

        Args:
            connection_id (str): An identifier for thr
            auth (Any): An object used for authentication.

        Raises:
            PermissionError: Permission denied.
        """
        username, password = auth
        if username != SimpleAuthSession.DB_USERNAME \
                or SimpleAuthSession.DB_PASSWORD != password:
            raise PermissionError("Login failed: %s" % auth)
        super().__init__(*args, **kwargs)

    @staticmethod
    def compute_auth(username, password, handshake):
        """Compute string used for authentication.

        Args:
            username (str): The username.
            password (str): The password.
            handshake (Any): The result of the handshake method.

        Returns:
            List[str]: The username and password.
        """
        return [username, password]


class TestTransportAuth(unittest.TestCase):
    """Test the authentication mechanism."""

    SERVER_STARTED = []
    OUTPUT_FILE = None

    @classmethod
    def setUpClass(cls):
        """Set up the servers as subprocesses."""
        args = ["python",
                "tests/test_transport_auth.py",
                "server1"]
        TestTransportAuth.OUTPUT_FILE = open("output_test_auth", "w")
        p = subprocess.Popen(args, stderr=TestTransportAuth.OUTPUT_FILE,
                             stdout=subprocess.PIPE)
        TestTransportAuth.SERVER_STARTED.append(p)
        for line in p.stdout:
            if b"ready" in line:
                break

        args[-1] = "server2"
        p = subprocess.Popen(args, stderr=TestTransportAuth.OUTPUT_FILE,
                             stdout=subprocess.PIPE)
        TestTransportAuth.SERVER_STARTED.append(p)
        for line in p.stdout:
            if b"ready" in line:
                break

    @classmethod
    def tearDownClass(cls):
        """Close files and shut down the server subprocess."""
        for p in TestTransportAuth.SERVER_STARTED:
            p.terminate()
        TestTransportAuth.OUTPUT_FILE.close()
        while True:
            try:
                os.remove("output_test_auth")
                break
            except PermissionError:
                pass

    def test_auth(self):
        """Test authentication."""
        with TransportSessionClient(AuthSession, URI_CORRECT1, path=DB) \
                as session:
            city.CityWrapper(session=session)

        with TransportSessionClient(AuthSession, URI_WRONG1, path=DB) \
                as session:
            self.assertRaises(RuntimeError, city.CityWrapper,
                              session=session)

        with TransportSessionClient(SimpleAuthSession, URI_CORRECT2, path=DB) \
                as session:
            city.CityWrapper(session=session)

        with TransportSessionClient(SimpleAuthSession, URI_WRONG2, path=DB) \
                as session:
            self.assertRaises(RuntimeError, city.CityWrapper,
                              session=session)


if __name__ == "__main__":
    if sys.argv[-1] == "server1":
        server = TransportSessionServer(AuthSession, HOST, PORT1)
        print("ready", flush=True)
        server.startListening()
    elif sys.argv[-1] == "server2":
        server = TransportSessionServer(SimpleAuthSession, HOST, PORT2)
        print("ready", flush=True)
        server.startListening()
    else:
        unittest.main()
