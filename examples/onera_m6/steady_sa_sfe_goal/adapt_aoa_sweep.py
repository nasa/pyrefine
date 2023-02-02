#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.refine import RefineGoalOriented
from pyrefine.simulation import SimulationFun3dSFEAdjoint
from pyrefine.controller import ControllerAoaSweep
from pbs4py import PBS

project = "om6ste"

pbs = PBS.k4()
pbs.profile_filename = "~/.bashrc_adapt"
pbs.time = 4
pbs.mpiexec = 'mpiexec_mpt'

driver = AdaptationDriver(project, pbs=pbs)
driver.simulation = SimulationFun3dSFEAdjoint(project, fwd_omp_threads=2, adj_omp_threads=20)

driver.refine = RefineGoalOriented(project)
mach = 0.84
reynolds = 14.6e6
temp = 273.0
driver.refine.set_metric_form_cons_visc(mach, reynolds, temp)
driver.refine.mask_strong_bc = True


driver.controller = ControllerAoaSweep(project, pbs)
driver.controller.fun3d_nml_list = ['fun3d.nml_forward', 'fun3d.nml_adjoint']
driver.controller.initial_aoa = 1.0
driver.controller.steps_per_aoa_transition = 4
driver.controller.aoa_step_size = 1.0
driver.controller.complexity_levels_per_aoa = 2
driver.controller.steps_per_complexity_at_aoa = 5
driver.controller.save_all = True

driver.set_iterations(1, 25)
driver.run()
