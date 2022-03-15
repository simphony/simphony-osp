"""Test the API of CUDS objects using the foaf ontology."""

import unittest2 as unittest

from osp.core.ontology.datatypes import UID

try:
    from osp.core.namespaces import foaf
except ImportError:
    from osp.core.ontology.parser.parser import OntologyParser
    from osp.core.ontology.namespace_registry import namespace_registry
    namespace_registry.load_parser(OntologyParser.get_parser("foaf"))
    foaf = namespace_registry.foaf


class TestAPIfoaf(unittest.TestCase):
    """Test the API of CUDS objects using the foaf ontology."""

    def test_creation(self):
        """Test creation of objectes are possible."""
        c = foaf.Person()
        self.assertTrue(c.is_a(foaf.Person))

    def test_uid(self):
        """Test that the uid variable contains an uid."""
        c = foaf.Person()
        self.assertIsInstance(c.uid, UID)

    def test_relations(self):
        """Test some relationships."""
        a = foaf.Person()
        b = foaf.Person()
        b.add(a, rel=foaf.knows)
        self.assertSetEqual(b.get(rel=foaf.knows), {a})

    def test_throw_exception(self):
        """Test some exceptions."""
        c = foaf.Person()
        c.age = 20
        # self.assertRaises(AttributeError, c.__setattr__, "age", "2.2")

    def test_bracket_notation(self):
        """Tests the functionality of the bracket notation.

        Only tests attributes, as all the the relationships are tested on
        test_apy_city.TestAPICity.test_bracket_notation.
        """
        marc = foaf.Person()

        # --- Test attributes ---

        # Basic functionality, assignment using single elements.
        self.assertSetEqual(set(), marc[foaf.name])
        marc[foaf.name] = 'Marc'
        self.assertSetEqual({'Marc'}, marc[foaf.name])
        marc[foaf.name] = 'Marco'
        self.assertSetEqual({'Marco'}, marc[foaf.name])
        marc[foaf.name] = 'Marc'
        del marc[foaf.name]
        self.assertSetEqual(set(), marc[foaf.name])
        marc[foaf.name] = 'Marc'
        marc[foaf.name] = None
        self.assertSetEqual(set(), marc[foaf.name])
        marc[foaf.name] = 'Marc'
        self.assertRaises(TypeError,
                          lambda x: marc.__setitem__(foaf.name, x),
                          marc)

        # Set features, assignment using sets.
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        self.assertSetEqual({'Marc'}, marc[foaf.nick])
        marc[foaf.nick] = set()
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        marc[foaf.nick] = None
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        del marc[foaf.nick]
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        marc[foaf.nick].clear()
        self.assertEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        self.assertIn('Marc', marc[foaf.nick])
        self.assertNotIn('Aimee', marc[foaf.nick])
        self.assertSetEqual({'Marc'}, set(marc[foaf.nick]))
        self.assertEqual(1, len(marc[foaf.nick]))
        self.assertLessEqual(marc[foaf.nick], {'Marc'})
        self.assertLessEqual(marc[foaf.nick], {'Marc', 'Aimee'})
        self.assertFalse(marc[foaf.nick] <= set())
        self.assertLess(marc[foaf.nick], {'Marc', 'Aimee'})
        self.assertFalse(marc[foaf.nick] < {'Marc'})
        self.assertEqual({'Marc'}, marc[foaf.nick])
        self.assertNotEqual(marc[foaf.nick], {'Marc', 'Aimee'})
        self.assertNotEqual(marc[foaf.nick], set())
        self.assertGreater(marc[foaf.nick], set())
        self.assertGreaterEqual(marc[foaf.nick], set())
        self.assertGreaterEqual(marc[foaf.nick], {'Marc'})
        self.assertFalse(marc[foaf.nick] >= {'Marc', 'Aimee'})
        self.assertSetEqual(set(), marc[foaf.nick] & set())
        self.assertSetEqual({'Marc'}, marc[foaf.nick] & {'Marc'})
        self.assertSetEqual(set(), marc[foaf.nick] & {'Aimee'})
        self.assertSetEqual({'Marc', 'Aimee'},
                            marc[foaf.nick] | {'Aimee'})
        self.assertSetEqual({'Marc'},
                            marc[foaf.nick] | {'Marc'})
        self.assertSetEqual({'Marc'},
                            marc[foaf.nick] | set())
        self.assertSetEqual(set(),
                            marc[foaf.nick] - {'Marc'})
        self.assertSetEqual({'Marc'},
                            marc[foaf.nick] - {'Aimee'})
        self.assertSetEqual({'Marc', 'Aimee'},
                            marc[foaf.nick] ^ {'Aimee'})
        self.assertSetEqual(set(),
                            marc[foaf.nick] ^ {'Marc'})
        self.assertTrue(marc[foaf.nick].isdisjoint({'Aimee'}))
        self.assertFalse(marc[foaf.nick].isdisjoint({'Marc'}))
        self.assertTrue(marc[foaf.nick].isdisjoint(set()))
        self.assertEqual('Marc', marc[foaf.nick].pop())
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        self.assertIsNot(marc[foaf.nick],
                         marc[foaf.nick].copy())
        self.assertSetEqual(marc[foaf.nick], marc[foaf.nick].copy())
        self.assertSetEqual(set(),
                            marc[foaf.nick].difference({'Marc'}))
        self.assertSetEqual({'Marc'},
                            marc[foaf.nick].difference({'Aimee'}))
        marc[foaf.nick].difference_update({'Aimee'})
        self.assertSetEqual({'Marc'}, marc[foaf.nick])
        marc[foaf.nick].difference_update({'Marc'})
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        marc[foaf.nick].discard('Aimee')
        self.assertSetEqual({'Marc'}, marc[foaf.nick])
        marc[foaf.nick].discard('Marc')
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        self.assertSetEqual({'Marc'},
                            marc[foaf.nick].intersection({'Marc'}))
        self.assertSetEqual(set(),
                            marc[foaf.nick].intersection({'Aimee'}))
        self.assertSetEqual(set(),
                            marc[foaf.nick].intersection(set()))
        marc[foaf.nick].intersection_update({'Marc'})
        self.assertSetEqual({'Marc'}, marc[foaf.nick])
        marc[foaf.nick].intersection_update({'Aimee'})
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Marc'}
        marc[foaf.nick].add('Aimee')
        self.assertSetEqual({'Aimee', 'Marc'}, marc[foaf.nick])
        marc[foaf.nick].remove('Aimee')
        self.assertSetEqual({'Marc'}, marc[foaf.nick])
        self.assertRaises(KeyError,
                          lambda x: marc[foaf.nick].remove(x),
                          'Aimee')
        marc[foaf.nick].update({'Aimee'})
        self.assertSetEqual({'Aimee', 'Marc'}, marc[foaf.nick])
        marc[foaf.nick] |= {'Aimee'}
        self.assertSetEqual({'Aimee', 'Marc'}, marc[foaf.nick])
        marc[foaf.nick] = {}
        marc[foaf.nick] |= {'Aimee'}
        self.assertSetEqual({'Aimee'}, marc[foaf.nick])
        marc[foaf.nick] &= {'Aimee'}
        self.assertSetEqual({'Aimee'}, marc[foaf.nick])
        marc[foaf.nick] &= {marc}
        self.assertSetEqual(set(), marc[foaf.nick])
        marc[foaf.nick] = {'Aimee'}
        marc[foaf.nick] ^= {'Marc'}
        self.assertSetEqual({'Aimee', 'Marc'}, marc[foaf.nick])
        marc[foaf.nick] ^= set()
        self.assertSetEqual({'Aimee', 'Marc'}, marc[foaf.nick])
        marc[foaf.nick] ^= {'Aimee'}
        self.assertSetEqual({'Marc'}, marc[foaf.nick])
        marc[foaf.nick] += {'Aimee'}
        self.assertSetEqual({'Marc', 'Aimee'}, marc[foaf.nick])
        marc[foaf.nick] -= {'Marc'}
        self.assertSetEqual({'Aimee'}, marc[foaf.nick])
        marc[foaf.nick] += 'Marc'
        marc[foaf.nick] += 'Aimee'
        self.assertSetEqual({'Marc', 'Aimee'}, marc[foaf.nick])
        marc[foaf.nick] -= 'Marc'
        self.assertSetEqual({'Aimee'}, marc[foaf.nick])
        marc[foaf.nick] -= 'Aimee'
        self.assertSetEqual(set(), marc[foaf.nick])
        self.assertRaises(TypeError,
                          lambda x: marc.__setitem__(
                              (foaf.nick, slice(None, None, None)),
                              x),
                          {marc})

        # Operations on sub-attributes.
        self.assertSetEqual(set(), marc[foaf.nick])
        self.assertSetEqual(set(), marc[foaf.skypeID])
        marc[foaf.skypeID] += 'marc_skype'
        marc[foaf.nick] += 'marc_discord'
        marc[foaf.nick] = {'marc_skype',
                           'marc_discord'}  # Should not change skypeID.
        self.assertSetEqual({'marc_skype'}, marc[foaf.skypeID])
        self.assertSetEqual({'marc_skype', 'marc_discord'}, marc[foaf.nick])
        marc[foaf.nick] += 'marc_skype'
        marc[foaf.skypeID] -= 'marc_skype'
        self.assertSetEqual({'marc_discord'}, marc[foaf.nick])
        marc[foaf.nick] += 'marc_skype'
        marc[foaf.skypeID] += 'marc_skype'
        self.assertEqual(2, len(marc[foaf.nick]))
        self.assertSetEqual({'marc_skype'}, marc[foaf.skypeID])
        marc[foaf.skypeID] -= 'marc_skype'
        self.assertSetEqual({'marc_skype', 'marc_discord'}, marc[foaf.nick])
        self.assertSetEqual(set(), marc[foaf.skypeID])

        # Test relationships -> goto
        # test_api_city.TestAPICity.test_bracket_notation.


if __name__ == '__main__':
    unittest.main()
