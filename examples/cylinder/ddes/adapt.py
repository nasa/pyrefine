#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.refine import RefineMultiscaleFixedPoint
from pbs4py import PBS
import f90nml

project = "cylinder"

# PBS scheduler
pbs = PBS.k4()
pbs.profile_filename = "~/.bashrc_adapt"
pbs.time = 72

# Refine setup
metric_timestep_window = [200, 1000]
metric_freq = f90nml.read('fun3d.nml')['sampling_parameters']['sampling_frequency'][0]
refine = RefineMultiscaleFixedPoint(project, pbs)
refine.set_timestep_range_and_frequency(metric_timestep_window[0], metric_timestep_window[1], metric_freq)

# Driver setup
adapt_driver = AdaptationDriver(project, pbs=pbs)
adapt_driver.refine = refine
adapt_driver.controller.initial_complexity = 6000
adapt_driver.set_iterations(1, 40)

adapt_driver.run()
