"""An example explaining the use of the Transport session."""

# Please install the city ontology: $pico install city

import os
import subprocess
import sys
import time

from osp.core.namespaces import city
from osp.core.session.transport.transport_session_client import (
    TransportSessionClient,
)
from osp.core.session.transport.transport_session_server import (
    TransportSessionServer,
)
from osp.core.utils import pretty_print
from osp.wrappers.sqlite import SqliteSession

# Start Server
if sys.argv[-1] == "server":
    if os.path.exists("test.db"):
        os.remove("test.db")
    server = TransportSessionServer(SqliteSession, "localhost", 8688)
    server.startListening()
    exit(0)

args = ["python3", "examples/transport_session_example.py", "server"]
try:
    p = subprocess.Popen(args)
except FileNotFoundError:
    args[0] = "python"
    p = subprocess.Popen(args)
time.sleep(5)

try:
    # Construct the Datastructure.
    c = city.City(name="Freiburg")
    p1 = city.Citizen(name="Peter")
    p2 = city.Citizen(name="Hans")
    p3 = city.Citizen(name="Michel")
    n = city.Neighborhood(name="Zähringen")
    s = city.Street(name="Le street")
    b = city.Building(name="Theater")
    a = city.Address(postalCode=79123, name="Le street", number=12)
    c.add(p1, p2, p3, rel=city.hasInhabitant)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via transport session")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", path="test.db"
    ) as session:
        wrapper = city.CityWrapper(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", path="test.db"
    ) as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        pretty_print(c)

    print("Reconnect and make some changes")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", path="test.db"
    ) as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        c.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", path="test.db"
    ) as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        pretty_print(c)

    print("Delete the city")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", path="test.db"
    ) as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        wrapper.remove(c)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with TransportSessionClient(
        SqliteSession, "ws://localhost:8688", path="test.db"
    ) as session:
        wrapper = city.CityWrapper(session=session)
        print("All cities:", wrapper.get(oclass=city.City))

finally:
    p.terminate()
    time.sleep(5)
    if os.path.exists("test.db"):
        os.remove("test.db")
