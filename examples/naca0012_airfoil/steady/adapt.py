#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS

adapt_driver = AdaptationDriver('naca0012_', pbs=PBS.k3a(time=4))
adapt_driver.refine.extrude_2d_mesh_to_3d = True
adapt_driver.set_iterations(1, 30)
adapt_driver.run()
