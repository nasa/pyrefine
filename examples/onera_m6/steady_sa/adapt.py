#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS

adapt_driver = AdaptationDriver('om6ste', pbs=PBS.k4(time=4))
adapt_driver.set_iterations(1, 15)
adapt_driver.run()
