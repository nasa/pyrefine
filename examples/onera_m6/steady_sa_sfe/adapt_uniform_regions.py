#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.simulation import SimulationFun3dSFE
from pyrefine.refine import UniformBox, UniformCylinder
from pbs4py import PBS

project = "om6ste"
pbs = PBS.k3()
pbs.profile_filename = "~/refine_test_modules_non_AVX.sh"
pbs.time = 4

adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.simulation = SimulationFun3dSFE(project)

box = UniformBox()
box.set_box_bounds(-0.1, 0.0, -0.1, 1.5, 0.5, 0.1)
box.limit = "floor"
box.h0 = 0.1
box.decay_distance = 0.1

cyl = UniformCylinder()
cyl.set_base(0.0, 1.4, 0.0, 0.1)
cyl.set_top(4.0, 1.4, 0.0, 0.2)
cyl.limit = "ceil"
cyl.h0 = 0.05
cyl.decay_distance = -0.01

adapt_driver.refine.uniform_regions = [box, cyl]

adapt_driver.set_iterations(1, 10)

adapt_driver.run()
