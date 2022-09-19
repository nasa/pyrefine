#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS

nas_pbs = PBS.nas(group_list='a1727')
adapt_driver = AdaptationDriver('om6ste', pbs=nas_pbs)
adapt_driver.set_iterations(1, 15)
adapt_driver.run()
