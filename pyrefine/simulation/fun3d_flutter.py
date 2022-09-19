import os
import f90nml

from .fun3d import SimulationFun3dFV
from pyrefine.shell_utils import mv, mkdir


class SimulationFlutterFV(SimulationFun3dFV):
    def __init__(self, project_name, pbs=None, external_wall_distance=True):
        """
        Base class to run the three standard phases of a fun3d flutter analysis:
        fixed mesh, static aeroelastic, and dynamic aeroelastic

        Designed for use with the fun3d internal mode solver.
        The _project_modes_shapes method need to be implemented for your problem
        in order to have mode shapes on the aerodynamic surface for each mesh.

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        external_wall_distance: bool
            Whether the wall distance needs to be computed by a stand alone wall
            distance calculator
        """
        super().__init__(project_name, pbs, external_wall_distance)

        self.fun3d_nml_fixed = 'fun3d.nml_fixed'
        self.fun3d_nml_static = 'fun3d.nml_static'
        self.fun3d_nml_dynamic = 'fun3d.nml_dynamic'

        self.moving_body_input_static = 'moving_body.input_static'
        self.moving_body_input_dynamic = 'moving_body.input_dynamic'

    def get_expected_file_list(self):
        project = self._create_project_rootname(1)
        first_mesh_file = f'{project}.meshb'
        first_mapbc_file = f'{project}.mapbc'
        expected_files = [self.fun3d_nml_fixed,
                          self.fun3d_nml_static,
                          self.fun3d_nml_dynamic,
                          self.moving_body_input_static,
                          self.moving_body_input_dynamic,
                          first_mesh_file,
                          first_mapbc_file]
        return expected_files

    def run(self, istep):
        """
        Prep the fun3d namelist and submit a job to run the flow solver
        """

        print('Running the fixed flow simulation')
        self.expect_moving_body_input = False
        self._run_fun3d_simulation(istep, job_name='fixed')

        self._project_mode_shapes(istep)

        print('Running the static aeroelastic simulation')
        self.expect_moving_body_input = True
        self._run_fun3d_simulation(istep, job_name='static', skip_external_distance=True)

        print('Running the dynamic aeroelastic simulation')
        self._run_fun3d_simulation(istep, job_name='dynamic', skip_external_distance=True)
        self._move_aehist_to_keep(istep)

    def _get_simulation_specific_fun3d_command_line_args_str(self, job_name):
        if job_name == 'fixed':
            return ' --write_massoud_file'
        else:
            return ' --aeroelastic_internal'

    def _get_template_fun3d_nml_filename(self, job_name):
        if job_name == 'fixed':
            nml_file = self.fun3d_nml_fixed
        elif job_name == 'static':
            nml_file = self.fun3d_nml_static
        else:
            nml_file = self.fun3d_nml_dynamic
        return f'../{nml_file}'

    def _get_template_moving_body_filename(self, job_name):
        if job_name == 'static':
            filename = self.moving_body_input_static
        else:
            filename = self.moving_body_input_dynamic
        return f'../{filename}'

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        if job_name in ['static', 'dynamic']:
            import_from = False
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)

    def _check_for_output_files(self, istep, job_name):
        if job_name == 'fixed':
            super()._check_for_output_files(istep, job_name)
        else:
            self._check_for_aeroelastic_hist_output()

    def _check_for_aeroelastic_hist_output(self):
        expected_file = 'aehist_body1_mode1.dat'
        if not os.path.exists(expected_file):
            raise FileNotFoundError(f'Expected file: {expected_file} was not found. Something failed with flow solver.')

    def _move_aehist_to_keep(self, istep):
        save_dir = f'{self._create_project_rootname(istep)}_hist'
        mkdir(save_dir)
        mv('aehist*', save_dir)

    def _project_mode_shapes(self, istep):
        raise NotImplementedError('Flutter simulations must implement projection of mode shapes')


class SimulationPapaFlutterFV(SimulationFlutterFV):
    def __init__(self, project_name, pbs):

        super(SimulationPapaFlutterFV, self).__init__(project_name, pbs)

        self.plunge_amplitude = 1.411425  # BSCW values
        self.pitch_amplitude = 0.173230375
        self.pitch_center = 8.0

    def _project_mode_shapes(self, istep):
        project = self._create_project_rootname(istep)
        massoud_file = f'{project}_massoud_body1.dat'

        for mode_num in range(1, 3):
            mode_file = f'{project}_body1_mode{mode_num}.dat'

            fh = open(massoud_file)
            fh2 = open(mode_file, mode='w')

            lines = []
            while True:
                line = fh.readline()
                if 'variables' in line.lower():
                    line = line[:-1] + ',"xmd","ymd","zmd"\n'
                lines.append(line)

                if 'zone' in line.lower():
                    nodes = int(line.split('=')[2].split(',')[0])
                    elems = int(line.split('=')[3].split(',')[0])

                    for node in range(nodes):
                        line = fh.readline()
                        x = float(line.split()[0])
                        y = float(line.split()[1])
                        z = float(line.split()[2])
                        id = int(line.split()[3])
                        xmd, ymd, zmd = self.papa_mode_func(x, mode_num,
                                                            self.plunge_amplitude,
                                                            self.pitch_amplitude, self.pitch_center)
                        line2 = " %0.9e, %0.9e, %0.9e, %d, %0.9e, %0.9e, %0.9e\n" % (x, y, z, id, xmd, ymd, zmd)
                        lines.append(line2)

                    for _ in range(elems):
                        line = fh.readline()
                        lines.append(line)

                if not line:
                    break

            fh2.writelines(lines)
            fh2.close()
            fh.close()

    def papa_mode_func(self, x, mode, z1, z2, x0):

        xmd = 0.0
        ymd = 0.0
        if mode == 1:
            zmd = z1
        else:
            zmd = z2 * (x-x0)
        return xmd, ymd, zmd
