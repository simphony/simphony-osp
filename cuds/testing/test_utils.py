# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

import unittest
import cuds.classes
from cuds.classes.core.session.core_session import CoreSession
from cuds.utils import (destruct_cuds, clone_cuds, create_for_session,
                        create_from_cuds)


class TestUtils(unittest.TestCase):

    def test_destruct_cuds(self):
        """Test destruction of cuds"""
        a = cuds.classes.City("Freiburg")
        b = cuds.classes.Citizen(age=12, name="Horst")
        with CoreSession() as session:
            w = cuds.classes.CityWrapper(session=session)
            aw = w.add(a)
            bw = aw.add(b, rel=cuds.classes.HasInhabitant)
            session._expired = {bw.uid}
            destruct_cuds(aw)

            self.assertEqual(a.name, "Freiburg")
            self.assertEqual(bw.name, "Horst")
            self.assertEqual(aw.name, None)
            self.assertEqual(aw.get(), [])

            destruct_cuds(bw)
            self.assertEqual(bw.name, None)
            self.assertEqual(session._expired, set())

    def test_clone_cuds(self):
        """Test cloning of cuds"""
        a = cuds.classes.City("Freiburg")
        with CoreSession() as session:
            w = cuds.classes.CityWrapper(session=session)
            aw = w.add(a)
            clone = clone_cuds(aw)
            self.assertIsNot(aw, None)
            self.assertIs(clone.session, aw.session)
            self.assertEqual(clone.uid, aw.uid)
            self.assertIs(aw, session._registry.get(aw.uid))
            self.assertEqual(clone.name, "Freiburg")

    def test_create_for_session(self):
        """Test creation of cuds for different session"""
        default_session = CoreSession()
        cuds.classes.Cuds._session = default_session
        a = cuds.classes.City("Freiburg")
        self.assertIs(a.session, default_session)
        with CoreSession() as session:
            b = create_for_session(cuds.classes.City,
                                   {"name": "Offenburg", "uid": a.uid},
                                   session=session)
            self.assertEqual(b.name, "Offenburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid})
            self.assertIs(session._registry.get(b.uid), b)

            x = cuds.classes.Citizen()
            b.add(x, rel=cuds.classes.HasInhabitant)

            c = create_for_session(cuds.classes.City,
                                   {"name": "Emmendingen", "uid": a.uid},
                                   session=session)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Emmendingen")
            self.assertEqual(c.get(rel=cuds.classes.Relationship), [])
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid})
            self.assertIs(default_session._registry.get(a.uid), a)

    def test_create_from_cuds(self):
        """Test copying cuds to different session"""
        default_session = CoreSession()
        cuds.classes.Cuds._session = default_session
        default_session = CoreSession()
        cuds.classes.Cuds._session = default_session
        a = cuds.classes.City("Freiburg")
        self.assertIs(a.session, default_session)
        with CoreSession() as session:
            b = create_from_cuds(a, session)
            self.assertEqual(b.name, "Freiburg")
            self.assertEqual(b.uid, a.uid)
            self.assertEqual(set(default_session._registry.keys()), {a.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
            self.assertEqual(set(session._registry.keys()), {b.uid})
            self.assertIs(session._registry.get(b.uid), b)

            b.name = "Emmendingen"
            x = cuds.classes.Citizen(age=54, name="Franz")
            b.add(x, rel=cuds.classes.HasInhabitant)
            y = cuds.classes.Citizen(age=21, name="Rolf")
            a.add(y, rel=cuds.classes.HasInhabitant)

            c = create_from_cuds(a, session)
            self.assertIs(b, c)
            self.assertEqual(c.name, "Freiburg")
            self.assertEqual(len(c.get(rel=cuds.classes.Relationship)), 1)
            self.assertEqual(c[cuds.classes.HasInhabitant],
                             {y.uid: cuds.classes.Citizen.cuba_key})
            self.assertEqual(set(default_session._registry.keys()),
                             {a.uid, x.uid, y.uid})
            self.assertIs(default_session._registry.get(a.uid), a)
