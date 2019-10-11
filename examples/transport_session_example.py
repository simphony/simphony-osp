import os
import sys
import subprocess
import time
import cuds.classes
from cuds.classes import CUBA
from cuds.utils import pretty_print
from cuds.session.transport.transport_session_client import \
    TransportSessionClient
from cuds.session.transport.transport_session_server import \
    TransportSessionServer
try:
    from cudsqlite.sqlite_wrapper_session import \
        SqliteWrapperSession
except ImportError as e:
    raise ImportError("For this example, the SQLite "
                      "wrapper for SimPhoNy is required!") from e

# Start Server
if sys.argv[-1] == "server":
    if os.path.exists("test.db"):
        os.remove("test.db")
    server = TransportSessionServer(SqliteWrapperSession, "localhost", 8688)
    server.startListening()
    exit(0)

args = ["python3",
        "examples/transport_session_example.py",
        "server"]
try:
    p = subprocess.Popen(args)
except FileNotFoundError:
    args[0] = "python"
    p = subprocess.Popen(args)
time.sleep(1)

try:
    # Construct the Datastructure.
    c = cuds.classes.City("Freiburg")
    p1 = cuds.classes.Citizen(name="Peter")
    p2 = cuds.classes.Citizen(name="Hans")
    p3 = cuds.classes.Citizen(name="Michel")
    n = cuds.classes.Neighbourhood("Zähringen")
    s = cuds.classes.Street("Le street")
    b = cuds.classes.Building("Theater")
    a = cuds.classes.Address(postal_code=79123, name='Le street', number=12)
    c.add(p1, p2, p3, rel=cuds.classes.HasInhabitant)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via transport session")
    with TransportSessionClient(
        SqliteWrapperSession, "localhost", 8688, "test.db"
    ) as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with TransportSessionClient(
        SqliteWrapperSession, "localhost", 8688, "test.db"
    ) as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        pretty_print(city)

    print("Reconnect and make some changes")
    with TransportSessionClient(
        SqliteWrapperSession, "localhost", 8688, "test.db"
    ) as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        city.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with TransportSessionClient(
        SqliteWrapperSession, "localhost", 8688, "test.db"
    ) as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        pretty_print(city)

    print("Delete the city")
    with TransportSessionClient(
        SqliteWrapperSession, "localhost", 8688, "test.db"
    ) as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        city = wrapper.get(cuba_key=CUBA.CITY)[0]
        wrapper.remove(city)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with TransportSessionClient(
        SqliteWrapperSession, "localhost", 8688, "test.db"
    ) as session:
        wrapper = cuds.classes.CityWrapper(session=session)
        print("All cities:", wrapper.get(cuba_key=CUBA.CITY))

finally:
    p.terminate()
    time.sleep(1)
    if os.path.exists("test.db"):
        os.remove("test.db")
