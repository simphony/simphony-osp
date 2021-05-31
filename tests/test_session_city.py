"""Test session basic methods."""

import unittest2 as unittest
from osp.core.namespaces import cuba
from osp.core.session.session import Session
from osp.core.session.wrapper_session import WrapperSession
from osp.core.session.buffers import BufferContext
from osp.core.session.core_session import CoreSession
from osp.core.cuds import Cuds

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city


class TestSessionCity(unittest.TestCase):
    """Test session basic methods."""

    def test_delete_cuds_object(self):
        """Tests the pruning method."""
        with TestWrapperSession() as session:
            w = city.CityWrapper(session=session)
            cities = list()
            neighborhoods = list()
            for i in range(2):
                c = city.City(name="city %s" % i)
                for j in range(2):
                    n = city.Neighborhood(name="neighborhood %s %s" % (i, j))
                    c.add(n)
                cities.append(w.add(c))
                neighborhoods.extend(cities[-1].get())
            session._reset_buffers(BufferContext.USER)
            session.delete_cuds_object(cities[0])
            self.maxDiff = None
            self.assertEqual(session._buffers, [
                [{}, {w.uid: w,
                      neighborhoods[0].uid: neighborhoods[0],
                      neighborhoods[1].uid: neighborhoods[1]},
                 {cities[0].uid: cities[0]}], [{}, {}, {}]])
            self.assertNotIn(cities[0], session._registry)
            self.assertRaises(AttributeError, getattr, cities[0], "name")

    def test_notify_update_call(self):
        """Tests if notify_update is called when Cuds objects are updated."""
        updated = set()
        session = TestSession(notify_update=lambda x: updated.add(x))
        w = city.CityWrapper(session=session)
        c = city.City(name="city 1")
        cw = w.add(c)
        self.assertEqual(updated, set([c, w]))

        updated.pop()
        updated.pop()
        cw.name = "city 2"
        self.assertEqual(updated, set([c]))

        updated.pop()
        c3 = city.City(name="city 3")
        w.add(c3)
        self.assertEqual(updated, set([c3, w]))

    def test_notify_delete_call(self):
        """Tests if notify_delete is called, when we call prune."""
        deleted = set()
        session = TestSession(notify_delete=lambda x: deleted.add(x))
        w = city.CityWrapper(session=session)
        cities = list()
        for i in range(3):
            c = city.City(name="city %s" % i)
            cw = w.add(c)
            cities.append(cw)
            for j in range(2):
                n = city.Neighborhood(name="neighborhood %s %s" % (i, j))
                cw.add(n)
                nw = cw.get(n.uid)
                for k in range(2):
                    s = city.Street(name="street %s %s %s" % (i, j, k))
                    nw.add(s)
        w.remove(cities[1].uid, cities[2].uid)
        expected_deletion = {
            x.uid for x in session._registry.values()
            if (
                hasattr(x, "name")
                and x.name in {
                    "city 2", "neighborhood 2 0", "neighborhood 2 1",
                    "street 2 0 0", "street 2 0 1", "street 2 1 0",
                    "street 2 1 1", "city 1", "neighborhood 1 0",
                    "neighborhood 1 1", "street 1 0 0", "street 1 0 1",
                    "street 1 1 0", "street 1 1 1"
                })}
        session.prune(rel=None)
        self.assertEqual(
            set(["wrapper" if k.is_a(cuba.Wrapper) else k.name
                 for k in session._registry.values()]),
            set(["city 0", "neighborhood 0 0", "neighborhood 0 1",
                 "street 0 0 0", "street 0 0 1", "street 0 1 0",
                 "street 0 1 1", "wrapper"]))
        self.assertEqual(set([d.uid for d in deleted]),
                         expected_deletion)

    def test_buffers(self):
        """Test if the buffers work correctly."""
        session = TestWrapperSession()
        self.assertEqual(
            session._buffers,
            [[dict(), dict(), dict()], [dict(), dict(), dict()]]
        )

        w = city.CityWrapper(session=session)
        c = city.City(name="city 1")
        n = city.Neighborhood(name="neighborhood")
        cw = w.add(c)
        cw.add(n)
        cw.remove(n.uid)
        cw.name = "city 2"
        w.session.prune()

        self.assertEqual(session._buffers, [
            [{cw.uid: cw, w.uid: w}, dict(), dict()],
            [dict(), dict(), dict()]])

        w.session._reset_buffers(BufferContext.USER)
        c2 = city.City(name="city3")
        w.add(c2)
        cw2 = w.get(c2.uid)
        w.remove(cw.uid)
        w.session.prune()

        self.assertEqual(session._buffers, [
            [{cw2.uid: cw2}, {w.uid: w}, {cw.uid: cw}],
            [dict(), dict(), dict()]])

    def test_default_session_context_manager(self):
        """Test changing the default session with a session context manager."""
        default_session = CoreSession()
        Cuds._session = default_session
        bern = city.City(name='Bern')
        with TestSession() as session1:
            freiburg = city.City(name='Freiburg')
            with TestSession() as session2:
                berlin = city.City(name='Berlin')
                with TestSession() as session3:
                    madrid = city.City(name='Madrid')
                    with TestSession() as session4:
                        beijing = city.City(name='北京')
                        self.assertIs(freiburg.session, session1)
                        self.assertIs(berlin.session, session2)
                        self.assertIs(madrid.session, session3)
                        self.assertIs(beijing.session, session4)
                paris = city.City(name='Paris')
                self.assertIs(berlin.session, paris.session)
                self.assertIsNot(berlin.session, beijing.session)
        tokyo = city.City(name='Tokyo')
        # Test default session restore.
        self.assertIs(bern.session, tokyo.session)
        self.assertIs(bern.session, default_session)

    # def test_parse_cardinality(self):
    #     """Test parsing cardinality from the ontology."""
    #     self.assertEqual(WrapperSession._parse_cardinality("*"),
    #                      (0, float("inf")))
    #     self.assertEqual(WrapperSession._parse_cardinality("many"),
    #                      (0, float("inf")))
    #     self.assertEqual(WrapperSession._parse_cardinality("0+"),
    #                      (0, float("inf")))
    #     self.assertEqual(WrapperSession._parse_cardinality("+"),
    #                      (1, float("inf")))
    #     self.assertEqual(WrapperSession._parse_cardinality("1+"),
    #                      (1, float("inf")))
    #     self.assertEqual(WrapperSession._parse_cardinality("5+"),
    #                      (5, float("inf")))
    #     self.assertEqual(WrapperSession._parse_cardinality("5"),
    #                      (5, 5))
    #     self.assertEqual(WrapperSession._parse_cardinality(5),
    #                      (5, 5))
    #     self.assertEqual(WrapperSession._parse_cardinality("5-5"),
    #                      (5, 5))
    #     self.assertEqual(WrapperSession._parse_cardinality("5-10"),
    #                      (5, 10))

    # def test_get_ontology_cardinalities(self):
    #     c = city.City(name="a city")
    #     p = cuds.classes.Citizen(name="a person")
    #     n = city.Neighborhood(name="a neighborhood")
    #     c.add(p, rel=cuds.classes.HasInhabitant)
    #     c.add(n)
    #     cardinalities, rels = WrapperSession._get_ontology_cardinalities(c)
    #     self.assertEqual(rels,
    #                      {cuds.classes.HasInhabitant, cuds.classes.HasPart})
    #     self.assertEqual(cardinalities, {
    #         (cuds.classes.HasPart, city.Neighborhood):
    #             (0, float("inf")),
    #         (cuds.classes.IsPartOf, city.CityWrapper):
    #             (0, 1),
    #         (cuds.classes.HasInhabitant, cuds.classes.Citizen):
    #             (0, float("inf")),
    #         (cuds.classes.HasMajor, cuds.classes.Citizen):
    #             (0, 1),
    #         (cuds.classes.HasWorker, cuds.classes.Person):
    #             (0, float("inf"))})

    # def test_check_cardinalities(self):
    #     c1 = city.City(name="a city")
    #     c2 = city.City(name="a city")
    #     p = cuds.classes.Citizen(name="a person")
    #     c1.add(p, rel=cuds.classes.HasInhabitant)
    #     c2.add(p, rel=cuds.classes.HasInhabitant)

    #     with TestWrapperSession() as session:
    #         wrapper = city.CityWrapper(session=session)
    #         wrapper.add(c1, c2)
    #         self.assertRaises(ValueError, session._check_cardinalities)
    #         Cuds.CUDS_SETTINGS["check_cardinalities"] = False
    #         session._check_cardinalities()
    #         Cuds.CUDS_SETTINGS["check_cardinalities"] = True
    #         c1w = wrapper.get(c1.uid)
    #         c1w.remove(p.uid)
    #         session._check_cardinalities()

    #     p.remove(rel=cuds.classes.IsInhabitantOf)
    #     p.add(c1, rel=cuds.classes.IsMajorOf)
    #     p.add(c2, rel=cuds.classes.WorksIn)
    #     p.add(c1, rel=cuds.classes.IsInhabitantOf)
    #     with TestWrapperSession() as session:
    #         wrapper = city.CityWrapper(session=session)
    #         wrapper.add(c1, c2)
    #         self.assertRaises(ValueError, session._check_cardinalities)
    #         Cuds.CUDS_SETTINGS["check_cardinalities"] = False
    #         session._check_cardinalities()
    #         Cuds.CUDS_SETTINGS["check_cardinalities"] = True
    #         c1w = wrapper.get(c1.uid)
    #         c1w.remove(p.uid, rel=cuds.classes.HasMajor)
    #         session._check_cardinalities()


