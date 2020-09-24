"""Test the API with the EMMO ontology."""

import unittest2 as unittest
import uuid

from osp.core.utils import create_from_cuds_object
from osp.core.session.core_session import CoreSession
from osp.core.namespaces import cuba

try:
    from osp.core.namespaces import math, holistic, mereotopology, perceptual
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.namespaces import _namespace_registry
    Parser(_namespace_registry._graph).parse("emmo")
    _namespace_registry.update_namespaces()
    math = _namespace_registry.math
    holistic = _namespace_registry.holistic
    mereotopology = _namespace_registry.mereotopology
    perceptual = _namespace_registry.perceptual


class TestAPIEmmo(unittest.TestCase):
    """Test the API with the EMMO ontology."""

    def test_is_a(self):
        """Test instance check."""
        # TODO update emmo
        c = math.Real(hasNumericalData=12)
        self.assertTrue(c.is_a(math.Number))
        self.assertTrue(c.is_a(math.Numerical))
        self.assertTrue(c.is_a(cuba.Class))
        self.assertFalse(c.is_a(cuba.relationship))
        self.assertFalse(c.is_a(math.Integer))
        self.assertFalse(c.is_a(holistic.Process))

    def test_creation(self):
        """Test the instantiation and type of the objects."""
        self.assertRaises(TypeError, math.Real, hasNumericalData=1.2,
                          uid=0, unwanted="unwanted")
        self.assertRaises(TypeError, math.Real)

        r = math.Real(hasNumericalData=1.2, hasSymbolData="1.2")
        r2 = math.Real(hasNumericalData=1.2)
        p = holistic.Process()
        self.assertEqual(r.oclass, math.Real)
        self.assertEqual(r2.oclass, math.Real)
        self.assertEqual(p.oclass, holistic.Process)
        cuba.Wrapper(session=CoreSession())

    def test_uid(self):
        """Tests that the uid variable contains a UUID object."""
        c = holistic.Process()
        self.assertIsInstance(c.uid, uuid.UUID)

    def test_set_throws_exception(self):
        """Test that setting a value for an invlid key throws an error."""
        c = holistic.Process()
        self.assertRaises(ValueError, c._neighbors.__setitem__,
                          "not an allowed key", 15)

    def test_add(self):
        """Test the standard, normal behavior of the add() method."""
        p = holistic.Process()
        n = math.Real(hasNumericalData=1.2)

        p.add(n)
        self.assertEqual(p.get(n.uid).uid, n.uid)

        # Test the inverse relationship
        get_inverse = n.get(rel=mereotopology.hasPart.inverse)
        self.assertEqual(get_inverse, [p])

    def test_get(self):
        """Test the standard, normal behavior of the get() method.

        - get()
        - get(*uids)
        - get(rel)
        - get(oclass)
        - get(*uids, rel)
        - get(rel, oclass)
        """
        p = holistic.Process()
        n = math.Real(hasNumericalData=1.2)
        i = math.Integer(hasNumericalData=42)
        p.add(n)
        p.add(i, rel=mereotopology.hasProperPart)

        # get()
        get_default = p.get()
        self.assertEqual(set(get_default), {i, n})

        # get(*uids)
        get_n_uid = p.get(n.uid)
        self.assertEqual(get_n_uid, n)
        get_i_uid = p.get(i.uid)
        self.assertEqual(get_i_uid, i)
        get_ni_uid = p.get(n.uid, i.uid)
        self.assertEqual(set(get_ni_uid), {n, i})
        get_new_uid = p.get(uuid.uuid4())
        self.assertEqual(get_new_uid, None)

        # get(rel)
        get_has_part = p.get(rel=mereotopology.hasPart)
        self.assertEqual(set(get_has_part), {n, i})
        get_encloses = p.get(rel=mereotopology.hasProperPart)
        self.assertEqual(set(get_encloses), {i})
        get_inhabits = p.get(rel=mereotopology.hasPart.inverse)
        self.assertEqual(get_inhabits, [])

        # get(oclass)
        get_citizen = p.get(oclass=math.Numerical)
        self.assertEqual(set(get_citizen), {i, n})
        get_real = p.get(oclass=math.Real)
        self.assertEqual(set(get_real), {n})
        get_integer = p.get(oclass=math.Integer)
        self.assertEqual(set(get_integer), {i})
        get_process = p.get(oclass=holistic.Process)
        self.assertEqual(get_process, [])

    def test_update(self):
        """Test the standard, normal behavior of the update() method."""
        c = holistic.Process()
        n = math.Real(hasNumericalData=1.2)
        new_n = create_from_cuds_object(n, CoreSession())
        new_s = math.Integer(hasNumericalData=42)
        new_n.add(new_s)
        c.add(n)

        old_real = c.get(n.uid)
        old_integers = old_real.get(oclass=math.Integer)
        self.assertEqual(old_integers, [])

        c.update(new_n)

        new_real = c.get(n.uid)
        new_integers = new_real.get(oclass=math.Integer)
        self.assertEqual(new_integers, [new_s])

        self.assertRaises(ValueError, c.update, n)

    def test_remove(self):
        """Test the standard, normal behavior of the remove() method.

        - remove()
        - remove(*uids/DataContainers)
        - remove(rel)
        - remove(oclass)
        - remove(rel, oclass)
        - remove(*uids/DataContainers, rel)
        """
        c = holistic.Process()
        n = math.Integer(hasNumericalData=12)
        p = math.Real(hasNumericalData=1.2)
        q = math.Real(hasNumericalData=4.2)
        c.add(n)
        c.add(q, p, rel=mereotopology.hasProperPart)

        self.assertIn(mereotopology.hasPart, c._neighbors)
        self.assertIn(mereotopology.hasProperPart, c._neighbors)

        # remove()
        c.remove()
        self.assertFalse(c._neighbors)
        # inverse
        get_inverse = p.get(rel=mereotopology.hasPart.inverse)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers)
        c.add(n)
        c.add(p, q, rel=mereotopology.hasProperPart)
        get_all = c.get()
        self.assertIn(p, get_all)
        c.remove(p.uid)
        get_all = c.get()
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=mereotopology.hasPart.inverse)
        self.assertEqual(get_inverse, [])

        # remove(rel)
        c.remove(rel=mereotopology.hasProperPart)
        self.assertNotIn(mereotopology.hasProperPart, c._neighbors)
        # inverse
        get_inverse = p.get(rel=mereotopology.hasProperPart.inverse)
        self.assertEqual(get_inverse, [])

        # remove(oclass)
        c.remove(oclass=math.Integer)
        self.assertNotIn(n, c.get())
        # inverse
        get_inverse = n.get(rel=mereotopology.hasProperPart.inverse)
        self.assertEqual(get_inverse, [])

        # remove(*uids/DataContainers, rel)
        c.add(p, q, rel=mereotopology.hasProperPart)
        self.assertIn(mereotopology.hasProperPart, c._neighbors)
        c.remove(q, p, rel=mereotopology.hasProperPart)
        self.assertNotIn(mereotopology.hasProperPart, c._neighbors)
        # inverse
        get_inverse = p.get(rel=mereotopology.hasProperPart.inverse)
        self.assertEqual(get_inverse, [])

        # remove(rel, oclass)
        c.add(p, rel=mereotopology.hasProperPart)
        c.add(n)
        c.remove(rel=mereotopology.hasProperPart,
                 oclass=math.Numerical)
        get_all = c.get()
        self.assertIn(n, get_all)
        self.assertNotIn(p, get_all)
        # inverse
        get_inverse = p.get(rel=mereotopology.hasProperPart.inverse)
        self.assertEqual(get_inverse, [])

    def test_iter(self):
        """Test the iter() method when no ontology class is provided."""
        c = holistic.Process()
        n = math.Integer(hasNumericalData=12)
        p = math.Real(hasNumericalData=1.2)
        q = holistic.Process()
        c.add(n)
        c.add(p, q, rel=mereotopology.hasProperPart)

        elements = set(list(c.iter()))
        self.assertEqual(elements, {n, p, q})

    def test_get_attributes(self):
        """Test getting the attributes."""
        p = math.Real(hasNumericalData=1.2)
        self.assertEqual(
            p.get_attributes(),
            {math.hasNumericalData: "1.2"}  # TODO type conversion
        )


if __name__ == '__main__':
    unittest.main()
