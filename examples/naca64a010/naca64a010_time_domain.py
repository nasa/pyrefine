import f90nml
import numpy as np
import scipy.linalg as linalg

from pyrefine.controller import ControllerBase
from pyrefine.simulation import SimulationFlutterFV
from damping_calculator import MatrixPencil


# Isogai structural properties
semichord = 0.5      # [m]
elastic_axis = -2.0  # nondimensional elastic axis location measured from the midchord
omega_alpha = 100.0  # pitch mode natural frequency
omega_h = 100.0      # plunge mode natural frequency
unbal = 1.8          # static unbalance
ra2 = 3.48           # r_a^2 square of radius of gyration
mu = 60.0            # mass ratio

# standard atmosphere
rho_ref = 1.225


class NacaData:
    def __init__(self):
        self.derivative_value = 1.0
        self.derivative_step = False
        self.vf = 1.0
        self.damping = 1.0
        self.perturb_size = 1e-2


class ControllerNaca64a010TimeDomainFlutter(ControllerBase):
    def __init__(self, project_name, naca_data: NacaData, vf_min=0.0, vf_max=1e99, pbs=None, start=1):
        super().__init__(project_name, pbs=pbs)
        self.naca_data = naca_data
        self.release_step = 1

        self.steps_per_complexity = 5
        self.complexity_multiplier = 2.0

        self.vf_min = vf_min
        self.vf_max = vf_max
        if start > 1:
            data = np.loadtxt('damping_hist.dat')
            self.naca_data.vf = data[-1, 2]

    def compute_complexity(self, istep, current_complexity):
        return self.initial_complexity * self.complexity_multiplier**((istep-1)//self.steps_per_complexity)

    def update_inputs(self, istep):
        self.naca_data.vf = self._compute_speed_index(istep, self.naca_data.vf,
                                                      self.naca_data.damping,
                                                      self.naca_data.derivative_value)
        print(f'Controller: Vf = {self.naca_data.vf}')

        self.naca_data.derivative_step = True if self._perturb_step(istep) else False

    def _compute_speed_index(self, istep, vf, damping, derivative):
        if self._first_step_at_complexity(istep) and istep > self.release_step:
            return self._update_speed_index(vf, damping, derivative)
        else:
            return vf

    def _first_step_at_complexity(self, istep):
        return istep % self.steps_per_complexity == 1

    def _perturb_step(self, istep):
        return istep % self.steps_per_complexity == 0

    def _update_speed_index(self, vf, damping, derivative):
        """ Newton step """
        return np.min((np.max((vf - damping / derivative, self.vf_min)), self.vf_max))


class SimulationNaca64a010TimeDomainFlutter(SimulationFlutterFV):
    def __init__(self, project_name, naca_data: NacaData, pbs=None):
        external_wall_distance = False

        self.naca_data = naca_data
        self.vec1, self.vec2 = self._structural_eigen_decomposition(rho_ref, semichord)
        super().__init__(project_name, pbs, external_wall_distance)

    def get_expected_file_list(self):
        first_mesh_file = f'{self.project_name}01.meshb'
        first_mapbc_file = f'{self.project_name}01.mapbc'
        expected_files = [self.fun3d_nml_fixed,
                          self.fun3d_nml_dynamic,
                          self.moving_body_input_dynamic,
                          first_mesh_file,
                          first_mapbc_file]
        return expected_files

    def run(self, istep):
        print('Running the fixed flow simulation')
        self.expect_moving_body_input = False
        self._run_fun3d_simulation(istep, job_name='fixed')

        self._write_mode_shape_files(istep)
        self._write_moving_body_input(self.naca_data.vf)

        print('Running the dynamic aeroelastic simulation')
        self.expect_moving_body_input = True
        self._run_fun3d_simulation(istep, job_name='dynamic', skip_external_distance=True)

        self._compute_damping(istep)
        self._move_aehist_to_keep(istep)
        if self.naca_data.derivative_step:
            self._write_moving_body_input(self.naca_data.vf + self.naca_data.perturb_size)
            self._run_fun3d_simulation(istep, job_name='perturb', skip_external_distance=True)
            self._compute_damping(istep, perturb_step=True)

    def _get_template_fun3d_nml_filename(self, job_name):
        if job_name == 'fixed':
            nml_file = self.fun3d_nml_fixed
        else:
            nml_file = self.fun3d_nml_dynamic
        return f'../{nml_file}'

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        if job_name in ['static', 'dynamic', 'perturb']:
            import_from = False
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)

    def _write_moving_body_input(self, vf):
        uinf = vf * semichord * omega_alpha * np.sqrt(mu)
        qinf = 0.5 * rho_ref * uinf ** 2.0

        moving_body = f90nml.read(f'../{self.moving_body_input_dynamic}')
        moving_body['aeroelastic_modal_data']['uinf'] = uinf
        moving_body['aeroelastic_modal_data']['qinf'] = qinf
        moving_body.write(f'../{self.moving_body_input_dynamic}', force=True)

    def _compute_damping(self, istep, perturb_step=False):
        start = 1000
        aehist = np.loadtxt(f'aehist_body1_mode1.dat', skiprows=3)
        t = aehist[start:, 0]
        x = aehist[start:, 1]
        mp = MatrixPencil(N=400, output_level=1)
        damp, freq = mp.compute(t, x)
        print('damp', damp)
        print('freq', freq)
        min_damp = np.min(damp[np.argwhere(np.abs(freq) > 1e-5)])

        if perturb_step:
            self.naca_data.derivative_value = (min_damp - self.naca_data.damping) / self.naca_data.perturb_size
        else:
            self.naca_data.damping = min_damp
            data = np.array([istep, min_damp, self.naca_data.vf]).reshape((-1, 3))
            if istep == 1:
                np.savetxt('../damping_hist.dat', data)
            else:
                hist = np.loadtxt('../damping_hist.dat')
                np.savetxt('../damping_hist.dat', np.vstack((hist, data)))

    def _write_mode_shape_files(self, istep):
        project = f'{self.project_name}{istep:02d}'
        filename = f'{project}_massoud_body1.dat'
        self.generate_mode_shape_file(1, filename, self.mode_func, self.vec1)
        self.generate_mode_shape_file(2, filename, self.mode_func, self.vec2)

    def mode_func(self, x, y, z, vec, b):

        # mode 1 - plunge
        xmd = 0.0
        ymd = 0.0
        zmd = -vec[0]

        # mode 2 - linearized pitch about elastic axis
        zmd += vec[1] * (0.5 + elastic_axis * b - x)
        return xmd, ymd, zmd

    def _structural_eigen_decomposition(self, rho, b):

        # Dimensional mass like terms (see kiviaho matrix pencil note 2019)
        m = mu * rho * np.pi * b**2.0
        Ia = ra2 * m * b**2.0
        Sa = unbal * m * b

        # Mass and Stiffness matrix
        M = np.zeros((2, 2))
        M[0, 0] = m
        M[0, 1] = Sa
        M[1, 0] = Sa
        M[1, 1] = Ia

        K = np.zeros((2, 2))
        K[0, 0] = m * omega_h**2.0
        K[1, 1] = Ia * omega_alpha**2.0

        lam, vec = linalg.eig(K, M)

        # scale the eigenvectors to get unit modal mass
        mass = np.zeros(2)
        stiff = np.zeros(2)
        for i in range(2):
            mass[i] = M.dot(vec[:, i]).dot(vec[:, i])
            vec[:, i] /= np.sqrt(mass[i])
        for i in range(2):
            mass[i] = M.dot(vec[:, i]).dot(vec[:, i])
            stiff[i] = K.dot(vec[:, i]).dot(vec[:, i])

        for i in range(2):
            print(
                'Structural Decomposition: mode=', i, 'freq=', np.sqrt(lam[i]),
                'shape=', vec[:, i],
                'mass=', mass[i],
                'stiff=', stiff[i],
                'freq2=', np.sqrt(stiff[i]))

        return vec[:, 0], vec[:, 1]

    def generate_mode_shape_file(self, mode_num, filename, mode_shape_func, vec):
        mode_file = filename.split('_massoud')[0] + '_body1_mode' + str(int(mode_num)) + '.dat'
        fh = open(filename)
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
                    xmd, ymd, zmd = mode_shape_func(x, y, z, vec, semichord)
                    line2 = " %0.9e, %0.9e, %0.9e, %d, %0.9e, %0.9e, %0.9e\n" % (x, y, z, id, xmd, ymd, zmd)
                    lines.append(line2)

                for elem in range(elems):
                    line = fh.readline()
                    lines.append(line)

            if not line:
                break

        fh2.writelines(lines)
        fh2.close()
        fh.close()
