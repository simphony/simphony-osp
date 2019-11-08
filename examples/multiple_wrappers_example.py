import sys
import os
from osp.core import CITY
from osp.core.utils import pretty_print
from getpass import getpass
try:
    from osp.wrappers.sqlalchemy_wrapper_session import \
        SqlAlchemyWrapperSession
except ImportError as e:
    raise ImportError("For this example, the SQLAlchemy "
                      "wrapper for SimPhoNy is required!") from e
try:
    from osp.wrappers.dummy_simulation_wrapper import DummySimWrapperSession
except ImportError as e:
    raise ImportError("For this example, the dummy simulation "
                      "wrapper for SimPhoNy is required!") from e


print("Input data to connect to Postgres table!")
user = input("User: ")
pwd = getpass("Password: ")
db_name = input("Database name: ")
host = input("Host: ")
port = int(input("Port [5432]: ") or 5432)
postgres_url = 'postgres://%s:%s@%s:%s/%s' % (user, pwd, host, port, db_name)

# Let's build an EMMO compatible city!
emmo_town = CITY.CITY(name='EMMO town')

emmo_town.add(CITY.CITIZEN(name='Emanuele Ghedini'), rel=CITY.HAS_INHABITANT)
emmo_town.add(CITY.CITIZEN(name='Adham Hashibon'), rel=CITY.HAS_INHABITANT)
emmo_town.add(CITY.CITIZEN(name='Jesper Friis'),
              CITY.CITIZEN(name='Gerhard Goldbeck'),
              CITY.CITIZEN(name='Georg Schmitz'),
              CITY.CITIZEN(name='Anne de Baas'),
              rel=CITY.HAS_INHABITANT)

emmo_town.add(CITY.NEIGHBOURHOOD(name="Ontology"))
emmo_town.add(CITY.NEIGHBOURHOOD(name="User cases"))

ontology_uid = None
for neighbourhood in emmo_town.get(oclass=CITY.NEIGHBOURHOOD):
    if neighbourhood.name == "Ontology":
        ontology_uid = neighbourhood.uid
        neighbourhood.add(CITY.STREET(name="Relationships"), rel=CITY.HAS_PART)
        neighbourhood.add(CITY.STREET(name="Entities"), rel=CITY.HAS_PART)

onto = emmo_town.get(ontology_uid)

# We can go through inverse relationships
print(onto.get(rel=CITY.IS_PART_OF)[0].name + ' is my city!')

# Working with a DB-wrapper: Store in the DB.
with SqlAlchemyWrapperSession(postgres_url) as session:
    wrapper = CITY.CITY_WRAPPER(session=session)
    wrapper.add(emmo_town)
    session.commit()

# Load from the DB.
with SqlAlchemyWrapperSession(postgres_url) as db_session:
    db_wrapper = CITY.CITY_WRAPPER(session=db_session)
    db_emmo_town = db_wrapper.get(emmo_town.uid)
    print("The database contains the following information about the city:")
    pretty_print(db_emmo_town)

    # Working with a Simulation wrapper
    with DummySimWrapperSession() as sim_session:
        sim_wrapper = CITY.CITY_SIM_WRAPPER(num_steps=1,
                                          session=sim_session)
        new_inhabitant = CITY.PERSON(age=31, name="Peter")
        sim_emmo_town, _ = sim_wrapper.add(db_emmo_town, new_inhabitant)
        sim_session.run()
        print("The city has a new inhabitant:")
        pretty_print(sim_emmo_town.get(new_inhabitant.uid))

    # update database
    db_wrapper.update(sim_emmo_town)
    db_session.commit()

# Check if database contains the changes of the simulation.
with SqlAlchemyWrapperSession(postgres_url) as db_session:
    db_wrapper = CITY.CITY_WRAPPER(session=db_session)
    db_emmo_town = db_wrapper.get(emmo_town.uid)
    print("The database contains the following information about the city:")
    pretty_print(db_emmo_town)
    input("Example finished. Press Enter to clear the database!")
    db_session._clear_database()
