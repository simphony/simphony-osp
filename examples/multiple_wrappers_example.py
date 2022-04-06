"""An expample explaining the interaction of multiple wrappers."""

# Please install the city ontology: $pico install city

from getpass import getpass

from osp.core.namespaces import city
from osp.core.utils import pretty_print
from osp.wrappers.simdummy import SimDummySession

try:
    from osp.wrappers.sqlalchemy_wrapper_session import (
        SqlAlchemyWrapperSession,
    )
except ImportError as e:
    raise ImportError(
        "For this example, the SQLAlchemy " "wrapper for SimPhoNy is required!"
    ) from e

# import logging
# logger = logging.getLogger("osp.core")
# logger.setLevel(logging.DEBUG)

print("Input data to connect to Postgres table!")
user = input("User: ")
pwd = getpass("Password: ")
db_name = input("Database name: ")
host = input("Host: ")
port = int(input("Port [5432]: ") or 5432)
postgres_url = "postgresql://%s:%s@%s:%s/%s" % (user, pwd, host, port, db_name)

# Let's build an EMMO compatible city!
emmo_town = city.City(name="EMMO town")

emmo_town.add(city.Citizen(name="Emanuele Ghedini"), rel=city.hasInhabitant)
emmo_town.add(city.Citizen(name="Adham Hashibon"), rel=city.hasInhabitant)
emmo_town.add(
    city.Citizen(name="Jesper Friis"),
    city.Citizen(name="Gerhard Goldbeck"),
    city.Citizen(name="Georg Schmitz"),
    city.Citizen(name="Anne de Baas"),
    rel=city.hasInhabitant,
)

emmo_town.add(city.Neighborhood(name="Ontology"))
emmo_town.add(city.Neighborhood(name="User cases"))

ontology_uid = None
for neighborhood in emmo_town.get(oclass=city.Neighborhood):
    if neighborhood.name == "Ontology":
        ontology_uid = neighborhood.uid
        neighborhood.add(city.Street(name="Relationships"), rel=city.hasPart)
        neighborhood.add(city.Street(name="Entities"), rel=city.hasPart)

onto = emmo_town.get(ontology_uid)

# We can go through inverse relationships
print(onto.get(rel=city.isPartOf)[0].name + " is my city!")

# Working with a DB-wrapper: Store in the DB.
with SqlAlchemyWrapperSession(postgres_url) as session:
    wrapper = city.CityWrapper(session=session)
    wrapper.add(emmo_town)
    session.commit()

# Load from the DB.
with SqlAlchemyWrapperSession(postgres_url) as db_session:
    db_wrapper = city.CityWrapper(session=db_session)
    db_emmo_town = db_wrapper.get(emmo_town.uid)
    print("The database contains the following information about the city:")
    pretty_print(db_emmo_town)

    # Working with a Simulation wrapper
    with SimDummySession() as sim_session:
        sim_wrapper = city.CitySimWrapper(numSteps=1, session=sim_session)
        new_inhabitant = city.Person(age=31, name="Peter")
        sim_emmo_town, _ = sim_wrapper.add(db_emmo_town, new_inhabitant)
        sim_session.run()
        print("The city has a new inhabitant:")
        pretty_print(sim_emmo_town.get(new_inhabitant.uid))

    # update database
    db_wrapper.update(sim_emmo_town)
    db_session.commit()

# Check if database contains the changes of the simulation.
with SqlAlchemyWrapperSession(postgres_url) as db_session:
    db_wrapper = city.CityWrapper(session=db_session)
    db_emmo_town = db_wrapper.get(emmo_town.uid)
    print("The database contains the following information about the city:")
    pretty_print(db_emmo_town)
    input("Example finished. Press Enter to clear the database!")
    db_session._clear_database()
