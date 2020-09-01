"""Test the API of CUDS objects using the CITY ontology."""

import unittest2 as unittest
import uuid

from osp.core.utils import clone_cuds_object, create_from_cuds_object, \
    get_neighbor_diff
from osp.core.session.core_session import CoreSession
from osp.core.cuds import Cuds
from osp.core.namespaces import cuba

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("city")
    _namespace_registry.update_namespaces()
    city = _namespace_registry.city


class TestAPICity(unittest.TestCase):
    """Test the API of CUDS objects using the CITY ontology."""

    def test_is_a(self):
        """Test instance check."""
        c = city.City(name="City")
        self.assertTrue(c.is_a(city.City))
        self.assertTrue(c.is_a(city.PopulatedPlace))
        self.assertTrue(c.is_a(cuba.Class))
        self.assertFalse(c.is_a(cuba.relationship))
        self.assertFalse(c.is_a(city.Citizen))
        self.assertFalse(c.is_a(city.Neighborhood))

    def test_creation(self):
        """Tests the instantiation and type of the objects."""
        self.assertRaises(TypeError, city.City, name="name",
                          coordinates=[1, 2], uid=0, unwanted="unwanted")
        self.assertRaises(TypeError, city.City)

        c = city.City(name="a city")
        p = city.Person()
        self.assertEqual(c.oclass, city.City)
        self.assertEqual(p.oclass, city.Person)

        self.assertRaises(TypeError, cuba.Nothing)
        self.assertRaises(TypeError, cuba.Wrapper)
        cuba.Wrapper(session=CoreSession())

    def test_uid(self):
        """Tests that the uid variable contains a UUID object."""
        c = city.City(name="a city")
        self.assertIsInstance(c.uid, uuid.UUID)

    def test_set_throws_exception(self):
        """Thest that setting an invalid key throws an exception."""
        c = city.City(name="a city")
        self.assertRaises(ValueError, c._neighbors.__setitem__,
                          "not an allowed key", 15)

    def test_add(self):
        """Tests the standard, normal behavior of the add() method."""
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        p = city.Citizen()

        c.add(n)
        self.assertEqual(c.get(n.uid).uid, n.uid)

        # Test the inverse relationship
        get_inverse = n.get(rel=city.isPartOf)
        self.assertEqual(get_inverse, [c])

        c.add(p, rel=city.hasInhabitant)
        self.assertEqual(c.get(p.uid).uid, p.uid)

    def test_add_throws_exception(self):
        """Tests the add() method for unusual behaviors.

        - Adding an object that is already there
        - Adding an unsupported object
        """
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")

        c.add(n)
        self.assertRaises(ValueError, c.add, n)
        self.assertRaises(TypeError, c.add, "Not a CUDS objects")

    def test_recursive_add(self):
        """Tests if add() works correctly.

        In this test case the added cuds_object is from another session.
        """
        c = city.City(name="City")
        p1 = city.Citizen()
        c.add(p1, rel=city.hasInhabitant)

        second_session = CoreSession()
        w = city.CityWrapper(session=second_session)
        cw = w.add(c)
        p1w = cw.get(p1.uid)
        self.assertIs(cw.session, second_session)
        self.assertIs(p1w.session, second_session)
        self.assertIsNot(c.session, second_session)
        self.assertIsNot(p1.session, second_session)
        self.assertTrue(c._stored)
        self.assertTrue(p1._stored)
        self.assertTrue(w._stored)
        self.assertTrue(cw._stored)
        self.assertTrue(p1w._stored)

        p2 = city.Citizen()
        p3 = city.Citizen()
        p4 = city.Citizen()
        c.add(p2, p3, rel=city.hasInhabitant)
        p1.add(p2, rel=city.hasChild)
        p3.add(p2, rel=city.hasChild)
        p2.add(p4, rel=city.hasChild)

        cw.add(p2, rel=city.hasInhabitant)
        p2w = cw.get(p2.uid)
        p4w = p2w.get(p4.uid)

        # check if there are unexpected changes in the first session
        # first check active relationships
        self.assertEqual(set(c._neighbors[city.hasInhabitant].keys()),
                         set([p1.uid, p2.uid, p3.uid]))
        self.assertEqual(set([p2.uid]),
                         set(p1._neighbors[city.hasChild].keys()))
        self.assertEqual(set([p2.uid]),
                         set(p3._neighbors[city.hasChild].keys()))
        self.assertEqual(set([p4.uid]), set(
            p2._neighbors[city.hasChild].keys()))

        # check passive relationships
        self.assertEqual(
            set([c.uid]),
            set(p1._neighbors[city.INVERSE_OF_hasInhabitant].keys()))
        self.assertEqual(
            set([p1.uid, p3.uid]),
            set(p2._neighbors[city.isChildOf].keys()))
        self.assertEqual(
            set([c.uid]),
            set(p2._neighbors[city.INVERSE_OF_hasInhabitant].keys()))
        self.assertEqual(
            set([c.uid]),
            set(p3._neighbors[city.INVERSE_OF_hasInhabitant].keys()))
        self.assertEqual(
            set([p2.uid]),
            set(p4._neighbors[city.isChildOf].keys()))

        # check if items correctly added in second session
        # active relations
        self.assertEqual(set(cw._neighbors[city.hasInhabitant].keys()),
                         set([p1w.uid, p2w.uid]))
        self.assertEqual(set([p2w.uid]),
                         set(p1w._neighbors[city.hasChild].keys()))
        self.assertEqual(set([p4w.uid]),
                         set(p2w._neighbors[city.hasChild].keys()))

        # passive relations
        self.assertEqual(
            set([cw.uid]),
            set(p1w._neighbors[city.INVERSE_OF_hasInhabitant].keys()))
        self.assertEqual(
            set([p1w.uid]),
            set(p2w._neighbors[city.isChildOf].keys()))
        self.assertEqual(
            set([cw.uid]),
            set(p2w._neighbors[city.INVERSE_OF_hasInhabitant].keys()))
        self.assertEqual(
            set([p2w.uid]),
            set(p4w._neighbors[city.isChildOf].keys()))

    def test_fix_neighbors(self):
        """Test fixing the neighbors after replacing CUDS objects."""
        w1 = city.CityWrapper(session=CoreSession())
        w2 = city.CityWrapper(session=CoreSession())

        c1w1 = city.City(name="city1")  # parent in both wrappers
        c2w1 = city.City(name="city2")  # parent in w1, not present in w2
        c3w1 = city.City(name="city3")  # parent only in w1, present in w2
        c4w1 = city.City(name="city4")  # parent only in w2
        p1w1 = city.Citizen(name="citizen")
        p2w1 = city.Citizen(name="child")

        w2.add(c1w1, c3w1, c4w1)
        c1w2, c3w2, c4w2 = w2.get(c1w1.uid, c3w1.uid, c4w1.uid)
        c1w2.add(p1w1, rel=city.hasInhabitant)
        c4w2.add(p1w1, rel=city.hasInhabitant)
        p1w2 = c1w2.get(p1w1.uid)
        p1w2.add(p2w1, rel=city.hasChild)
        p2w2 = p1w2.get(p2w1.uid)

        w1.add(c1w1, c2w1, c3w1, c4w1)
        c1w1.add(p1w1, rel=city.hasInhabitant)
        c2w1.add(p1w1, rel=city.hasInhabitant)
        c3w1.add(p1w1, rel=city.hasInhabitant)

        self.assertEqual(
            set(p1w1._neighbors[city.INVERSE_OF_hasInhabitant].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid]))
        self.assertEqual(
            set(p2w2._neighbors[city.isChildOf].keys()),
            set([p1w2.uid]))

        missing = dict()
        Cuds._fix_neighbors(new_cuds_object=p1w1,
                            old_cuds_object=p1w2,
                            session=p1w2.session,
                            missing=missing)

        # check if connections cuds_objects that are no
        # longer parents are in the missing dict
        self.assertIn(c2w1.uid, missing)
        self.assertEqual(
            set(p1w1._neighbors[city.INVERSE_OF_hasInhabitant].keys()),
            set([c1w1.uid, c2w1.uid, c3w1.uid, c4w1.uid]))
        self.assertNotIn(city.isPartOf, p2w2._neighbors)

        # check if there are no unexpected other changes
        self.assertEqual(
            set(c1w1._neighbors[city.hasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c2w1._neighbors[city.hasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w1._neighbors[city.hasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertNotIn(city.hasInhabitant, c4w1._neighbors)

        # check if the parents in w2 have been updated
        self.assertEqual(
            set(c1w2._neighbors[city.hasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c3w2._neighbors[city.hasInhabitant].keys()),
            set([p1w1.uid]))
        self.assertEqual(
            set(c4w2._neighbors[city.hasInhabitant].keys()),
            set([p1w1.uid]))

    def test_get(self):
        """Tests the standard, normal behavior of the get() method.

        - get()
        - get(*uids)
        - get(rel)
        - get(oclass)
        - get(*uids, rel)
        - get(rel, oclass)
        """
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        p = city.Citizen(name="John Smith")
        q = city.Citizen(name="Jane Doe")
        c.add(n)
        c.add(p, q, rel=city.hasInhabitant)

        # get()
        get_default = c.get()
        self.assertEqual(set(get_default), {n, p, q})

        # get(*uids)
        get_p_uid = c.get(p.uid)
        self.assertEqual(get_p_uid, p)
        get_q_uid = c.get(q.uid)
        self.assertEqual(get_q_uid, q)
        get_nq_uid = c.get(n.uid, q.uid)
        self.assertEqual(set(get_nq_uid), {n, q})
        get_new_uid = c.get(uuid.uuid4())
        self.assertEqual(get_new_uid, None)

        # get(rel)
        get_has_part = c.get(rel=city.hasInhabitant)
        self.assertEqual(set(get_has_part), {p, q})
        get_encloses = c.get(rel=city.encloses)
        self.assertEqual(set(get_encloses), {n, p, q})
        get_inhabits = c.get(rel=city.INVERSE_OF_hasInhabitant)
        self.assertEqual(get_inhabits, [])

        # get(oclass)
        get_citizen = c.get(oclass=city.Citizen)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(oclass=city.Building)
        self.assertEqual(get_building, [])
        get_citizen = c.get(oclass=city.Person)
        self.assertEqual(set(get_citizen), {q, p})
        get_building = c.get(
            oclass=city.ArchitecturalStructure)
        self.assertEqual(get_building, [])

        # get(*uids, rel)
        get_has_part_p = c.get(p.uid, rel=city.hasInhabitant)
        self.assertEqual(get_has_part_p, p)

        get_has_part_q = c.get(q.uid, rel=city.hasPart)
        self.assertEqual(get_has_part_q, None)

        # get(rel, oclass)
        get_inhabited_citizen = c.get(rel=city.hasInhabitant,
                                      oclass=city.Citizen)
        self.assertEqual(set(get_inhabited_citizen), {p, q})

        # return_rel=True
        get_p_uid, get_p_rel = c.get(p.uid, return_rel=True)
        self.assertEqual(get_p_uid, p)
        self.assertEqual(get_p_rel, city.hasInhabitant)
        result = c.get(rel=city.encloses, return_rel=True)
        self.assertEqual(set(result), set([
            (p, city.hasInhabitant),
            (q, city.hasInhabitant),
            (n, city.hasPart)
        ]))

    def test_get_throws_exception(self):
        """Tests the get() method for unusual behaviors.

        - Getting with a wrong type
        - Getting with a not allowed combination of arguments
        """
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        c.add(n)

        self.assertRaises(TypeError, c.get, "not a proper key")
        self.assertRaises(TypeError, c.get,
                          n.uid,
                          oclass=city.Neighborhood)
        self.assertRaises(ValueError, c.get, oclass=city.hasInhabitant)
        self.assertRaises(ValueError, c.get, rel=city.Citizen)

    def test_update(self):
        """Tests the standard, normal behavior of the update() method."""
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        new_n = create_from_cuds_object(n, CoreSession())
        new_s = city.Street(name="a new street")
        new_n.add(new_s)
        c.add(n)

        old_neighborhood = c.get(n.uid)
        old_streets = old_neighborhood.get(
            oclass=city.Street)
        self.assertEqual(old_streets, [])

        c.update(new_n)

        new_neighborhood = c.get(n.uid)
        self.assertIs(new_neighborhood, n)
        new_streets = new_neighborhood.get(
            oclass=city.Street)
        self.assertEqual(new_streets, [new_s])

        self.assertRaises(ValueError, c.update, n)

    def test_remove(self):
        """Tests the standard, normal behavior of the remove() method.

        - remove()
        - remove(*uids/DataContainers)
        - remove(rel)
        - remove(oclass)
        - remove(rel, oclass)
        - remove(*uids/DataContainers, rel)
        """
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        p = city.Citizen(name="John Smith")
        q = city.Citizen(name="Jane Doe")
        c.add(n)
        c.add(q, p, rel=city.hasInhabitant)

        self.assertIn(city.hasPart, c._neighbors)
        self.assertIn(city.hasInhabitant, c._neighbors)

        # remove()
        c.remove()
        self.assertFalse(c._neighbors)
        # inverse
        get_inverse = p.get(rel=city.isPartOf)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers)
        c.add(n)
        c.add(p, q, rel=city.hasInhabitant)
        get_all = c.get()
        self.assertIn(p, get_all)
        c.remove(p.uid)
        get_all = c.get()
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=city.isPartOf)
        self.assertEqual(get_inverse, [])

        # remove(rel)
        c.remove(rel=city.hasPart)
        self.assertNotIn(city.hasPart, c._neighbors)
        # inverse
        get_inverse = n.get(rel=city.isPartOf)
        self.assertEqual(get_inverse, [])

        # remove(oclass)
        c.remove(oclass=city.Citizen)
        self.assertNotIn(q, c.get())
        # inverse
        get_inverse = q.get(rel=city.INVERSE_OF_hasInhabitant)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers, rel)
        c.add(p, q, rel=city.hasInhabitant)
        self.assertIn(city.hasInhabitant, c._neighbors)
        c.remove(q, p, rel=city.hasInhabitant)
        self.assertNotIn(city.hasInhabitant, c._neighbors)
        # inverse
        get_inverse = p.get(rel=city.INVERSE_OF_hasInhabitant)
        self.assertEqual(get_inverse, [])

        # remove(rel, oclass)
        c.add(p, rel=city.hasInhabitant)
        c.add(n)
        c.remove(rel=city.hasInhabitant,
                 oclass=city.Citizen)
        get_all = c.get()
        self.assertIn(n, get_all)
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=city.INVERSE_OF_hasInhabitant)
        self.assertEqual(get_inverse, [])

    def test_remove_throws_exception(self):
        """Tests the remove() method for unusual behaviors.

        - Removing with a wrong key
        - Removing something non-existent
        - Removing with a not allowed argument combination
        """
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")

        # Wrong key
        self.assertRaises(TypeError, c.remove, "not a proper key")

        # Non-existent
        self.assertRaises(RuntimeError, c.remove, n.uid)
        self.assertRaises(RuntimeError, c.remove, rel=city.hasPart)
        self.assertRaises(RuntimeError, c.remove,
                          oclass=city.Street)
        self.assertRaises(
            RuntimeError, c.remove, n.uid, rel=city.hasPart)

        # Wrong arguments
        self.assertRaises(TypeError, c.remove, n.uid,
                          oclass=city.Street)

    def test_update_throws_exception(self):
        """Tests the update() method for unusual behaviors.

        - Update an element that wasn't added before
        """
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        c.add(n)
        p = city.Citizen()
        self.assertRaises(ValueError, c.update, p)

    def test_iter(self):
        """Tests the iter() method when no ontology class is provided."""
        c = city.City(name="a city")
        n = city.Neighborhood(name="a neighborhood")
        p = city.Citizen(name="John Smith")
        q = city.Citizen(name="Jane Doe")
        c.add(n)
        c.add(p, q, rel=city.hasInhabitant)

        elements = set(list(c.iter()))
        self.assertEqual(elements, {n, p, q})

        # return_rel=True
        get_p_uid, get_p_rel = next(c.iter(p.uid, return_rel=True))
        self.assertEqual(get_p_uid, p)
        self.assertEqual(get_p_rel, city.hasInhabitant)
        result = c.iter(rel=city.encloses, return_rel=True)
        self.assertEqual(set(result), set([
            (p, city.hasInhabitant),
            (q, city.hasInhabitant),
            (n, city.hasPart)
        ]))

    # def test_check_valid_add(self):  # TODO
    #     """Check if _check_valid_add throws exceptions when illegal
    #     relationships are added.
    #     """
    #     c = cuds.classes.PopulatedPlace("Freiburg")
    #     p1 = cuds.classes.Person(name="Peter")
    #     c.add(p1, rel=cuds.classes.HasWorker)
    #     p2 = city.Citizen(name="Martin")
    #     c.add(p2, rel=cuds.classes.HasWorker)
    #     p3 = cuds.classes.LivingBeing(name="Mimi")
    #     self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)
    #     c.remove()

    #     c.add(p1, rel=cuds.classes.HasMajor)
    #     c.add(p2, rel=cuds.classes.HasMajor)
    #     self.assertRaises(ValueError, c.add, p1, rel=city.hasPart)

    #     c = city.City("Freiburg")
    #     c.add(p1, rel=cuds.classes.HasWorker)
    #     c.add(p2, rel=cuds.classes.HasWorker)
    #     self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)

    #     c = cuds.classes.GeographicalPlace("Freiburg")
    #     self.assertRaises(ValueError, c.add, p1, rel=cuds.classes.HasWorker)
    #     self.assertRaises(ValueError, c.add, p2, rel=cuds.classes.HasWorker)
    #     self.assertRaises(ValueError, c.add, p3, rel=cuds.classes.HasWorker)

    #     Cuds.CUDS_SETTINGS["check_relationship_supported"] = False
    #     c.add(p1, rel=cuds.classes.HasWorker)
    #     c.add(p2, rel=cuds.classes.HasWorker)
    #     c.add(p3, rel=cuds.classes.HasWorker)
    #     Cuds.CUDS_SETTINGS["check_relationship_supported"] = True

    def test_recursive_store(self):
        """Test if _recursive_store correctly stores cuds_objects correctly.

        It should correct dangling and one-way connections.
        """
        c = city.City(name="Freiburg")
        with CoreSession() as session:
            w = city.CityWrapper(session=session)
            cw = w.add(c)

            p1 = city.Citizen()
            p2 = city.Citizen()
            p3 = city.Citizen()
            p4 = city.Citizen()
            c.add(p1, p2, p3, rel=city.hasInhabitant)
            p3.add(p1, p2, rel=city.isChildOf)
            p3.add(p4, rel=city.hasChild)

            cw = w._recursive_store(c, cw)

            p1w, p2w, p3w = cw.get(p1.uid, p2.uid, p3.uid)
            p4w = p3w.get(p4.uid)

            self.assertEqual(w.get(rel=city.hasPart), [cw])
            self.assertEqual(
                set(cw.get(rel=city.hasInhabitant)),
                {p1w, p2w, p3w}
            )
            self.assertEqual(
                set(cw.get(rel=city.isPartOf)),
                {w}
            )

            self.assertEqual(p3w.get(rel=city.INVERSE_OF_hasInhabitant), [cw])
            self.assertEqual(
                set(p3w.get(rel=city.isChildOf)),
                {p1w, p2w}
            )
            self.assertEqual(p3w.get(rel=city.hasChild), [p4w])

    def test_fix_new_parents(self):
        """Check _fix_new_parent.

        Make sure the method:
        - Deletes connection to new parents not available in new session
        - Adds connection to new parents available in new session
        """
        n = city.Neighborhood(name="Zähringen")
        # parent in both sessions
        c1 = city.City(name="Berlin")
        # only parent in default session (available in both)
        c2 = city.City(name="Paris")
        n.add(c1, c2, rel=city.isPartOf)

        with CoreSession() as session:
            wrapper = city.CityWrapper(session=session)
            c1w, c2w = wrapper.add(c1, c2)
            nw = c2w.get(n.uid)
            nw.remove(c2.uid, rel=cuba.relationship)

            # only parent + available in default session
            c3 = city.City(name="London")
            n.add(c3, rel=city.isPartOf)

            n = clone_cuds_object(n)
            n._session = session
            new_parent_diff = get_neighbor_diff(
                n, nw, mode="non-active")
            new_parents = session.load(*[x[0] for x in new_parent_diff])

            missing = dict()
            Cuds._fix_new_parents(new_cuds_object=n,
                                  new_parents=new_parents,
                                  new_parent_diff=new_parent_diff,
                                  missing=missing)

        self.assertEqual(
            set(n.get(rel=city.isPartOf)),
            {c1w, c2w, None}  # missing parent, should be in missing dict
        )
        self.assertEqual(missing, {c3.uid: [(n, city.isPartOf)]})
        self.assertEqual(c2w.get(rel=city.hasPart), [n])

    def test_fix_old_neighbors(self):
        """Check if _fix_old_neighbors.

        - Deletes old children.
        - Adds connection to old parents.
        """
        c = city.City(name="Freiburg")

        with CoreSession() as session:
            wrapper = city.CityWrapper(session=session)
            cw = wrapper.add(c)
            n = city.Neighborhood(name="Zähringen")
            nw = cw.add(n)

            c = clone_cuds_object(c)
            c._session = session
            old_neighbor_diff = get_neighbor_diff(cw, c)
            old_neighbors = session.load(*[x[0] for x in old_neighbor_diff])
            Cuds._fix_old_neighbors(new_cuds_object=c,
                                    old_cuds_object=cw,
                                    old_neighbors=old_neighbors,
                                    old_neighbor_diff=old_neighbor_diff)
        self.assertEqual(c.get(rel=city.isPartOf), [wrapper])
        self.assertEqual(c.get(rel=city.hasPart), [])
        self.assertEqual(nw.get(rel=city.isPartOf), [])
        self.assertEqual(wrapper.get(rel=city.hasPart), [c])

    def test_add_twice(self):
        """Test what happens if you add the same object twice."""
        p = city.Citizen(name="Ralf")
        c1 = city.City(name="Freiburg")
        c2 = city.City(name="Offenburg")
        with CoreSession() as session:
            w = city.CityWrapper(session=session)
            c1w, c2w = w.add(c1, c2)
            pw1 = c1w.add(p, rel=city.hasInhabitant)
            pw2 = c2w.add(p, rel=city.hasInhabitant)
            self.assertIs(pw1, pw2)
            self.assertEqual(set(pw1.get(rel=city.INVERSE_OF_hasInhabitant)),
                             {c1w, c2w})

    def test_get_attributes(self):
        """Test getting the attributes of CUDS objects."""
        p = city.Citizen(name="Ralf")
        self.assertEqual(
            p.get_attributes(),
            {city.name: "Ralf", city.age: 25}
        )

    def test_add_multi_session(self):
        """Test the add method in a comext of multiple sessions."""
        with CoreSession() as session:
            wrapper = cuba.Wrapper(session=session)
            aw = cuba.Class(session=session)
            b = cuba.Class()
            c = cuba.Class()
            bw = aw.add(b, rel=cuba.activeRelationship)
            c.add(b, rel=cuba.activeRelationship)
            wrapper.add(c, rel=cuba.activeRelationship)
            self.assertIn(bw, aw.get(rel=cuba.activeRelationship))
            self.assertIn(aw, bw.get(rel=cuba.passiveRelationship))


if __name__ == '__main__':
    unittest.main()
