"""An example explaining the API of CUDS objects."""

# Please install the city ontology: $pico install city

from osp.core.namespaces import city

print("Creating a City object, c...")
c = city.City(name="Freiburg", coordinates=[47, 7])
print("Creating Citizen objects, p1, p2...")
p1 = city.Citizen(name="Peter")
p2 = city.Citizen(name="Anne")

# Functionalities exposed as Python properties.

print("Retrieving uid, IRIs and ontology classes...")

print("  uid of c: " + str(c.uid))
print("  uid of p1: " + str(p1.uid))
print("  uid of p2: " + str(p2.uid))

print("  IRI of c: " + str(c.iri))
print("  IRI of p1: " + str(p1.iri))
print("  IRI of p2: " + str(p2.iri))

print("  oclass of c: " + str(c.oclass))
print("  oclass of p1: " + str(p1.oclass))
print("  oclass of p2: " + str(p2.oclass))

print("Checking attributes of the CUDS objects...")
print(f"  Name of c: {c.name}. Coordinates of c: {c.coordinates}.")
print("  Name of p1: " + str(p1.name))
print("  Name of p2: " + str(p2.name))

print("\nChanging the attribute values of the CUDS objects...")
print(f"  Change the name of {p1.name}.")
p1.name = "Bob"
print(f"  Name of p1: {p1.name}.")

# Functionalities exposed as Python methods.

print("\nAdding p1 to c...")
c.add(p1, rel=city.hasInhabitant)

print("Adding p2 to c...")
c.add(p2, rel=city.hasInhabitant)

print("\nElements in c:")
for el in c.iter():
    print("  uid: " + str(el.uid))

print("\nGetting p1 from c:")
print(f"  {c.get(p1.uid)}")

print("\nGetting city.Citizen from c:")
print(f"  {c.get(oclass=city.Citizen)}")

print("\nRemove p1:")
c.remove(p1.uid)
print(f"  {c.get(oclass=city.Citizen)}")

print("\nAdding neighborhoods to Cuds object in a loop:")
for i in range(6):
    print("  Added neighborhood %s" % i)
    c.add(city.Neighborhood(
        name="neighborhood %s" % i))

print('\nTrying out the `is_a` method trivially with the city and the new '
      'neighborhoods.')
print("  Is the city an instance of `city.City` or of a subclass of it? %s" %
      c.is_a(city.City))
print("  Are all neighborhoods instances of `city.Neighborhood` or of a "
      "subclass of it? %s" %
      all(n.is_a(city.Neighborhood) for n in c.get(oclass=city.Neighborhood)))

# Functionalities exposed through subscripting.

print("\nAdd, get and remove cuds using subscripting. The object returned by "
      "the subscripting notation call behaves like a Python set, but has "
      "some additional capabilities.")

print(f"  {c[city.hasInhabitant].any().name}")
c[city.hasInhabitant] = p1
print(f"  {c[city.hasInhabitant].any().name}")
c[city.hasInhabitant] = None
print(f"  {c[city.hasInhabitant]}")
c[city.hasInhabitant] = p1
del c[city.hasInhabitant]
print(f"  {c[city.hasInhabitant]}")

print(f"  p1: {p1}")
print(f"  p2: {p2}")
c[city.hasInhabitant] = {p1, p2}
print(f"  {c[city.hasInhabitant]}")
c[city.hasInhabitant] -= p1
print(f"  {c[city.hasInhabitant]}")
c[city.hasInhabitant] += p1
print(f"  {c[city.hasInhabitant]}")
c[city.hasInhabitant] = {p2}
print(f"  {c[city.hasInhabitant]}")
c[city.hasInhabitant] ^= {p2}
print(f"  {c[city.hasInhabitant]}")
print(f"  {c[city.hasInhabitant] | {p1, p2}}")
print(f"  {c[city.hasInhabitant]}")

print("\nThe subscripting also works for attributes. In particular, it can be "
      "used to assign multiple values to the same attribute.")
c[city.name] = {'Freiburg', 'Freiburg im Breisgau'}
print(f"  {c[city.name]}")
print("  Be aware that when multiple values are assigned, the dot notation "
      "will raise an exception.")
c[city.name] += {'Stadt', 'City'}
print(f"  {c[city.name]}")
print(f"  {c[city.name].any()}")
# c.name -> Exception
c[city.name] -= {'Stadt', 'City', 'Freiburg'}
print(f"  {c[city.name]}")
