#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pbs4py import PBS

pbs = PBS.k4()
adapt_driver = AdaptationDriver('om6ste', pbs)
adapt_driver.refine.vertices_per_cpu_core = 10000

# override the target mesh size per CPU core for the GPU
adapt_driver.simulation.vertices_per_cpu_core = 1e6
adapt_driver.simulation.pbs = PBS.k5_a100()
adapt_driver.simulation.fun3d_command_line_args = '--mixed'

adapt_driver.controller.initial_complexity = 40000
adapt_driver.set_iterations(1, 40)
adapt_driver.run()
