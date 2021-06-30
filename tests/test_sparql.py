"""Test SPARQL queries API (on the core session)."""
import unittest
from osp.core.utils import sparql

try:
    from osp.core.namespaces import city
except ImportError:
    from osp.core.ontology import Parser
    from osp.core.ontology.namespace_registry import namespace_registry
    Parser().parse("city")
    city = namespace_registry.city


class TestSPARQL(unittest.TestCase):
    """Test SPARQL queries API (on the core session)."""

    def test_sparql(self):
        """Test SPARQL by creating a city and performing a very simple query.

        Create a city with a single inhabitant and perform a very simple SPARQL
        query using both the `sparql` function from utils and the sparql method
        of the session.
        """
        freiburg = city.City(name='Freiburg')
        karl = city.Citizen(name="Karl", age=47)
        freiburg.add(karl, rel=city.hasInhabitant)
        core_session = freiburg.session
        query = f"""SELECT ?city_name ?citizen ?citizen_age ?citizen_name
                    WHERE {{ ?city a <{city.City.iri}> .
                             ?city <{city.name.iri}> ?city_name .
                             ?city <{city.hasInhabitant.iri}> ?citizen .
                             ?citizen <{city.name.iri}> ?citizen_name .
                             ?citizen <{city.age.iri}> ?citizen_age .
                          }}
                 """
        results_none = sparql(query, session=None)
        results_core_session = sparql(query, session=core_session)
        results_core_session_method = core_session.sparql(query)
        self.assertEqual(len(results_none), 1)
        self.assertEqual(len(results_core_session), 1)
        self.assertEqual(len(results_core_session_method), 1)
        results = (next(iter(results_none)),
                   next(iter(results_core_session)),
                   next(iter(results_core_session_method)))
        self.assertTrue(all(result['city_name'].toPython() == freiburg.name
                            for result in results))
        self.assertTrue(all(result['citizen'] == karl.iri
                            for result in results))
        self.assertTrue(all(result['citizen_age'].toPython() == karl.age
                            for result in results))
        self.assertTrue(all(result['citizen_name'].toPython() == karl.name
                            for result in results))

        def test_function(iri):
            value = str(iri._value)
            if value == "Freiburg":
                return True
            else:
                return False

        for row in results_core_session(citizen='cuds',
                                        citizen_age=int,
                                        citizen_name=str,
                                        city_name=test_function):
            self.assertTrue(row["citizen"].is_a(karl.oclass))
            self.assertEqual(row["citizen_age"], karl.age)
            self.assertEqual(row["citizen_name"], karl.name)
            self.assertTrue(row["city_name"])

        self.assertDictEqual(
            results_core_session.datatypes,
            dict(
                citizen="cuds",
                citizen_age=int,
                citizen_name=str,
                city_name=test_function
            )
        )


if __name__ == '__main__':
    unittest.main()
