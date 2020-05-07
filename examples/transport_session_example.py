import os
import sys
import subprocess
import time
from osp.core import CITY
from osp.core.utils import pretty_print
from osp.core.session.transport.transport_session_client import \
    TransportSessionClient
from osp.core.session.transport.transport_session_server import \
    TransportSessionServer
from osp.wrappers.sqlite_session import SqliteSession

# Start Server
if sys.argv[-1] == "server":
    if os.path.exists("test.db"):
        os.remove("test.db")
    server = TransportSessionServer(SqliteSession, "localhost", 8688)
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
    c = CITY.CITY(name="Freiburg")
    p1 = CITY.CITIZEN(name="Peter")
    p2 = CITY.CITIZEN(name="Hans")
    p3 = CITY.CITIZEN(name="Michel")
    n = CITY.NEIGHBOURHOOD(name="Zähringen")
    s = CITY.STREET(name="Le street")
    b = CITY.BUILDING(name="Theater")
    a = CITY.ADDRESS(postal_code=79123, name='Le street', number=12)
    c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via transport session")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", "test.db"
    ) as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", "test.db"
    ) as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        pretty_print(city)

    print("Reconnect and make some changes")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", "test.db"
    ) as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        city.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", "test.db"
    ) as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        pretty_print(city)

    print("Delete the city")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", "test.db"
    ) as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        wrapper.remove(city)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", "test.db"
    ) as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        print("All cities:", wrapper.get(oclass=CITY.CITY))

finally:
    p.terminate()
    time.sleep(1)
    if os.path.exists("test.db"):
        os.remove("test.db")
