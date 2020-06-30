import os
from osp.core.namespaces import city
from osp.core.utils import pretty_print
from osp.wrappers.sqlite_wrapper_session import \
    SqliteWrapperSession

try:
    # Construct the Datastructure.
    c = city.City(name="Freiburg")
    p1 = city.Citizen(name="Peter")
    p2 = city.Citizen(name="Hans")
    p3 = city.Citizen(name="Michel")
    n = city.Neighborhood(name="Zähringen")
    s = city.Street(name="Le street")
    b = city.Building(name="Theater")
    a = city.Address(postal_code=79123, name='Le street', number=12)
    c.add(p1, p2, p3, rel=city.hasInhabitant)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via sqlite session")
    with SqliteWrapperSession("test.db") as session:
        wrapper = city.CityWrapper(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with SqliteWrapperSession("test.db") as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        pretty_print(c)

    print("Reconnect and make some changes")
    with SqliteWrapperSession("test.db") as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        c.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with SqliteWrapperSession("test.db") as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        pretty_print(c)

    print("Delete the city")
    with SqliteWrapperSession("test.db") as session:
        wrapper = city.CityWrapper(session=session)
        c = wrapper.get(oclass=city.City)[0]
        wrapper.remove(c)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with SqliteWrapperSession("test.db") as session:
        wrapper = city.CityWrapper(session=session)
        print("All cities:", wrapper.get(oclass=city.City))

finally:
    if os.path.exists("test.db"):
        os.remove("test.db")
