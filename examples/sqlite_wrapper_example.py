# To add a new cell, type '#%%'
# To add a new markdown cell, type '#%% [markdown]'

# %%
import cuds.classes
from cuds.classes.core.session.sqlite_wrapper_session import \
    SqliteWrapperSession

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)

    c = cuds.classes.City("Freiburg")
    p1 = cuds.classes.Person("Peter")
    p2 = cuds.classes.Person("Hans")
    p3 = cuds.classes.Person("Michel")
    c.add(p1, p2, p3)
    wrapper.add(c)
    wrapper.session.commit()

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)
    city, = wrapper.get()
    persons = city.get()
    print(wrapper, wrapper.items(), "", sep="\n")
    print(city, city.name, city.items(), "",  sep="\n")
    print(persons[0], persons[0].name, persons[0].items(), "", sep="\n")
    print(persons[1], persons[1].name, persons[1].items(), "", sep="\n")
    print(persons[2], persons[2].name, persons[2].items(), "", sep="\n")

# %%
with SqliteWrapperSession("test.db") as session:
    wrapper = cuds.classes.CityWrapper(session=session)
    city, = wrapper.get()
    city.name = "Paris"
    wrapper.session.commit()