# To add a new cell, type '#%%'
# To add a new markdown cell, type '#%% [markdown]'

# %%
import cuds.classes
from cuds.classes.generated.cuba import CUBA
from cuds.session.db.sqlite_wrapper_session import \
    SqliteWrapperSession

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)

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
    wrapper.add(c)
    wrapper.session.commit()

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)
    city, = wrapper.get(cuba_key=CUBA.CITY)
    persons = city.get()
    print(wrapper, wrapper.items(), "", sep="\n")
    print(city, city.name, city.items(), "", sep="\n")
    print(persons[0], persons[0].name, persons[0].items(), "", sep="\n")
    print(persons[1], persons[1].name, persons[1].items(), "", sep="\n")
    print(persons[2], persons[2].name, persons[2].items(), "", sep="\n")

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)
    city, = wrapper.get(cuba_key=CUBA.CITY)
    city.name = "Paris"
    wrapper.session.commit()

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)
    city = wrapper.get(cuba_key=CUBA.CITY)[0]
    wrapper.remove(city)
    wrapper.session.prune()
    wrapper.session.commit()


#%%
