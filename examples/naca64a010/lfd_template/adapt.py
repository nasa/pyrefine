#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.controller import ControllerSmoothTransition
from simulation_naca64a010 import SimulationNaca64a010Flutter
from pbs4py import PBS

project = "naca64a010_"
u_ref = 387.2983346207417

pbs = PBS.k3(time=24)
pbs.profile_filename = "~/.bashrc_adapt"
pbs.mpiexec = 'mpiexec_mpt'

adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.refine.extrude_2d_mesh_to_3d = True
adapt_driver.simulation = SimulationNaca64a010Flutter(project, u_ref=u_ref, omp_threads=8, pbs=pbs)
adapt_driver.controller = ControllerSmoothTransition(project)
adapt_driver.controller.steps_per_transition = 4
adapt_driver.controller.save_all = True
adapt_driver.set_iterations(1, 65)
adapt_driver.vertices_per_cpu_core = 2500
adapt_driver.run()
