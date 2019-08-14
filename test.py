import cuds.classes
from cuds.classes.core.session.sqlite_wrapper_session \
    import SqliteWrapperSession

session = SqliteWrapperSession("test.db")
wrapper = cuds.classes.CityWrapper(session=session)
c = cuds.classes.City("city")
wrapper.add(c)

wrapper.session.commit()