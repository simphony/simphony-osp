from cuds.classes.generated import *
from cuds.utils import *

force_ds = ForceDataSpace("General Force DataSpace")
sim_ds = SimulationDataSpace("DataSpace for the simulation")
cuds = Cuds("Main Cuds container")
sim_ds.add(cuds)
force_ds.add(sim_ds)
pm = PhysicsBasedModel()
pm.add(PhysicsEquation())
pm.add(InteratomicPotential())
mat = Material("One material")
mat.add(Mass(5))
mat.add(Charge(0.5))
cuds.add(mat)
pm.get(CUBA.INTERATOMIC_POTENTIAL)[0].add(mat)
for i in range(3):
    cuds.add(Atom())
box = Box(name='SimulationBox')
box.add(Condition("A condition"))

pretty_print(force_ds)
