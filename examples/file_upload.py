import sys
import logging
from osp.wrappers.sqlite import SqliteSession
from osp.core.session import TransportSessionServer
from osp.core import cuba
from osp.wrappers.dataspace import DataspaceSession

logging.getLogger("osp.core.session.transport").setLevel(logging.DEBUG)

if sys.argv[-1] == "client":
    print("Please specify where you want to cache the files on the client:")
    with DataspaceSession("ws://127.0.0.1:4587",
                          input("file destination: > ")) as session:
        wrapper = cuba.wrapper(session=session)
        file = cuba.file(path=input("file to upload: > "))
        wrapper.add(file, rel=cuba.active_relationship)
        session.commit()

else:
    print("Please specify where you want to cache the files on the server:")
    file_destination = input("file destination: > ")
    print("Starting server now.")
    print("Please call 'python %s client' to connect" % __file__)
    TransportSessionServer(
        SqliteSession, "localhost", 4587,
        session_kwargs={"path": "test.db"},
        file_destination=file_destination
    ).startListening()
