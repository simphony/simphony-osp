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
print("  oclass of c: " + str(c.oclass) + "\n")

print("Creating Citizen objects, p1, p2...")
p1 = city.Citizen(name="Peter")
p2 = city.Citizen(name="Anne")

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
