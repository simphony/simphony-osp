import os
import sys
import time
import subprocess
import unittest2 as unittest
import hashlib
from osp.wrappers.sqlite import SqliteSession
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")

HOST = "127.0.0.1"
PORT = 8456
URI_CORRECT = f"ws://username:correct@{HOST}:{PORT}"
URI_WRONG = f"ws://username:wrong@{HOST}:{PORT}"
DB = "transport.db"


class AuthSession(SqliteSession):
    DB_SALT = "salt"
    DB_PW_HASH = hashlib.sha256(
        ("correct" + DB_SALT).encode("utf-8")).hexdigest()
    CONN_SALTS = dict()

    def __init__(self, *args, connection_id, auth, **kwargs):
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
        x = (str(username) + str(connection_id)).encode("utf-8")
        conn_salt = hashlib.sha256(x).hexdigest()
        AuthSession.CONN_SALTS[connection_id] = conn_salt
        return [conn_salt, AuthSession.DB_SALT]

    @staticmethod
    def compute_auth(username, password, handshake):
        conn_salt, db_salt = handshake
        salted_pw = (password + db_salt).encode("utf-8")
        pwd_hash = hashlib.sha256(salted_pw).hexdigest()  # that's in the db
        auth = (pwd_hash + conn_salt).encode("utf-8")
        return [username, hashlib.sha256(auth).hexdigest()]


class TestTransportSqliteCity(unittest.TestCase):
    SERVER_STARTED = False
    OUTPUT_FILE = None

    @classmethod
    def setUpClass(cls):
        args = ["python",
                "tests/test_transport_auth.py",
                "server"]
        TestTransportSqliteCity.OUTPUT_FILE = open("output_test_auth", "w")
        p = subprocess.Popen(args, stderr=TestTransportSqliteCity.OUTPUT_FILE)

        TestTransportSqliteCity.SERVER_STARTED = p
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        TestTransportSqliteCity.OUTPUT_FILE.close()
        os.remove("output_test_auth")

    def test_auth(self):
        """Test authentication."""
        with TransportSessionClient(AuthSession, URI_CORRECT, path=DB) \
                as session:
            CITY.CITY_WRAPPER(session=session)

        with TransportSessionClient(AuthSession, URI_WRONG, path=DB) \
                as session:
            self.assertRaises(RuntimeError, CITY.CITY_WRAPPER,
                              session=session)


if __name__ == "__main__":
    if sys.argv[-1] == "server":
        server = TransportSessionServer(AuthSession, HOST, PORT)
        server.startListening()
    else:
        unittest.main()
