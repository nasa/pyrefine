import os
import f90nml
import numpy as np

from .fun3d import SimulationFun3dSFE
from pyrefine.shell_utils import rm, cp, mv, mkdir

try:
    from pyNastran.bdf.bdf import BDF
    from pyNastran.op2.op2 import OP2
    from scipy.spatial.distance import cdist
    from scipy.linalg import lu_factor, lu_solve
    from pk_flutter_solver.read_fun3d_files import read_files
    from pk_flutter_solver.pk_solver import PK
except:
    print('modules needed for SimulationFlutterLfd not found: code can only be used for unit testing')

class SimulationFlutterLfd(SimulationFun3dSFE):
    def __init__(self, project_name, pbs=None, external_wall_distance=True, omp_threads=None):
        """
        Runs a steady SFE analysis, followed by LFD, and then PK to find the
        flutter point.  A complex mach field is constructed based on PK results,
        and then unsteady mach snapshots are constructed, by emulating small oscillations
        about the steady mach field.

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        external_wall_distance: bool
            Whether the wall distance needs to be computed by a stand alone wall
            distance calculator
        omp_threads: int
            Number of OpenMP threads per mpi process to run if doing hybrid
            parallelism. If not doing hybrid parallelism, this optional argument
            should be left as None.
        """
        super().__init__(project_name, pbs, external_wall_distance, omp_threads)

        #: str: fun3d.nml file name used for LFD analysis in the root directory
        self.fun3d_nml_lfd = 'fun3d.nml_lfd'

        #: str: sfe.cfg file name used for LFD analysis in the root directory
        self.sfe_cfg_lfd = 'sfe.cfg_lfd'

        #: str: moving_body.input file name used for LFD analysis in the root directory
        self.moving_body_input_lfd = 'moving_body.input_lfd'

        #: str: flutter_terms.input file name used for flutter analysis in the root directory
        self.flutter_terms_input = 'flutter_terms.input'

        #: str: path to libMeshb for converting sol and solb files.
        self.libMeshb_path = ''

        #: int: the number of small-perturbation mach snapshots to create
        self.number_of_snapshots = 20

        #: float: the amplitude scaling of the unsteady Mach field about the steady field
        self.linear_perturbation = 0.01

    def get_expected_file_list(self):
        expected_files = super().get_expected_file_list()
        expected_files.append(self.fun3d_nml_lfd)
        expected_files.append(self.sfe_cfg_lfd)
        expected_files.append(self.moving_body_input_lfd)
        expected_files.append(self.flutter_terms_input)
        return expected_files

    def run(self, istep):
        print('Running the steady fun3d simulation')
        self.expect_moving_body_input = False
        self._run_fun3d_simulation(istep, 'steady')
        self._project_mode_shapes(istep)

        print('Running the LFD simulation')
        self.expect_moving_body_input = True
        self._run_fun3d_simulation(istep, 'lfd', skip_external_distance=True)
        self._check_for_lfd_output(istep)

        print('Running the PK flutter simulation')
        pk = self._run_pk_flutter_solver(istep)
        self._write_history(istep, pk)

        print('Constructing unsteady snapshots from the LFD solution')
        self._construct_unsteady_snapshots(istep, pk)

    def _get_template_fun3d_nml_filename(self, job_name):
        if job_name == 'lfd':
            nml_file = self.fun3d_nml_lfd
        else:
            nml_file = self.fun3d_nml
        return f'../{nml_file}'

    def _get_template_sfe_cfg_filename(self, job_name):
        if job_name == 'lfd':
            sfe_cfg = self.sfe_cfg_lfd
        else:
            sfe_cfg = self.sfe_cfg
        return f'../{sfe_cfg}'

    def _get_template_moving_body_filename(self, job_name):
        if job_name == 'lfd':
            filename = self.moving_body_input_lfd
        else:
            filename = self.moving_body_input
        return f'../{filename}'

    def _get_simulation_nodet(self, job_name):
        if job_name == 'lfd':
            return 'complex_nodet_mpi'
        else:
            return super()._get_simulation_nodet(job_name)

    def _get_simulation_specific_fun3d_command_line_args_str(self, job_name):
        if job_name == 'steady':
            return ' --write_massoud_file'
        else:
            return ' --aeroelastic_internal'

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        if job_name == 'lfd':
            import_from = False
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)

    def _project_mode_shapes(self, istep):
        raise NotImplementedError('LFD simulations must implement projection of mode shapes')

    def _check_for_lfd_output(self, istep):
        nml = f90nml.read(f'moving_body.input_lfd{istep:02d}')
        final_lfd_step = nml["aeroelastic_modal_data"]["nmode"][0] * nml["aeroelastic_modal_data"]["lfd_nfreq"]
        expected_file = f'{self._create_project_rootname(istep)}_lfd_{final_lfd_step}.solb'
        if not os.path.exists(expected_file):
            raise FileNotFoundError(f'Expected file: {expected_file} was not found. Something failed with LFD solver.')

    def _run_pk_flutter_solver(self, istep):
        # read parameters from files
        params = read_files()
        params.set_moving_body_file(self.moving_body_input)
        params.read_moving_body()
        params.read_flutter_terms()
        params.set_gaf_file(f'{self.project_name}{istep:02d}_gafs.dat')
        params.read_GAFs()

        # set parameters
        pk = PK()
        pk.rho_in = params.rho
        pk.vel_in = params.vel
        pk.k_sweep = params.k
        pk.b = params.b
        pk.GAF = params.GAF
        pk.K = params.K
        pk.M = params.M
        pk.C = params.C

        # compute flutter point
        pk.solve()
        try:
            pk.find_flutter()
            pk.rho_flutter = pk.rho_flutter[0]
            pk.vel_flutter = pk.vel_flutter[0]
            pk.omega_flutter = pk.omega_flutter[0]
            pk.R_flutter = pk.R_flutter[0, :]
        except:
            print("PK could not find a flutter point: reach back and use the values from the previous istep")
            pk.rho_flutter, pk.vel_flutter, pk.omega_flutter, pk.R_flutter = self._retrieve_old_PK_values(istep)

        return pk

    def _retrieve_old_PK_values(self, istep):
        raise NotImplementedError(
            'LFD simulations must implement a method to retrieve flutter solution from the previous istep')

    def _write_history(self, istep, PK_driver):
        raise NotImplementedError('LFD simulations must implement a method to write flutter data to a history file')

    def _construct_unsteady_snapshots(self, istep, pk):
        project = f'{self.project_name}{istep:02d}'

        # convert the steady .solb file into a .sol file
        self._convert_sol_and_solb(f'{project}_volume.solb', f'{project}_steady.sol')

        # Mach number and gamma, needed for Cp computations
        mach = f90nml.read(self.fun3d_nml)['reference_physical_properties']['mach_number']
        gamma = self._get_gamma(self.fun3d_command_line_args)

        # ID the LFD .solb outputs which participate in the flutter mode, and convert to .sol
        LFD_files, omega_LB, omega_UB = self._get_flutter_participation_ID(pk)
        for i in LFD_files:
            self._convert_sol_and_solb(f'{project}_lfd_{i}.solb', f'{project}_lfd_{i}.sol')

        # find the number of equations being solved (6: RANS, 5: Euler)
        n_eqs = self._get_number_of_equations()

        # verify that the steady volume output is in the correct format
        self._verify_steady_volume_format(istep, n_eqs)

        # read the steady and LFD .sol files to obtain the Mach and Cp fields
        M_0, M_lfd, Cp_0, Cp_lfd = self._read_sol_files(project, LFD_files, n_eqs, pk, omega_LB, omega_UB, gamma, mach)

        # create unsteady snapshots of time domain data
        self._compute_mach_snapshots(project, M_0, M_lfd)

        # convert .sol snapshots into .solb
        for i in range(self.number_of_snapshots):
            self._convert_sol_and_solb(f'{project}_volume_timestep{i+1}.sol', f'{project}_volume_timestep{i+1}.solb')

        # write a tecplot file with the surface deformation and Cp data
        self._write_surface_flutter_data(project, istep, pk, Cp_0, Cp_lfd)

        # delete lfd .solb and .sol output, and the volume_timestep.sol files
        extensions = ["_steady.sol", "_lfd_*.solb", "_lfd_*.sol", "_volume_timestep*.sol"]
        for ext in extensions:
            rm(f'{project}*{ext}')

    def _convert_sol_and_solb(self, file1, file2):
        os.system(f'{self.libMeshb_path}/build/utilities/transmesh {file1} {file2}')

    def _get_gamma(self, fun3d_command_line_args):
        args = fun3d_command_line_args.split()
        if args:
            index = [idx for idx, s in enumerate(args) if 'gamma' in s][0]
            gamma = float(args[index+1])
        else:
            gamma = 1.4
        return gamma

    def _get_flutter_participation_ID(self, pk):
        nml = f90nml.read(self.moving_body_input)
        lfd_freq = np.ndarray.flatten(np.asarray(nml['aeroelastic_modal_data']['lfd_freq']), 'F')

        i = np.where(lfd_freq > pk.omega_flutter)[0][0]
        omega_LB = lfd_freq[i-1]
        omega_UB = lfd_freq[i]

        N_modes = len(pk.K)
        LFD_files = np.arange(N_modes*(i-1)+1, (i+1)*N_modes+1)
        return LFD_files, omega_LB, omega_UB

    def _get_number_of_equations(self):
        nml = f90nml.read(self.fun3d_nml)
        if nml['governing_equations']['viscous_terms'] == 'inviscid':
            n_eqs = 5
        else:
            n_eqs = 6
        return n_eqs

    def _verify_steady_volume_format(self, istep, n_eqs):
        volume_data = f90nml.read(f'fun3d.nml_steady{istep:02d}')['volume_output_variables']
        if n_eqs == 5:
            desired = {'export_to': 'solb', 'primitive_variables': True, 'x': False, 'y': False, 'z': False}
        elif n_eqs == 6:
            desired = {'export_to': 'solb', 'primitive_variables': True,
                       'turb1': True, 'x': False, 'y': False, 'z': False}
        if volume_data != desired:
            raise ValueError('Steady volume data not in the correct format')

    def _read_sol_files(self, project, LFD_files, n_eqs, pk, omega_LB, omega_UB, gamma, mach):
        # open the LFD and steady .sol files
        data = []
        for i in (LFD_files):
            data.append(open(f'{project}_lfd_{i}.sol', 'r'))
        data.append(open(f'{project}_steady.sol', 'r'))

        # read the number of nodes, and step down to where the data starts
        for i in range(6):
            lines = [i.readline() for i in data]
        N_nodes = int(lines[0][0:-1])

        lines = [i.readline() for i in data]

        # loop over number of nodes, storing the steady and dynamic mach number, and the steady and dynamic Cp
        N_modes = len(pk.K)

        M_0 = np.zeros(N_nodes)
        M_lfd = np.zeros(N_nodes, dtype=complex)
        Cp_0 = np.zeros(N_nodes)
        Cp_lfd = np.zeros(N_nodes, dtype=complex)

        for i in range(N_nodes):
            lines = [i.readline() for i in data]

            # read the LFD data:
            #   RANS:  columns 0/1/2/3/4 are real rho/u/v/w/T, and 6/7/8/9/10 are imag rho/u/v/w/T
            #   Euler: columns 0/1/2/3/4 are real rho/u/v/w/T, and 5/6/7/8/9 are imag rho/u/v/w/T

            rho_lfd = np.zeros(len(LFD_files), dtype=complex)
            u_lfd = np.zeros(len(LFD_files), dtype=complex)
            v_lfd = np.zeros(len(LFD_files), dtype=complex)
            w_lfd = np.zeros(len(LFD_files), dtype=complex)
            T_lfd = np.zeros(len(LFD_files), dtype=complex)
            for j in range(len(LFD_files)):
                rho_lfd[j] = float(lines[j].split()[0]) + 1j*float(lines[j].split()[n_eqs])
                u_lfd[j] = float(lines[j].split()[1]) + 1j*float(lines[j].split()[n_eqs+1])
                v_lfd[j] = float(lines[j].split()[2]) + 1j*float(lines[j].split()[n_eqs+2])
                w_lfd[j] = float(lines[j].split()[3]) + 1j*float(lines[j].split()[n_eqs+3])
                T_lfd[j] = float(lines[j].split()[4]) + 1j*float(lines[j].split()[n_eqs+4])

            rho_lfd = np.reshape(rho_lfd, [2, N_modes])
            u_lfd = np.reshape(u_lfd, [2, N_modes])
            v_lfd = np.reshape(v_lfd, [2, N_modes])
            w_lfd = np.reshape(w_lfd, [2, N_modes])
            T_lfd = np.reshape(T_lfd, [2, N_modes])

            # interpolate to the frequency you care about
            rho_lfd = (rho_lfd[1, :] - rho_lfd[0, :])*((pk.omega_flutter-omega_LB)/(omega_UB-omega_LB)) + rho_lfd[0, :]
            u_lfd = (u_lfd[1, :] - u_lfd[0, :])*((pk.omega_flutter-omega_LB)/(omega_UB-omega_LB)) + u_lfd[0, :]
            v_lfd = (v_lfd[1, :] - v_lfd[0, :])*((pk.omega_flutter-omega_LB)/(omega_UB-omega_LB)) + v_lfd[0, :]
            w_lfd = (w_lfd[1, :] - w_lfd[0, :])*((pk.omega_flutter-omega_LB)/(omega_UB-omega_LB)) + w_lfd[0, :]
            T_lfd = (T_lfd[1, :] - T_lfd[0, :])*((pk.omega_flutter-omega_LB)/(omega_UB-omega_LB)) + T_lfd[0, :]

            # combine the modes based on the flutter eigenvector
            rho_lfd = np.inner(pk.R_flutter[0:N_modes], rho_lfd)
            u_lfd = np.inner(pk.R_flutter[0:N_modes], u_lfd)
            v_lfd = np.inner(pk.R_flutter[0:N_modes], v_lfd)
            w_lfd = np.inner(pk.R_flutter[0:N_modes], w_lfd)
            T_lfd = np.inner(pk.R_flutter[0:N_modes], T_lfd)

            # read the steady data: columns 0/1/2/3/4 are rho/u/v/w/p
            rho_0 = float(lines[-1].split()[0])
            u_0 = float(lines[-1].split()[1])
            v_0 = float(lines[-1].split()[2])
            w_0 = float(lines[-1].split()[3])
            p_0 = float(lines[-1].split()[4])

            # calculate the steady and the complex Mach number
            M_0[i] = np.sqrt(u_0**2 + v_0**2 + w_0**2)

            if M_0[i] == 0.:
                M_lfd[i] = 0.
            else:
                M_lfd[i] = (u_0*u_lfd + v_0*v_lfd + w_0*w_lfd)/M_0[i]

            # calculate the steady and the complex Cp
            Cp_0[i] = 2*(p_0 - 1/gamma)/mach/mach

            T_0 = gamma*p_0/rho_0
            p_lfd = (rho_0*T_lfd + T_0*rho_lfd)/gamma
            Cp_lfd[i] = 2*p_lfd/mach/mach

        for i in data:
            i.close()

        return M_0, M_lfd, Cp_0, Cp_lfd

    def _compute_mach_snapshots(self, project, M_0, M_lfd):
        N_nodes = len(M_0)
        data = []
        for i in range(self.number_of_snapshots):
            data.append(open("%s_volume_timestep%d.sol" % (project, i+1), "w"))

        # fill in the initial headers for each snapshot
        [i.writelines("MeshVersionFormatted 3\n") for i in data]
        [i.writelines("Dimension 3\n") for i in data]
        [i.writelines("SolAtVertices\n") for i in data]
        [i.writelines("%d\n" % N_nodes) for i in data]
        [i.writelines("1\n") for i in data]
        [i.writelines("1\n") for i in data]

        # loop over number of nodes
        t = 2*np.pi*np.arange(0, self.number_of_snapshots)/self.number_of_snapshots
        for i in range(N_nodes):
            mach = M_0[i] + self.linear_perturbation*np.imag(M_lfd[i]*np.exp(1j*t))
            for q in range(self.number_of_snapshots):
                data[q].writelines(("%0.15E\n" % mach[q]))

        # write end, and close
        [i.writelines("End") for i in data]
        for i in data:
            i.close()

    def _write_surface_flutter_data(self, project, istep, pk, Cp_0, Cp_lfd):
        # read in the mode shapes
        N_modes = len(pk.K)
        x, y, z, ID, dx, dy, dz, quad = self._read_mode_shapes(project, N_modes)

        # compute the steady deformation
        nml = f90nml.read(f'moving_body.input_lfd{istep:02d}')
        gdisp0 = nml['aeroelastic_modal_data']['gdisp0'][0]
        dx_0 = dx @ gdisp0
        dy_0 = dy @ gdisp0
        dz_0 = dz @ gdisp0

        # compute the unsteady deformation
        dx_lfd = dx @ pk.R_flutter[0:N_modes]
        dy_lfd = dy @ pk.R_flutter[0:N_modes]
        dz_lfd = dz @ pk.R_flutter[0:N_modes]

        # write a tecplot file with the surface deformation and Cp data
        Nn = len(x)
        Ne = len(quad)

        Cp_0 = Cp_0[ID-1]
        Cp_lfd = Cp_lfd[ID-1]

        surface_file = f'{project}_deformed_surface_pressures.dat'
        f = open(surface_file, mode='w')

        lines = []
        lines.append('title="surface data of wing deformation and Cp"\n')
        lines.append('variables="x_rigid","y_rigid","z_rigid","id","dx_0","dy_0","dz_0","dx_lfd_r","dx_lfd_i","dy_lfd_r","dy_lfd_i","dz_lfd_r","dz_lfd_i","Cp_0","Cp_lfd_r","Cp_lfd_i"\n')
        lines.append('zone t="mdo body 1", i=' + str(Nn) + ', j=' + str(Ne) +
                     ', f=fepoint,  solutiontime= 0.1000000E+01, strandid=0\n')
        for i in range(0, Nn):
            line = ' %0.15e, %0.15e, %0.15e, %d, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e, %0.9e\n' % \
                   (x[i], y[i], z[i], ID[i], dx_0[i], dy_0[i], dz_0[i],
                    np.real(dx_lfd[i]), np.imag(dx_lfd[i]), np.real(dy_lfd[i]), np.imag(dy_lfd[i]), np.real(dz_lfd[i]), np.imag(dz_lfd[i]), Cp_0[i], np.real(Cp_lfd[i]), np.imag(Cp_lfd[i]))
            lines.append(line)
        for i in range(0, Ne):
            line = ' %d, %d, %d, %d\n' % (quad[i, 0], quad[i, 1], quad[i, 2], quad[i, 3])
            lines.append(line)

        f.writelines(lines)
        f.close()

    def _read_mode_shapes(self, project, N_modes):
        mode_file = f'{project}_body1_mode1.dat'

        f = open(mode_file, "r")
        contents = f.read().split()
        f.close()

        Nn = int(contents[12][2:-1])
        Ne = int(contents[13][2:-1])

        x, y, z = np.zeros(Nn), np.zeros(Nn), np.zeros(Nn)
        ID = np.zeros(Nn, dtype=int)
        dx, dy, dz = np.zeros([Nn, N_modes]), np.zeros([Nn, N_modes]), np.zeros([Nn, N_modes])
        quad = np.zeros([Ne, 4], dtype=int)

        for i in range(0, N_modes):
            mode_file = f'{project}_body1_mode{i+1}.dat'
            f = open(mode_file, 'r')
            contents = f.read().split()
            f.close()

            for q in range(0, Nn):
                x[q] = float(contents[q*7+18][0:-1])
                y[q] = float(contents[q*7+19][0:-1])
                z[q] = float(contents[q*7+20][0:-1])
                ID[q] = int(contents[q*7+21][0:-1])
                dx[q, i] = float(contents[q*7+22][0:-1])
                dy[q, i] = float(contents[q*7+23][0:-1])
                dz[q, i] = float(contents[q*7+24])

            for q in range(0, Ne):
                quad[q, :] = np.asarray(contents[Nn*7+18+q*4:Nn*7+22+q*4]).astype(int)

        return x, y, z, ID, dx, dy, dz, quad


