from cuds.classes.generated import *


# Creating a Cuds object
c = Cuds("test CUDS")

boundary_a = ComputationalBoundary(name="ComputationalBoundary a")
boundary_b = ComputationalBoundary(name="ComputationalBoundary b")

# Add
c.add(boundary_a, boundary_b)

# Add in a loop
for i in range(6):
    c.add(ComputationalBoundary(name="Computational Boundary number {}".format(i)))

# Iterate
for el in c.iter():
    print("  uid: " + str(el.uid))

# Get by uid
get_boundary_a = c.get(boundary_a.uid)

# Getting by CUBA key
all_boundaries = c.get(CUBA.COMPUTATIONAL_BOUNDARY)

# Remove
c.remove(boundary_a.uid)
