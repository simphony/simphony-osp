from osp.wrappers.sqlite import SqliteSession
from osp.core.namespaces import city, cuba


def delete(db_wrapper, c):
    _delete_aux(c, db_wrapper)
    db_wrapper.session.commit()


def _delete_aux(cuds_object, db_wrapper):
    for c in cuds_object.get(rel=cuba.activeRelationship):
        _delete_aux(c, db_wrapper)
    db_wrapper.session.delete_cuds_object(cuds_object)
    # db_wrapper.session.commit()


with SqliteSession('test.db') as session:
    wrapper = city.CityWrapper(session=session)
    a = city.City(name='freiburg', session=wrapper.session)
    b = city.Citizen(name='peter', session=wrapper.session)
    a.add(b, rel=city.hasInhabitant)
    wrapper.session.commit()
    delete(wrapper, a)