class SimulationPapaFlutterLfd(SimulationFlutterLfd):
    def __init__(self, project_name, pbs=None, external_wall_distance=True, omp_threads=None):
        """
        Runs a fun3d/SFE/LFD flutter analysis for PAPA (pitch and plunge) configurations

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        external_wall_distance: bool
            Whether the wall distance needs to be computed by a stand alone wall
            distance calculator
        omp_threads: int
            Number of OpenMP threads per mpi process to run if doing hybrid
            parallelism. If not doing hybrid parallelism, this optional argument
            should be left as None.
        """
        super().__init__(project_name, pbs, external_wall_distance, omp_threads)

        #: float: the amplitude of the plunge mode
        self.plunge_amp = 1.0

        #: float: the amplitude of the pitch mode
        self.pitch_amp = 1.0

        #: float: the x-coordinate of the pitch mode center of rotation
        self.pitch_center = 0.0

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        self._set_aoa(nml)
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)

    def _set_aoa(self, nml: f90nml.Namelist):
        if os.path.exists('aoa.txt'):
            f = open('aoa.txt', 'r')
            aoa = float(f.read().splitlines()[0])
            f.close()
            nml['reference_physical_properties']['angle_of_attack'] = aoa

    def _project_mode_shapes(self, istep):
        project = f'{self.project_name}{istep:02d}'
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
                        xmd, ymd, zmd = self.papa_mode_func(
                            x, y, z, mode_num, self.plunge_amp, self.pitch_amp, self.pitch_center)
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

    def papa_mode_func(self, x, y, z, mode, z1, z2, x0):
        xmd = 0.0
        ymd = 0.0
        if mode == 1:
            zmd = z1
        else:
            zmd = z2 * (x-x0)
        return xmd, ymd, zmd

    def _write_history(self, istep, pk):
        # read .out to find nnodes
        f = open(f'steady{istep:02d}.out', "r")
        contents = f.read().split()
        a = contents.index('nnodes')
        nnodes = int(contents[a+1])
        f.close()

        # read .nml file to find AoA
        nml = f90nml.read(f'fun3d.nml_steady{istep:02d}')
        AoA = nml['reference_physical_properties']['angle_of_attack']

        # if this is the first step, create the history file, and populate first line: otherwise, append to end
        if istep == 1:
            f = open('history.dat', 'w+')
            f.write('istep nnodes AoA rho_flutter vel_flutter omega_flutter R_flutter\n')
        else:
            f = open('history.dat', 'a')

        # write data, and close
        f.write(
            str(istep) + ' ' + str(nnodes) + ' ' + str(AoA) + ' ' + str(pk.rho_flutter) + ' ' +
            str(pk.vel_flutter) + ' ' + str(pk.omega_flutter) + ' ' + str(pk.R_flutter.tolist()) + '\n')
        f.close()

    def _retrieve_old_PK_values(self, istep):
        f = open('history.dat', 'r')
        contents = f.readlines()

        step = np.zeros(len(contents)-1, dtype=int)
        AoA = np.zeros(len(contents)-1, dtype=float)
        rho_flutter = np.zeros(len(contents)-1, dtype=float)
        vel_flutter = np.zeros(len(contents)-1, dtype=float)
        omega_flutter = np.zeros(len(contents)-1, dtype=float)
        R_flutter = np.zeros([len(contents)-1, 4], dtype=complex)

        for i in range(len(step)):
            line = contents[i+1].split()
            step[i] = int(line[0])
            AoA[i] = float(line[2])
            rho_flutter[i] = float(line[3])
            vel_flutter[i] = float(line[4])
            omega_flutter[i] = float(line[5])
            R_flutter[i, 0] = complex(line[6][2:-2])
            R_flutter[i, 1] = complex(line[7][1:-2])
            R_flutter[i, 2] = complex(line[8][1:-2])
            R_flutter[i, 3] = complex(line[9][1:-2])

        f.close()

        old = np.argwhere(step == istep-1)[0][0]
        rho_flutter = rho_flutter[old]
        vel_flutter = vel_flutter[old]
        omega_flutter = omega_flutter[old]
        R_flutter = R_flutter[old, :]

        return rho_flutter, vel_flutter, omega_flutter, R_flutter


