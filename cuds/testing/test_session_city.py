# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest2 as unittest
import cuds.classes
from cuds.classes.core.session.session import Session
from cuds.classes.core.session.wrapper_session import WrapperSession
from cuds.classes import ActiveRelationship


class TestSessionCity(unittest.TestCase):

    def setUp(self):
        pass

    def test_notify_update_call(self):
        """
        Tests if notify_update is called when Cuds objects are updated.
        """
        updated = set()
        session = TestSession(notify_update=lambda x: updated.add(x))
        w = cuds.classes.CityWrapper(session=session)
        c = cuds.classes.City("city 1")
        w.add(c)
        self.assertEqual(updated, set([w]))

        cw, = w.get(c.uid)
        cw.name = "city 2"
        self.assertEqual(updated, set([c, w]))

        updated.pop()
        updated.pop()
        c3 = cuds.classes.City("city 3")
        w.add(c3)
        self.assertEqual(updated, set([w]))

    def test_notify_delete_call(self):
        """
        Tests if notify_delete is called, when we call prune.
        """
        deleted = set()
        session = TestSession(notify_delete=lambda x: deleted.add(x))
        w = cuds.classes.CityWrapper(session=session)
        cities = list()
        for i in range(3):
            c = cuds.classes.City("city %s" % i)
            w.add(c)
            cw, = w.get(c.uid)
            cities.append(cw)
            for j in range(2):
                n = cuds.classes.Neighbourhood("neighborhood %s %s" % (i, j))
                cw.add(n)
                nw, = cw.get(n.uid)
                for k in range(2):
                    s = cuds.classes.Street("street %s %s %s" % (i, j, k))
                    nw.add(s)
        w.remove(cities[1].uid, cities[2].uid)
        session.prune(rel=None)
        self.assertEqual(
            set(["wrapper" if isinstance(k, cuds.classes.Wrapper) else k.name
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
        session = TestWrapperSession(engine=None)
        self.assertEqual(session._added, dict())
        self.assertEqual(session._updated, dict())
        self.assertEqual(session._deleted, dict())

        w = cuds.classes.CityWrapper(session=session)
        c = cuds.classes.City("city 1")
        n = cuds.classes.Neighbourhood("neighborhood")
        w.add(c)
        cw, = w.get(c.uid)
        cw.add(n)
        cw.remove(n.uid)
        cw.name = "city 2"
        w.session.prune()

        self.assertEqual(session._added, {cw.uid: cw, w.uid: w})
        self.assertEqual(session._updated, dict())
        self.assertEqual(session._deleted, dict())

        w.session._reset_buffers()
        c2 = cuds.classes.City("city3")
        w.add(c2)
        cw2, = w.get(c2.uid)
        w.remove(cw.uid)
        w.session.prune()

        self.assertEqual(session._added, {cw2.uid: cw2})
        self.assertEqual(session._updated, {w.uid: w})
        self.assertEqual(session._deleted, {cw.uid: cw})


class TestSession(Session):
    def __init__(self, notify_update=None, notify_delete=None):
        super().__init__()
        self.notify_update = notify_update
        self.notify_delete = notify_delete

    def __str__(self):
        return ""

    def _notify_update(self, entity):
        if self.notify_update:
            self.notify_update(entity)

    def _notify_delete(self, entity):
        if self.notify_delete:
            self.notify_delete(entity)


class TestWrapperSession(WrapperSession):
    def __str__(self):
        return ""

    def _apply_added(self):
        pass

    def _apply_deleted(self):
        pass

    def _apply_updated(self):
        pass
