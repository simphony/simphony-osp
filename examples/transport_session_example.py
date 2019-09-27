
from cuds.session.transport.transport_session import \
    TransportSessionServer
from cuds.session.db.sqlite_wrapper_session import \
    SqliteWrapperSession

with SqliteWrapperSession("test.db") as session:
    s = TransportSessionServer(session, "127.0.0.1", 8687)
    s.startListening()


from cuds.session.transport.transport_session import \
    TransportSessionClient
from cuds.session.db.sqlite_wrapper_session import \
    SqliteWrapperSession

c = TransportSessionClient(SqliteWrapperSession, "127.0.0.1", 8687)
c.commit()

# %%
from cuds.session.transport.transport_session import \
    serialize, deserialize
import cuds.classes
c = cuds.classes.City("hi")
p = cuds.classes.Citizen(name="Peter")
c.add(p, rel=cuds.classes.HasInhabitant)
sc = serialize(c)
sp = serialize(p)
print(sc)
print(sp)

print(deserialize(sc))
print(deserialize(sp))