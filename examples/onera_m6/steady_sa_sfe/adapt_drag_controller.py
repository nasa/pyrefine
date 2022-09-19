#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.simulation import SimulationFun3dSFE
from pyrefine.controller import ControllerMonitorForcesSFE
from pbs4py import PBS

project = "om6ste"
pbs = PBS.k3a()
pbs.profile_filename = "~/.bashrc_adapt"
pbs.time = 4

adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.simulation = SimulationFun3dSFE(project)
adapt_driver.controller = ControllerMonitorForcesSFE(project)
adapt_driver.set_iterations(1, 20)

adapt_driver.run()
