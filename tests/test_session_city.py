import unittest2 as unittest
from osp.core import CUBA
from osp.core.session.session import Session
from osp.core.session.wrapper_session import WrapperSession
from osp.core.session.buffers import BufferContext

try:
    from osp.core import CITY
except ImportError:
    from osp.core.ontology import Parser
    CITY = Parser().parse("city")


class TestSessionCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_delete_cuds_object(self):
        """Tests the pruning method"""
        with TestWrapperSession() as session:
            w = CITY.CITY_WRAPPER(session=session)
            cities = list()
            neighborhoods = list()
            for i in range(2):
                c = CITY.CITY(name="city %s" % i)
                for j in range(2):
                    n = CITY.NEIGHBORHOOD(name="neighborhood %s %s" % (i, j))
                    c.add(n)
                cities.append(w.add(c))
                neighborhoods.extend(cities[-1].get())
            session._reset_buffers(BufferContext.USER)
            session.delete_cuds_object(cities[0])
            self.maxDiff = None
            self.assertEqual(session._buffers, [
                [{}, {w.uid: w, neighborhoods[0].uid: neighborhoods[0],
                      neighborhoods[1].uid: neighborhoods[1]},
                 {cities[0].uid: cities[0]}], [{}, {}, {}]])
            self.assertNotIn(cities[0], session._registry)
            self.assertRaises(AttributeError, getattr, cities[0], "name")

    def test_notify_update_call(self):
        """
        Tests if notify_update is called when Cuds objects are updated.
        """
        updated = set()
        session = TestSession(notify_update=lambda x: updated.add(x))
        w = CITY.CITY_WRAPPER(session=session)
        c = CITY.CITY(name="city 1")
        cw = w.add(c)
        self.assertEqual(updated, set([c, w]))

        updated.pop()
        updated.pop()
        cw.name = "city 2"
        self.assertEqual(updated, set([c]))

        updated.pop()
        c3 = CITY.CITY(name="city 3")
        w.add(c3)
        self.assertEqual(updated, set([c3, w]))

    def test_notify_delete_call(self):
        """
        Tests if notify_delete is called, when we call prune.
        """
        deleted = set()
        session = TestSession(notify_delete=lambda x: deleted.add(x))
        w = CITY.CITY_WRAPPER(session=session)
        cities = list()
        for i in range(3):
            c = CITY.CITY(name="city %s" % i)
            cw = w.add(c)
            cities.append(cw)
            for j in range(2):
                n = CITY.NEIGHBORHOOD(name="neighborhood %s %s" % (i, j))
                cw.add(n)
                nw = cw.get(n.uid)
                for k in range(2):
                    s = CITY.STREET(name="street %s %s %s" % (i, j, k))
                    nw.add(s)
        w.remove(cities[1].uid, cities[2].uid)
        session.prune(rel=None)
        self.assertEqual(
            set(["wrapper" if k.is_a(CUBA.WRAPPER) else k.name
                 for k in session._registry.values()]),
            set(["city 0", "neighborhood 0 0", "neighborhood 0 1",
                 "street 0 0 0", "street 0 0 1", "street 0 1 0",
                 "street 0 1 1", "wrapper"]))
        self.assertEqual(
            set([d.name for d in deleted]),
            set(["city 2", "neighborhood 2 0", "neighborhood 2 1",
                 "street 2 0 0", "street 2 0 1", "street 2 1 0",
                 "street 2 1 1", "city 1", "neighborhood 1 0",
                 "neighborhood 1 1", "street 1 0 0", "street 1 0 1",
                 "street 1 1 0", "street 1 1 1"])
        )

    def test_buffers(self):
        """test if the buffers work correctly"""
        session = TestWrapperSession()
        self.assertEqual(
            session._buffers,
            [[dict(), dict(), dict()], [dict(), dict(), dict()]]
        )

        w = CITY.CITY_WRAPPER(session=session)
        c = CITY.CITY(name="city 1")
        n = CITY.NEIGHBORHOOD(name="neighborhood")
        cw = w.add(c)
        cw.add(n)
        cw.remove(n.uid)
        cw.name = "city 2"
        w.session.prune()

        self.assertEqual(session._buffers, [
            [{cw.uid: cw, w.uid: w}, dict(), dict()],
            [dict(), dict(), dict()]])

        w.session._reset_buffers(BufferContext.USER)
        c2 = CITY.CITY(name="city3")
        w.add(c2)
        cw2 = w.get(c2.uid)
        w.remove(cw.uid)
        w.session.prune()

        self.assertEqual(session._buffers, [
            [{cw2.uid: cw2}, {w.uid: w}, {cw.uid: cw}],
            [dict(), dict(), dict()]])

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
    #     c = CITY.CITY(name="a city")
    #     p = cuds.classes.Citizen(name="a person")
    #     n = CITY.NEIGHBORHOOD(name="a neighborhood")
    #     c.add(p, rel=cuds.classes.HasInhabitant)
    #     c.add(n)
    #     cardinalities, rels = WrapperSession._get_ontology_cardinalities(c)
    #     self.assertEqual(rels,
    #                      {cuds.classes.HasInhabitant, cuds.classes.HasPart})
    #     self.assertEqual(cardinalities, {
    #         (cuds.classes.HasPart, CITY.NEIGHBORHOOD):
    #             (0, float("inf")),
    #         (cuds.classes.IsPartOf, CITY.CITY_WRAPPER):
    #             (0, 1),
    #         (cuds.classes.HasInhabitant, cuds.classes.Citizen):
    #             (0, float("inf")),
    #         (cuds.classes.HasMajor, cuds.classes.Citizen):
    #             (0, 1),
    #         (cuds.classes.HasWorker, cuds.classes.Person):
    #             (0, float("inf"))})

    # def test_check_cardinalities(self):
    #     c1 = CITY.CITY(name="a city")
    #     c2 = CITY.CITY(name="a city")
    #     p = cuds.classes.Citizen(name="a person")
    #     c1.add(p, rel=cuds.classes.HasInhabitant)
    #     c2.add(p, rel=cuds.classes.HasInhabitant)

    #     with TestWrapperSession() as session:
    #         wrapper = CITY.CITY_WRAPPER(session=session)
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
    #         wrapper = CITY.CITY_WRAPPER(session=session)
    #         wrapper.add(c1, c2)
    #         self.assertRaises(ValueError, session._check_cardinalities)
    #         Cuds.CUDS_SETTINGS["check_cardinalities"] = False
    #         session._check_cardinalities()
    #         Cuds.CUDS_SETTINGS["check_cardinalities"] = True
    #         c1w = wrapper.get(c1.uid)
    #         c1w.remove(p.uid, rel=cuds.classes.HasMajor)
    #         session._check_cardinalities()


class TestSession(Session):
    def __init__(self, notify_update=None, notify_delete=None):
        super().__init__()
        self.notify_update = notify_update
        self.notify_delete = notify_delete

    def __str__(self):
        return ""

    def _notify_update(self, cuds_object):
        if self.notify_update:
            self.notify_update(cuds_object)

    def _notify_delete(self, cuds_object):
        if self.notify_delete:
            self.notify_delete(cuds_object)

    def _notify_read(self, cuds_object):
        pass


class TestWrapperSession(WrapperSession):
    def __init__(self, *args, **kwargs):
        super().__init__(None, *args, **kwargs)

    def __str__(self):
        return ""

    def _apply_added(self, root_obj, buffer):
        pass

    def _apply_deleted(self, root_obj, buffer):
        pass

    def _apply_updated(self, root_obj, buffer):
        pass

    def _load_from_backend(self, uids, expired=None):
        yield from Session.load(self, *uids)


if __name__ == "__main__":
    unittest.main()