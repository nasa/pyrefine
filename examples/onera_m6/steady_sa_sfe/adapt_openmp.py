#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.simulation import SimulationFun3dSFE
from pbs4py import PBS

project = "om6ste"
pbs = PBS.k4()
pbs.profile_filename = "~/refine_allmpi.sh"
pbs.time = 4
pbs.mpiexec = 'mpiexec_mpt'

adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.simulation = SimulationFun3dSFE(project, pbs, omp_threads=4)
adapt_driver.set_iterations(1, 5)
adapt_driver.run()
