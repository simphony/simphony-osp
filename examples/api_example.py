import cuds.classes

"""
The objects without any other entities added are shown as
empty dictionaries '{}'. This is so because the uid, name and other
properties are stored elsewhere and not shown.

This example shows some options how to use the API
"""

print("Creating a Cuds object, c...")
c = cuds.classes.Cuds("test CUDS")
print("  uid of c: " + str(c.uid))
print("  type of c: " + str(type(c)) + "\n")

print("Creating a ComputationalBoundary object, d...")
d = cuds.classes.ComputationalBoundary(name="test ComputationalBoundary")
print("  uid of d: " + str(d.uid))
print("  type of d: " + str(type(d)) + "\n")

print("Creating another ComputationalBoundary object, e...")
e = cuds.classes.ComputationalBoundary(name="ComputationalBoundary e")

print("\nAdding d to c...")
c.add(d)
print("  c with d: " + str(c) + "\n")

print("Adding e to c...")
c.add(e)
print("  c with d and e: " + str(c) + "\n")

print("\nElements in c:")
for el in c.iter():
    print("  uid: " + str(el.uid))

print("\nGetting d from c:")
print(c.get(d.uid))

print("\nGetting CUBA.COMPUTATIONAL_BOUNDARY from c:")
print(c.get(cuds.classes.CUBA.COMPUTATIONAL_BOUNDARY))

c.remove(d.uid)
print("\nc without d: " + str(c))

print("\nAdding Computational Boundaries to Cuds object in a loop:")
for i in range(6):
    c.add(cuds.classes.ComputationalBoundary(
        name="Comp_Boundary number {}".format(i)))
