import logging
from osp.core.session import TransportSessionServer
from osp.wrappers.sqlite import SqliteSession

logging.getLogger("osp.core").setLevel(logging.DEBUG)

TransportSessionServer(
    SqliteSession, "localhost", 4587,
    session_kwargs={"path": "test.db"},
    file_destination="tmp_data_server"
).startListening()
