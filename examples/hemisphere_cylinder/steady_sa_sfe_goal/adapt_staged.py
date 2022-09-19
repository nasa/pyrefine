#!/usr/bin/env python
import os
from pyrefine import AdaptationDriver
from pyrefine.controller import ControllerSmoothTransition
from pyrefine.refine import RefineGoalOriented
from pyrefine.simulation import SimulationFun3dSFE, SimulationFun3dSFEAdjoint
from pbs4py import PBS


project = 'hemisphere-cylinder'
pbs = PBS.k3a(time=24)
pbs.profile_filename = f'{os.getcwd()}/fun3d_intg_modules.sh'
pbs.mpiexec = 'mpiexec_mpt'

initial_complexity = 2000
steps_per_complexity = 5
complexity_multiplier = 2.0

# multiscale stage
adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.controller.initial_complexity = initial_complexity
adapt_driver.controller.steps_per_complexity = steps_per_complexity
adapt_driver.controller.complexity_multiplier = complexity_multiplier
adapt_driver.controller.save_all = True
adapt_driver.simulation = SimulationFun3dSFE(project, external_wall_distance=False)
adapt_driver.simulation.fun3d_nml = 'fun3d.nml_forward'
adapt_driver.simulation.sfe_cfg = 'sfe.cfg_forward'
adapt_driver.set_iterations(1, 10)
adapt_driver.run()

# goal oriented stage
adapt_driver = AdaptationDriver(project, pbs)
adapt_driver.refine = RefineGoalOriented(project)
adapt_driver.simulation = SimulationFun3dSFEAdjoint(project, fwd_omp_threads=1, adj_omp_threads=8,
                                                    external_wall_distance=False)

smooth_controller = ControllerSmoothTransition(project)
smooth_controller.initial_complexity = initial_complexity
smooth_controller.steps_per_complexity = 1
smooth_controller.complexity_multiplier = complexity_multiplier
smooth_controller.steps_per_transition = steps_per_complexity - smooth_controller.steps_per_complexity
adapt_driver.controller = smooth_controller

mach = 0.6
reynolds_number = 0.35e6
temperature = 300.0
adapt_driver.refine.set_metric_form_cons_visc(mach, reynolds_number, temperature)
adapt_driver.refine.gradation = -1
adapt_driver.controller.save_all = True
adapt_driver.set_iterations(11, 20)
adapt_driver.run()
