import cuds.classes as cuds
from cuds.utils import pretty_print


c = cuds.Cuds("Main Cuds container")
pm = cuds.PhysicsBasedModel()
pm.add(cuds.PhysicsEquation())
pm.add(cuds.InteratomicPotential())
mat = cuds.Material("One material")
mat.add(cuds.Mass("pg", 5))
mat.add(cuds.Charge(0.5))
c.add(mat)
pm.get(cuds.CUBA.INTERATOMIC_POTENTIAL)[0].add(mat)
for i in range(3):
    c.add(cuds.Atom())
box = cuds.Box(name='SimulationBox')
box.add(cuds.Condition("A condition"))
c.add(box)

pretty_print(c)
