from pyrefine import AdaptationDriver
from pyrefine.refine import RefineMultiscaleFixedPoint
from pbs4py import PBS

project = 'pacman'

pbs = PBS.k3(time=24)

driver = AdaptationDriver(project, pbs)

driver.controller.initial_complexity = 10000
driver.controller.steps_per_complexity = 5

driver.refine = RefineMultiscaleFixedPoint(project, pbs)
driver.refine.set_timestep_range_and_frequency(100, 8000, 10)
driver.refine.number_of_sweeps = 15
driver.refine.extrude_2d_mesh_to_3d = True
driver.refine.use_deforming = True

driver.simulation.external_wall_distance = False
driver.simulation.import_solution_from_previous_mesh = False
driver.simulation.expect_moving_body_input = True

driver.set_iterations(1, 10)
driver.run()
