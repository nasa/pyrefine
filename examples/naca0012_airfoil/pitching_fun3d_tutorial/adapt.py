from pyrefine import AdaptationDriver
from pyrefine.refine import RefineMultiscaleFixedPoint
from pbs4py import PBS
from pyrefine.shell_utils import cp

start = 1
end = 50
deforming = False

pbs = PBS.k3()
pbs.time = 12
pbs.profile_filename = '~/.bashrc_adapt'

project = 'naca0012_'

run_type = 'deforming' if deforming else 'rigid'
for file in ['fun3d.nml', 'moving_body.input']:
    cp(f'{file}.{run_type}', file)

driver = AdaptationDriver(project, pbs)

driver.refine = RefineMultiscaleFixedPoint(project, pbs)
driver.refine.set_timestep_range_and_frequency(1000, 2000, 50)
driver.refine.extrude_2d_mesh_to_3d = True
driver.refine.use_deforming = deforming

driver.controller.initial_complexity = 1000
driver.controller.steps_per_complexity = 5
driver.controller.save_all = True

driver.simulation.expect_moving_body_input = True

driver.set_iterations(start, end)
driver.run()
