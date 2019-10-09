import cuds.classes

"""
The objects without any other entities added are shown as
empty dictionaries '{}'. This is so because the uid, name and other
properties are stored elsewhere and not shown.

This example shows some options how to use the API
"""

print("Creating a City object, c...")
c = cuds.classes.City(name="Freiburg", coordinates=[47, 7])
print("  uid of c: " + str(c.uid))
print("  type of c: " + str(type(c)) + "\n")

print("Creating Citizen objects, p1, p2...")
p1 = cuds.classes.Citizen(name="Peter")
p2 = cuds.classes.Citizen(name="Anne")

print("\nAdding p1 to c...")
c.add(p1, rel=cuds.classes.HasInhabitant)
print("internal dict of c:", super(cuds.classes.Cuds, c).__str__() + "\n")

print("Adding p2 to c...")
c.add(p2, rel=cuds.classes.HasInhabitant)
print("internal dict of c:", super(cuds.classes.Cuds, c).__str__() + "\n")

print("\nElements in c:")
for el in c.iter():
    print("  uid: " + str(el.uid))

print("\nGetting p1 from c:")
print(c.get(p1.uid))

print("\nGetting CUBA.CITIZEN from c:")
print(c.get(cuba_key=cuds.classes.CUBA.CITIZEN))

print("\n Remove p1:")
c.remove(p1.uid)
print("internal dict of c:", super(cuds.classes.Cuds, c).__str__() + "\n")

print("\nAdding Neighborhoods to Cuds object in a loop:")
for i in range(6):
    c.add(cuds.classes.Neighbourhood(
        name="Neighborhood %s" % i))
print("internal dict of c:", super(cuds.classes.Cuds, c).__str__() + "\n")
