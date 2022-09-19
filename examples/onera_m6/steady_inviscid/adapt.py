#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS

pbs = PBS.k4(time=4)

adapt_driver = AdaptationDriver('om6ste', pbs)
adapt_driver.simulation.external_wall_distance = False
adapt_driver.set_iterations(1, 25)
adapt_driver.run()
