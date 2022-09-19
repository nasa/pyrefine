import os
import f90nml
import numpy as np
import scipy.linalg as linalg

from pyrefine.simulation import SimulationFun3dSFE
from pk_flutter_solver import read_files, PK


class SimulationNaca64a010Flutter(SimulationFun3dSFE):
    def __init__(self, project_name, pbs=None, omp_threads=None, u_ref=600):
        """
        Runs fun3d SFE and LFD and pk analysis for the Isogai airfoil problem.
        Uses a fixed reduced frequency list and adaptively selects more
        frequencies based on the zero damping points of the previous mesh.

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        omp_threads: int
            Number of OpenMP threads per mpi process to run if doing hybrid
            parallelism. If not doing hybrid parallelism, this optional argument
            should be left as None.
        u_ref: float
            Reference velocity for computing reduced frequencies in LFD
        """
        external_wall_distance = False
        super().__init__(project_name, pbs, external_wall_distance, omp_threads)

        self.sfe_cfg_lfd = 'sfe.cfg.lfd'
        self.fun3d_nml_lfd = 'fun3d.nml.lfd'

        self.expect_moving_body_input = True

        # standard atmosphere
        self.rho_ref = 1.225
        self.u_ref = u_ref

        # Isogai structural properties
        self.b = 0.5
        self.omega_alpha = 100.0    # pitch mode natural frequency
        self.mu = 60.0     # mass ratio
        self.vec1, self.vec2 = self._structural_eigen_decomposition(self.rho_ref, self.b)

        # pk parameters
        self.rho = np.linspace(self.rho_ref-1e-4, self.rho_ref+1e-4)
        self.vel = np.linspace(0.4 * u_ref, 10.0 * u_ref)
        self.k = np.array([0.01, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0])

        n = 200
        self.vf = np.zeros((n, 4))
        self.vf[:, 0] = np.arange(1, n+1)
        self.k_hist = np.zeros((n, 4))
        self.k_hist[:, 0] = np.arange(1, n+1)

    def get_expected_file_list(self):
        expected_files = super().get_expected_file_list()
        expected_files.extend([self.sfe_cfg_lfd, self.fun3d_nml_lfd])
        return expected_files

    def run(self, istep):
        self._run_steady(istep)
        self._write_mode_shape_files(istep)
        k = self._chose_k(istep)
        self._run_lfd(istep, k)
        self._run_pk(istep, k)
        self._save_outputs(istep)

    def _chose_k(self, istep):
        half_span = 0.0125
        k = self.k
        critical_pts = []
        if istep > 1:
            for i in range(1, 4):
                val = self.k_hist[istep-2, i]
                if val > 1e-4:
                    critical_pts.append(val)
        for pt in critical_pts:
            k = np.hstack((k, np.linspace(pt-half_span, pt+half_span, 7)))
        k.sort()
        return k

    def _run_steady(self, istep):
        print('Running the steady simulation')

        job_name = f'flow{istep:02d}'
        project = self._create_project_rootname(istep)

        # create namelist for this simulation
        nml = f90nml.read(f'../{self.fun3d_nml}')
        nml['project']['project_rootname'] = project
        if istep > 1 and self.import_solution_from_previous_mesh:
            nml['flow_initialization']['import_from'] = f'{project}-restart.solb'

        self._set_openmp_inputs_in_nml(nml, self.omp_threads)
        os.system(f'cp ../{self.sfe_cfg} sfe.cfg')

        nml.write('fun3d.nml', force=True)

        self._save_a_copy_of_solver_inputs(istep, 'steady')

        # set up the nodet command and launch it
        command = (f'nodet_mpi --write_massoud_file {self.fun3d_command_line_args}')

        command_list = [self.pbs.create_mpi_command(command, job_name, self.omp_threads)]
        self.pbs.launch(job_name, command_list)

        expected_file = f'{project}_volume.solb'
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(f'Expected file: {expected_file} was not found. Something failed with flow solver.')

    def _write_mode_shape_files(self, istep):
        project = f'{self.project_name}{istep:02d}'
        filename = f'{project}_massoud_body1.dat'
        self.generate_mode_shape_file(1, filename, self.mode_func, self.vec1)
        self.generate_mode_shape_file(2, filename, self.mode_func, self.vec2)

    def _run_lfd(self, istep, k):
        print('Running the lfd simulation')

        job_name = f'lfd{istep:02d}'
        project = self._create_project_rootname(istep)

        nml = f90nml.read(f'../{self.fun3d_nml_lfd}')
        nml['project']['project_rootname'] = project
        nml['code_run_control']['steps'] = k.size * 2

        self.current_sfe_cfg_file = self.sfe_cfg_lfd
        self._set_openmp_inputs_in_nml(nml, self.omp_threads)

        nml.write('fun3d.nml', force=True)

        self._write_moving_body_input(k)
        os.system(f'cp ../{self.sfe_cfg_lfd} sfe.cfg')

        self._save_a_copy_of_solver_inputs(istep, job_name='lfd')

        command = (f'complex_nodet_mpi --aeroelastic_internal {self.fun3d_command_line_args}')
        command_list = [self.pbs.create_mpi_command(command, job_name, self.omp_threads)]
        self.pbs.launch(job_name, command_list)

        expected_file = f'{project}_gafs.dat'
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(f'Expected file: {expected_file} was not found. Something failed with flow solver.')

    def _write_moving_body_input(self, k):
        moving_body = f90nml.read(f'../{self.moving_body_input}')

        moving_body['aeroelastic_modal_data']['uinf'] = self.u_ref
        moving_body['aeroelastic_modal_data']['qinf'] = 0.5 * self.rho_ref * self.u_ref**2.0

        omega = k * self.u_ref / self.b
        moving_body['aeroelastic_modal_data']['lfd_nfreq'] = omega.size
        moving_body['aeroelastic_modal_data']['lfd_freq'] = omega.tolist()
        moving_body.write('moving_body.input', force=True)

    def _run_pk(self, istep, k):
        project = self._create_project_rootname(istep)

        params = read_files()
        params.gaf_file = f'{project}_gafs.dat'
        params.read_moving_body()
        params.read_GAFs()

        # set parameters

        pk = PK()
        pk.set_input_density(self.rho)
        pk.set_input_velocity(self.vel)
        pk.set_reduced_frequencies(k)
        pk.set_reference_length(self.b)
        pk.set_GAFs(params.GAF)
        pk.set_reduced_stiffness(params.K)
        pk.set_reduced_mass(params.M)
        pk.set_reduced_damping(params.C)

        pk.solve()

        pk.find_flutter(most_critical_only=False)
        if pk.vel_flutter.size > 0:
            vf = pk.vel_flutter / (self.b * self.omega_alpha * np.sqrt(self.mu))
            print(f'Flutter speed index = {vf}, k = {pk.k_flutter}')
            self.vf[istep-1, 1] = vf[0]
            self.k_hist[istep-1, 1] = pk.k_flutter[0]
            if vf.size == 2:
                self.vf[istep-1, 3] = vf[1]
                self.k_hist[istep-1, 3] = pk.k_flutter[1]

        pk.find_stabilizing_points()
        if pk.vel_stabilizing_pt.size > 0:
            vf = pk.vel_stabilizing_pt / (self.b * self.omega_alpha * np.sqrt(self.mu))
            print(f'Stabilizing speed index = {vf}, k = {pk.k_stabilizing_pt}')
            self.vf[istep-1, 2] = vf
            self.k_hist[istep-1, 2] = pk.k_stabilizing_pt[0]
        np.savetxt('../flutter_vf_hist.dat', self.vf[:istep, :])
        np.savetxt('../flutter_k_hist.dat', self.k_hist[:istep, :])

    def _save_outputs(self, istep):
        output_dir = f'lfd{istep:02d}'
        os.system(f'mkdir -p {output_dir}')
        os.system(f'mv gafs.dat moving_body.input {output_dir}')

    def mode_func(self, x, y, z, vec, b):
        a = -2.0  # nondimensional elastic axis location measured from the midchord

        # mode 1 - plunge
        xmd = 0.0
        ymd = 0.0
        zmd = -vec[0]

        # mode 2 - linearized pitch about elastic axis
        zmd += vec[1] * (0.5 + a * b - x)
        return xmd, ymd, zmd

    def _structural_eigen_decomposition(self, rho, b):
        # Isogai properties
        unbal = 1.8   # static unbalance
        ra2 = 3.48    # r_a^2 square of radius of gyration
        wh = 100.0    # plunge mode natural frequency

        # Dimensional mass like terms (see kiviaho matrix pencil note 2019)
        m = self.mu * rho * np.pi * b**2.0
        Ia = ra2 * m * b**2.0
        Sa = unbal * m * b

        # Mass and Stiffness matrix
        M = np.zeros((2, 2))
        M[0, 0] = m
        M[0, 1] = Sa
        M[1, 0] = Sa
        M[1, 1] = Ia

        K = np.zeros((2, 2))
        K[0, 0] = m * wh**2.0
        K[1, 1] = Ia * self.omega_alpha**2.0

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
                    xmd, ymd, zmd = mode_shape_func(x, y, z, vec, self.b)
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
