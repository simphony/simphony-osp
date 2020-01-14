from osp.core import city

c = city.City(name="Freiburg")
p = city.Citizen(name="Peter")
c.add(p, rel=city.HasInhabitant)

r = c.session.sparql_query("SELECT DISTINCT ?a ?b WHERE {?a ?b \"Peter\" . }")
print(list(r))

# r = c.session.sparql_query("SELECT DISTINCT ?b ?c WHERE {<%s> ?b ?c . }" % (
#     c.get_iri()))
# print(list(r))
