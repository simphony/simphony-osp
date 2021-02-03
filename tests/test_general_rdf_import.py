"""Test general RDF data."""

# from osp.core.namespaces import city
# from osp.core.utils import serialize_rdf_graph

# # c = city.City(name="Frankfurt")
# # p = city.Citizen(name="John")
# # n = city.Neighborhood(name="Sachsenhausen")
# # c.add(p, rel=city.hasInhabitant)
# # c.add(n)

# # serialize_rdf_graph("abc.ttl", format="ttl")

# from osp.core.utils import import_rdf_file
# import rdflib

# street = city.Street(name="Some street.")
# import_rdf_file("abc.ttl", format="ttl")
# serialize_rdf_graph("dev.ttl", format="ttl")

# city = next(
#     street.session.load_from_iri(rdflib.URIRef("http://www.random.com#C"))
# )
# print(city)
# print(city.iri)
# print(city.name)
# print(city.coordinates)
