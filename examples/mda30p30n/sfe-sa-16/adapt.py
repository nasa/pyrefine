#!/usr/bin/env python

from pyrefine import AdaptationDriver
from pyrefine.simulation import SimulationFun3dSFE
from pbs4py import PBS


project = "mda30p30n"
pbs = PBS.k4()
pbs.mpiexec = 'mpiexec_mpt'

adapt_driver = AdaptationDriver(project, pbs)
adapt_driver.refine.extrude_2d_mesh_to_3d = True
adapt_driver.simulation = SimulationFun3dSFE(project, pbs, omp_threads=4)
adapt_driver.simulation.import_solution_from_previous_mesh = False
adapt_driver.set_iterations(1, 10)

adapt_driver.run()
