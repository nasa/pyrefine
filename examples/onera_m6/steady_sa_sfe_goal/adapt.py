from pyrefine import AdaptationDriver
from pyrefine.refine import RefineGoalOriented
from pyrefine.simulation import SimulationFun3dSFEAdjoint
from pbs4py import PBS

project = "om6ste"

pbs = PBS.k4(time=4)
pbs.mpiexec = 'mpiexec_mpt'

adapt_driver = AdaptationDriver(project, pbs)
adapt_driver.refine = RefineGoalOriented(project)
adapt_driver.refine.mask_strong_bc = True
adapt_driver.simulation = SimulationFun3dSFEAdjoint(project, fwd_omp_threads=2, adj_omp_threads=20)
adapt_driver.controller.save_all = True

adapt_driver.set_iterations(1, 5)
adapt_driver.run()
