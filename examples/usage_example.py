import cuds.classes


# Creating a Cuds object
c = cuds.classes.Cuds("test CUDS")

boundary_a = cuds.classes.ComputationalBoundary(name="ComputationalBoundary a")
boundary_b = cuds.classes.ComputationalBoundary(name="ComputationalBoundary b")

# Add
c.add(boundary_a, boundary_b)

# Add in a loop
for i in range(6):
    c.add(cuds.classes.ComputationalBoundary(
        name="Comp_Boundary number {}".format(i)))

# Iterate
for el in c.iter():
    print("  uid: " + str(el.uid))

# Get by uid
get_boundary_a = c.get(boundary_a.uid)

# Getting by CUBA key
all_boundaries = c.get(cuds.classes.CUBA.COMPUTATIONAL_BOUNDARY)

# Remove
c.remove(boundary_a.uid)
