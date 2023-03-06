#!/usr/bin/env python
from pyrefine import AdaptationDriver
from pyrefine.simulation import SimulationFun3dSFE
from pyrefine.refine import TinfinityMultiscale
from pbs4py import PBS

project = "om6ste"

pbs = PBS.k4()
pbs.profile_filename = "~/.bashrc"
pbs.time = 4

adapt_driver = AdaptationDriver(project, pbs=pbs)

adapt_driver.simulation = SimulationFun3dSFE(project)

adapt_driver.refine = TinfinityMultiscale(project, field_file_extensions=['_sample1.solb', '_sample2.solb'])

adapt_driver.controller.initial_complexity = 10000.0
adapt_driver.set_iterations(1, 10)

adapt_driver.run()
