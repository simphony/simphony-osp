import os
from osp.core import CITY
from osp.core.utils import pretty_print
from osp.wrappers.sqlite_wrapper_session import \
    SqliteWrapperSession

try:
    # Construct the Datastructure.
    c = CITY.CITY(name="Freiburg")
    p1 = CITY.CITIZEN(name="Peter")
    p2 = CITY.CITIZEN(name="Hans")
    p3 = CITY.CITIZEN(name="Michel")
    n = CITY.NEIGHBORHOOD(name="Zähringen")
    s = CITY.STREET(name="Le street")
    b = CITY.BUILDING(name="Theater")
    a = CITY.ADDRESS(postal_code=79123, name='Le street', number=12)
    c.add(p1, p2, p3, rel=CITY.HAS_INHABITANT)
    c.add(n).add(s).add(b).add(a)

    print("Connect to DB via sqlite session")
    with SqliteWrapperSession("test.db") as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        wrapper.add(c)
        wrapper.session.commit()

    print("Reconnect and check if data is still there")
    with SqliteWrapperSession("test.db") as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        pretty_print(city)

    print("Reconnect and make some changes")
    with SqliteWrapperSession("test.db") as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        city.name = "Paris"
        wrapper.session.commit()

    print("Reconnect and check if changes were successful")
    with SqliteWrapperSession("test.db") as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        pretty_print(city)

    print("Delete the city")
    with SqliteWrapperSession("test.db") as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        city = wrapper.get(oclass=CITY.CITY)[0]
        wrapper.remove(city)
        wrapper.session.prune()
        wrapper.session.commit()

    print("Reconnect and check if deletion was successful")
    with SqliteWrapperSession("test.db") as session:
        wrapper = CITY.CITY_WRAPPER(session=session)
        print("All cities:", wrapper.get(oclass=CITY.CITY))

finally:
    if os.path.exists("test.db"):
        os.remove("test.db")