class TestSession(Session):
    """Session used for testing."""

    def __init__(self, notify_update=None, notify_delete=None):
        """Initialize."""
        super().__init__()
        self.notify_update = notify_update
        self.notify_delete = notify_delete

    def __str__(self):
        """Convert to string."""
        return ""

    def _notify_update(self, cuds_object):
        """Notify when CUDS object has been updated."""
        if self.notify_update:
            self.notify_update(cuds_object)

    def _notify_delete(self, cuds_object):
        """Notify when CUDS object has been deleted."""
        if self.notify_delete:
            self.notify_delete(cuds_object)

    def _notify_read(self, cuds_object):
        """Do nothing."""
        pass

    def _get_full_graph(self):
        """Get the graph."""
        return self.graph


class TestWrapperSession(WrapperSession):
    """Tests for abstract TestWrapperSession."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__(None, *args, **kwargs)

    def __str__(self):
        """Convert to string."""
        return ""

    def _apply_added(self, root_obj, buffer):
        """Apply added objects."""
        pass

    def _apply_deleted(self, root_obj, buffer):
        """Apply deleted objects."""
        pass

    def _apply_updated(self, root_obj, buffer):
        """Apply updated objects."""
        pass

    def _load_from_backend(self, uids, expired=None):
        """Load data from backend."""
        yield from Session.load(self, *uids)


if __name__ == "__main__":
    unittest.main()
