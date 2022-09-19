#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.refine import RefineMultiscaleFixedPoint
from pbs4py import PBS

from naca64a010_time_domain import SimulationNaca64a010TimeDomainFlutter
from naca64a010_time_domain import ControllerNaca64a010TimeDomainFlutter
from naca64a010_time_domain import NacaData

project = "naca64a010_"
naca_data = NacaData()
naca_data.perturb_size = 1e-2
naca_data.vf = 1.15
vf_min = 1.0
vf_max = 1.5

start = 1

pbs = PBS.k3(time=24)
pbs.profile_filename = "~/.bashrc_adapt"
pbs.mpiexec = 'mpiexec_mpt'

adapt_driver = AdaptationDriver(project, pbs=pbs)

refine = RefineMultiscaleFixedPoint(project)
refine.extrude_2d_mesh_to_3d = True
refine.set_timestep_range_and_frequency(1000, 3000, 25)
adapt_driver.refine = refine

adapt_driver.simulation = SimulationNaca64a010TimeDomainFlutter(project, naca_data)
adapt_driver.controller = ControllerNaca64a010TimeDomainFlutter(project, naca_data,
                                                                vf_min=vf_min, vf_max=vf_max,
                                                                start=start)
adapt_driver.controller.save_all = True

adapt_driver.set_iterations(start, 60)
adapt_driver.run()
