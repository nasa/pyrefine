#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS

pbs = PBS.k4(time=4)
adapt_driver = AdaptationDriver('om6ste', pbs=pbs)
adapt_driver.set_iterations(16, 30)
adapt_driver.run()
