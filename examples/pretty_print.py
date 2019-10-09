import cuds.classes
from cuds.utils import pretty_print


c = cuds.classes.Cuds("Main Cuds container")
pm = cuds.classes.PhysicsBasedModel()
pm.add(cuds.classes.PhysicsEquation())
pm.add(cuds.classes.InteratomicPotential())
mat = cuds.classes.Material("One material")
mat.add(cuds.classes.Mass("pg", 5))
mat.add(cuds.classes.Charge('',0.5))
c.add(mat)
pm.get(cuds.classes.CUBA.INTERATOMIC_POTENTIAL)[0].add(mat)
for i in range(3):
    c.add(cuds.classes.Atom())
box = cuds.classes.Box(name='SimulationBox')
box.add(cuds.classes.Condition("A condition"))
c.add(box)

pretty_print(c)
