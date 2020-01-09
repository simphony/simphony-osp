from osp.core import city

c = city.City(name="Freiburg")
p = city.Citizen(name="Peter")
c.add(p, rel=city.HasInhabitant)

r = c.session.sparql_query("SELECT DISTINCT ?d ?b WHERE {<%s> ?d ?b . }" % (
    c.get_iri()))
print(list(r))
