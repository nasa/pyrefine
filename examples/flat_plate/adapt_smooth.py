#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.controller import ControllerSmoothTransition
from pyrefine.refine import RefineGoalOriented
from pyrefine.simulation import SimulationFun3dSFEAdjoint
from pbs4py import PBS

project = "numerics_flat_plate"
pbs = PBS.k3a()
pbs.time = 24
pbs.mpiexec = 'mpiexec_mpt'

adapt_driver = AdaptationDriver(project, pbs)
adapt_driver.simulation = SimulationFun3dSFEAdjoint(project)
#adapt_driver.simulation = SimulationFun3dSFEAdjoint(project, fwd_omp_threads=1, adj_omp_threads=20)

smooth_controller = ControllerSmoothTransition(project, pbs=None)
smooth_controller.initial_complexity = 2500
smooth_controller.steps_per_complexity = 1
smooth_controller.complexity_multiplier = 2.0
smooth_controller.steps_per_transition = 7
smooth_controller.save_all = True
adapt_driver.controller = smooth_controller

adapt_driver.refine = RefineGoalOriented(project)
mach = 0.8
reynolds_number = 73.0
temperature = 273.0
adapt_driver.refine.set_metric_form_cons_visc(mach, reynolds_number, temperature)
adapt_driver.refine.gradation = -1
adapt_driver.refine.use_kexact = True

adapt_driver.set_iterations(1, 20)
adapt_driver.run()