class SimulationModalFlutterLfd(SimulationFlutterLfd):
    def __init__(self, project_name, pbs=None, external_wall_distance=True, omp_threads=None):
        """
        Runs a fun3d/SFE/LFD flutter analysis for a modal structural configuration

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        external_wall_distance: bool
            Whether the wall distance needs to be computed by a stand alone wall
            distance calculator
        omp_threads: int
            Number of OpenMP threads per mpi process to run if doing hybrid
            parallelism. If not doing hybrid parallelism, this optional argument
            should be left as None.
        """
        super().__init__(project_name, pbs, external_wall_distance, omp_threads)

        #: str: fun3d.nml file name used for massoud-output analysis in the root directory
        self.fun3d_nml_output_massoud = "fun3d.nml_output_massoud"

        #: str: BDF file name used for the nastran model
        self.bdf_file = 'model.bdf'

        #: str: OP2 file name used for the nastran output
        self.op2_file = 'model.op2'

        #: float: filter size used to downselect structural nodes for RBF interpolation
        #: filter = (Ymax-Ymin)/nodal_downselect_filter
        self.nodal_downselect_filter = 50.

        #: bool: specify whether the y = 0 plane is a symmetry plane, to be preserved during mode shape projection
        self.y_symmetry = True

        #: float: if y_symmetry is True, y-displacements of the CFD surface grid are
        #         gradually blended to 0 at y = 0, for y < (Ymax-Ymin)/y_symmetry_cutoff
        self.y_symmetry_cutoff = 50.

    def get_expected_file_list(self):
        expected_files = super().get_expected_file_list()
        expected_files.append(self.fun3d_nml_output_massoud)
        expected_files.append(self.bdf_file)
        expected_files.append(self.op2_file)
        return expected_files

    def run(self, istep):
        print('Running the steady fun3d simulation to output the massoud file')
        self.expect_moving_body_input = False
        self._run_fun3d_simulation(istep, 'output_massoud')
        self._project_mode_shapes(istep)

        print('Running the steady fun3d simulation')
        self.expect_moving_body_input = True
        self._run_fun3d_simulation(istep, 'steady')
        self._move_aehist(istep)

        print('Running the LFD simulation')
        self.expect_moving_body_input = True
        self._run_fun3d_simulation(istep, 'lfd', skip_external_distance=True)
        self._check_for_lfd_output(istep)

        print('Running the PK flutter simulation')
        pk = self._run_pk_flutter_solver(istep)
        self._write_history(istep, pk)

        print('Constructing unsteady snapshots from the LFD solution')
        self._construct_unsteady_snapshots(istep, pk)

    def _get_template_fun3d_nml_filename(self, job_name):
        if job_name == 'lfd':
            nml_file = self.fun3d_nml_lfd
        elif job_name == 'output_massoud':
            nml_file = self.fun3d_nml_output_massoud
        else:
            nml_file = self.fun3d_nml
        return f'../{nml_file}'

    def _get_simulation_specific_fun3d_command_line_args_str(self, job_name):
        if job_name == 'output_massoud':
            return ' --write_massoud_file'
        else:
            return ' --aeroelastic_internal'

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        if job_name == 'output_massoud':
            import_from = False
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)

    def _prepare_moving_body_input(self, istep: int, job_name: str):
        cp(self._get_template_moving_body_filename(job_name), 'moving_body.input')
        if job_name == 'steady':
            self._set_gdisp()

    def _set_gdisp(self):
        if os.path.exists('gdisp.txt'):
            pass
        # todo: if refine is ever able to work with meshes undergoing static aeroelastic deformations,
        #       you will augment the trimmed LFD controller to handle modal configurations, read in the
        #       aehist files created at istep-1, extract the GAFs from these files, solve a static modal
        #       system to compute gdisp values, and then write those to disk.  If that gdisp.txt exists
        #       this code will read it, and write it to moving_body.input, so that the steady solve will
        #       run about this deformed state.
        #       Does the moving_body.input used by LFD also need these gdisp0's?

    def _project_mode_shapes(self, istep):
        project = f'{self.project_name}{istep:02d}'
        massoud_file = f'{project}_massoud_body1.dat'

        # load FEM
        model = BDF()
        model.read_bdf(self.bdf_file)
        FEA_grid = model.get_xyz_in_coord()

        # downselect the nodes you'll use for splining
        radius = (np.max(FEA_grid[:, 1]) - np.min(FEA_grid[:, 1]))/self.nodal_downselect_filter
        keep = self._downselect_nodes(FEA_grid, radius)

        # load the massoud file
        CFD_grid = self._load_massoud(massoud_file)

        # load the mode shapes
        model = OP2()
        model.read_op2(self.op2_file)

        # RBF setup
        lu, piv, phi = self._rbf_setup(FEA_grid[keep, :], CFD_grid)

        # loop over modes
        for i in range(0, len(model.eigenvectors[1].modes)):

            # interpolate mode with RBF
            eigenvector = model.eigenvectors[1].data[i, :, :3]
            uvw = self._rbf_solve(eigenvector[keep, :], CFD_grid, lu, piv, phi)

            # zero-out y-displacements near the symmetry plane
            if self.y_symmetry is True:
                uvw = self._zero_y_near_symmetry_plane(uvw, CFD_grid)

            # write .dat file
            mode_file = f'{project}_body1_mode{i+1}.dat'

            print('writing', mode_file)
            f = open(massoud_file)
            f2 = open(mode_file, mode='w')

            lines = []
            while True:
                line = f.readline()
                if 'variables' in line.lower():
                    line = 'variables="x","y","z","id","xmd","ymd","zmd"\n'
                lines.append(line)

                if 'zone' in line.lower():
                    nodes = int(line.split('=')[2].split(',')[0])
                    elems = int(line.split('=')[3].split(',')[0])

                    for node in range(nodes):
                        line = f.readline()
                        x = float(line.split()[0])
                        y = float(line.split()[1])
                        z = float(line.split()[2])
                        id = int(line.split()[3])
                        line2 = " %0.15e, %0.15e, %0.15e, %d, %0.9e, %0.9e, %0.9e\n" % (
                            x, y, z, id, uvw[node, 0], uvw[node, 1], uvw[node, 2])
                        lines.append(line2)

                    for elem in range(elems):
                        line = f.readline()
                        lines.append(line)

                if not line:
                    break

            f2.writelines(lines)
            f2.close()
            f.close()

    def _downselect_nodes(self, nodes, radius):
        keep = np.array([-1])
        toss = np.array([-1])

        for i in range(0, len(nodes)):
            if np.in1d(i, toss)[0]*1 == 0:
                keep = np.r_[keep, i]
                toss = np.r_[toss, np.argwhere(np.sqrt(
                    (nodes[i, 0]-nodes[:, 0])**2 + (nodes[i, 1]-nodes[:, 1])**2 + (nodes[i, 2]-nodes[:, 2])**2
                ) < radius)[:, 0]]

        keep = keep[1:]
        return keep

    def _load_massoud(self, massoud_file):
        f = open(massoud_file, "r")
        contents = f.read().split()
        f.close()

        N = int(contents[12][2:-1])
        xyz = np.zeros([N, 3], 'float')
        for i in range(0, N):
            xyz[i, :] = np.array([float(contents[i*4+18]), float(contents[i*4+19]), float(contents[i*4+20])])
        return xyz

    def _rbf_setup(self, FEA_grid, CFD_grid):
        PHI = cdist(FEA_grid, FEA_grid)**3
        P = np.c_[FEA_grid, np.ones(len(FEA_grid))]
        A = np.r_[np.c_[PHI, P], np.r_[P, np.zeros([4, 4])].transpose()]

        lu, piv = lu_factor(A)
        phi = cdist(CFD_grid, FEA_grid)**3
        return lu, piv, phi

    def _rbf_solve(self, vector, CFD_grid, lu, piv, phi):
        RHS = np.r_[vector, np.zeros([4, 3])]
        params = lu_solve((lu, piv), RHS)
        uvw = phi @ params[0:len(vector), :] + np.c_[CFD_grid, np.ones(len(CFD_grid))] @ params[len(vector):, :]
        return uvw

    def _zero_y_near_symmetry_plane(self, uvw, CFD_grid):
        cutoff = (np.max(CFD_grid[:, 1]) - np.min(CFD_grid[:, 1]))/self.y_symmetry_cutoff
        a = np.argwhere(CFD_grid[:, 1] < cutoff)
        uvw[a, 1] = uvw[a, 1]*(-(CFD_grid[a, 1]/cutoff)**2 + 2*CFD_grid[a, 1]/cutoff)
        return uvw

    def _move_aehist(self, istep):
        project = f'{self.project_name}{istep:02d}'
        rm('aesubhist*')
        save_dir = f'{project}_aehist'
        mkdir(save_dir)
        mv('aehist*', save_dir)

    def _write_history(self, istep, pk):
        # read .out to find nnodes
        f = open(f'steady{istep:02d}.out', "r")
        contents = f.read().split()
        a = contents.index('nnodes')
        nnodes = int(contents[a+1])
        f.close()

        # read moving_body.input to find steady modal ampltiudes
        moving_body = f90nml.read(f'moving_body.input_steady{istep:02d}')
        modal_amplitude = moving_body['aeroelastic_modal_data']['gdisp0']

        # if this is the first step, create the history file, and populate first line: otherwise, append to end
        if istep == 1:
            f = open('history.dat', 'w+')
            f.write('istep nnodes steady_modal_amplitude rho_flutter vel_flutter omega_flutter R_flutter\n')
        else:
            f = open("history.dat", "a")

        # write data, and close
        f.write(
            str(istep) + ' ' + str(nnodes) + ' ' + str(modal_amplitude) + ' ' + str(pk.rho_flutter) + ' ' +
            str(pk.vel_flutter) + ' ' + str(pk.omega_flutter) + ' ' + str(pk.R_flutter.tolist()) + '\n')
        f.close()

    def _retrieve_old_PK_values(self, istep):
        f = open('history.dat', 'r')
        contents = f.readlines()

        nml = f90nml.read(f'moving_body.input_lfd{istep:02d}')
        N_modes = nml["aeroelastic_modal_data"]["nmode"][0]

        step = np.zeros(len(contents)-1, dtype=int)
        steady_modal_amplitude = np.zeros([len(contents)-1, N_modes], dtype=float)
        rho_flutter = np.zeros(len(contents)-1, dtype=float)
        vel_flutter = np.zeros(len(contents)-1, dtype=float)
        omega_flutter = np.zeros(len(contents)-1, dtype=float)
        R_flutter = np.zeros([len(contents)-1, N_modes*2], dtype=complex)

        for i in range(len(step)):
            line = contents[i+1].split()
            step[i] = int(line[0])

            steady_modal_amplitude[i, 0] = line[2][2:-1]
            for j in range(1, N_modes-1):
                steady_modal_amplitude[i, j] = float(line[2+j][0:-1])
            steady_modal_amplitude[i, -1] = line[1+N_modes][0:-2]

            rho_flutter[i] = float(line[2+N_modes])
            vel_flutter[i] = float(line[3+N_modes])
            omega_flutter[i] = float(line[4+N_modes])

            R_flutter[i, 0] = complex(line[5+N_modes][2:-2])
            for j in range(1, 2*N_modes-1):
                R_flutter[i, j] = complex(line[j+5+N_modes][1:-2])
            R_flutter[i, -1] = complex(line[j+6+N_modes][1:-2])

        old = np.argwhere(step == istep-1)[0][0]
        rho_flutter = rho_flutter[old]
        vel_flutter = vel_flutter[old]
        omega_flutter = omega_flutter[old]
        R_flutter = R_flutter[old, :]

        return rho_flutter, vel_flutter, omega_flutter, R_flutter
