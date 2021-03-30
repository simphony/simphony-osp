"""An example explaining the API of CUDS objects."""

# Please install the city ontology: $pico install city

# If you did not install the city ontology
# (pico install city),
# you have to execute these commands first:
# from osp.core import Parser
# p = Parser()
# p.parse("city")

from osp.core.namespaces import city

print("Creating a City object, c...")
c = city.City(name="Freiburg", coordinates=[47, 7])
print("  uid of c: " + str(c.uid))
print("  IRI of c: " + str(c.iri))
print("  oclass of c: " + str(c.oclass) + "\n")

print("Creating Citizen objects, p1, p2...")
p1 = city.Citizen(name="Peter")
p2 = city.Citizen(name="Anne")
print("  uid of p1: " + str(p1.uid))
print("  IRI of p1: " + str(p1.iri))
print("  oclass of p1: " + str(p1.oclass) + "\n")
print("  uid of p2: " + str(p2.uid))
print("  IRI of p2: " + str(p2.iri))
print("  oclass of p2: " + str(p2.oclass) + "\n")

print("Checking attributes of the CUDS objects...")
print(f"Name of c: {c.name}. Coordinates of c: {c.coordinates}." )
print("Name of p1: " + str(p1.name))
print("Name of p2: " + str(p2.name))

print("\nAdding p1 to c...")
c.add(p1, rel=city.hasInhabitant)
print("internal dict of c:", c._neighbors, "\n")

print("Adding p2 to c...")
c.add(p2, rel=city.hasInhabitant)
print("internal dict of c:", c._neighbors, "\n")

print("\nElements in c:")
for el in c.iter():
    print("  uid: " + str(el.uid))

print("\nGetting p1 from c:")
print(c.get(p1.uid))

print("\nGetting city.Citizen from c:")
print(c.get(oclass=city.Citizen))

print("\n Remove p1:")
c.remove(p1.uid)
print("internal dict of c:", c._neighbors, "\n")

print("\nAdding neighborhoods to Cuds object in a loop:")
for i in range(6):
    print("Added neighborhood %s" % i)
    c.add(city.Neighborhood(
        name="neighborhood %s" % i))
print("internal dict of c:", c._neighbors, "\n")

print('Trying out the `is_a` method trivially with the new neighborhoods.')
print(all(n.is_a(city.Neighborhood) for n in c.get(oclass=city.Neighborhood)))
