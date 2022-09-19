#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.controller import ControllerMonitorForcesFUN3D
from pbs4py import PBS

project = 'om6ste'
pbs = PBS.k4(time=4)
adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.controller = ControllerMonitorForcesFUN3D(project, pbs, monitor_cd=True)

adapt_driver.set_iterations(1, 25)
adapt_driver.run()
