from cuds.classes import (
    City, Citizen, Neighbourhood, Street,
    HasPart, HasInhabitant, IsPartOf,
    CUBA, CityWrapper, CitySimWrapper, Person
)
from cuds.session.db.sqlalchemy_wrapper_session import \
    SqlAlchemyWrapperSession
from cuds.testing.test_sim_wrapper_city import DummySimSession
from cuds.utils import pretty_print
from getpass import getpass

user = input("User: ")
pwd = getpass("Password: ")
db_name = input("Database name: ")
host = input("Host: ")
port = int(input("Port [5432]: ") or 5432)
postgres_url = 'postgres://%s:%s@%s:%s/%s' % (user, pwd, host, port, db_name)

# Let's build an EMMO compatible city!
emmo_town = City('EMMO town')

emmo_town.add(Citizen(name='Emanuele Ghedini'), rel=HasInhabitant)
emmo_town.add(Citizen(name='Adham Hashibon'), rel=HasInhabitant)
emmo_town.add(Citizen(name='Jesper Friis'), Citizen(name='Gerhard Goldbeck'),
              Citizen(name='Georg Schmitz'), Citizen(name='Anne de Baas'),
              rel=HasInhabitant)

emmo_town.add(Neighbourhood("Ontology"))
emmo_town.add(Neighbourhood("User cases"))

ontology_uid = None
for neighbourhood in emmo_town.get(cuba_key=CUBA.NEIGHBOURHOOD):
    if neighbourhood.name == "Ontology":
        ontology_uid = neighbourhood.uid
        neighbourhood.add(Street("Relationships"), rel=HasPart)
        neighbourhood.add(Street("Entities"), rel=HasPart)

onto = emmo_town.get(ontology_uid)

# We can go through inverse relationships
print(onto.get(rel=IsPartOf)[0].name + ' is my city!')

# Working with a DB-wrapper: Store in the DB.
with SqlAlchemyWrapperSession(postgres_url) as session:
    wrapper = CityWrapper(session=session)
    wrapper.add(emmo_town)
    session.commit()

# Load from the DB.
with SqlAlchemyWrapperSession(postgres_url) as db_session:
    db_wrapper = CityWrapper(session=db_session)
    db_emmo_town = db_wrapper.get(emmo_town.uid)
    print("The database contains the following information about the city:")
    pretty_print(db_emmo_town)

    # Working with a Simulation wrapper
    with DummySimSession() as sim_session:
        sim_wrapper = CitySimWrapper(num_steps=1,
                                     session=sim_session)
        new_inhabitant = Person(age=31, name="Peter")
        sim_emmo_town, _ = sim_wrapper.add(db_emmo_town, new_inhabitant)
        sim_session.run()
        print("The city has a new inhabitant:")
        pretty_print(sim_emmo_town.get(new_inhabitant.uid))

    # update database
    db_wrapper.update(sim_emmo_town)
    db_session.commit()

# Check if database contains the changes of the simulation.
with SqlAlchemyWrapperSession(postgres_url) as db_session:
    db_wrapper = CityWrapper(session=db_session)
    db_emmo_town = db_wrapper.get(emmo_town.uid)
    print("The database contains the following information about the city:")
    pretty_print(db_emmo_town)
    db_session._clear_database()
