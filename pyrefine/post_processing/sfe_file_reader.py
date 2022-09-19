import os
import numpy as np

from .tecplot_writer import write_data_to_tecplot_format
from pyrefine.shell_utils import grep


class SFEForwardHistoryReader:
    def __init__(self, data_directory: str, project_rootname: str, mesh_number: int):
        self.dir = data_directory
        self.project = project_rootname
        self.imesh = mesh_number
        self.prefix = 'flow'
        self.logfile = f'{self.dir}/{self.prefix}{self.imesh:02}.out'

        self.normalized_timings = False

        if self.dir == '' or project_rootname == '':
            self.set_empty_data()
        else:
            self.read_data()

    def set_empty_data(self):
        self.number_of_steps = 0
        self.normalized_timings = False
        self.timing_data = {}
        self.norm_timing_data = {}
        self.residual_convergence_data = {}
        self.preconditioner_data = {}

    def read_data(self):
        self.timing_data = self.extract_timing_information(False, self.logfile)
        self.norm_timing_data = self.extract_timing_information(True, self.logfile)
        self.residual_convergence_data = self.set_convergence_data()
        self.preconditioner_data = self.extract_preconditioner_data()

    def extract_timing_information(self, normalized_timings, file) -> dict:
        timing_data = {}

        strings = ["Wall clock time for residual", "Wall clock time for left-hand side", "init wall clock time",
                   "core wall clock time", "Preconditioner update wall clock time",
                   "Preconditioner application wall clock time", "Matrix vector product wall clock time",
                   "Wall clock time for linear solve", "Wall clock time for line search"]

        timing_list = []
        for pattern in strings:
            lines = grep(pattern, file)
            values = [float(line.split('=')[-1]) for line in lines]
            timing_list.append(values)

        timing_list = np.array(timing_list).transpose()

        if normalized_timings:
            total_time_per_iteration = timing_list[:, 0] + timing_list[:, 1] + timing_list[:, 7] + timing_list[:, 8]
            total_time_per_iteration = total_time_per_iteration.reshape((total_time_per_iteration.shape[0], 1))
            timing_list = timing_list/total_time_per_iteration

        variable_names = ["RHS", "LHS", "Linear method init", "Linear method core", "Preconditioner update",
                          "Preconditioner apply", "Mat-vec product", "Linear solve", "Line search"]

        self.number_of_steps = timing_list.shape[0]

        for var in variable_names:
            timing_data[var] = np.zeros(self.number_of_steps, dtype=float)

        for step in range(0, self.number_of_steps):
            for ivar, var in enumerate(variable_names):
                timing_data[var][step] = float(timing_list[step, ivar])

        self.variable_names = variable_names

        return timing_data

    def write_convergence_data_to_tec(self, filename):
        title = f'{self.project}_sfe_forward_convergence_hist'
        zone = f'{self.project}'

        data = np.zeros((self.number_of_steps, len(self.residual_convergence_data)+1))
        data[:, 0] = np.arange(1, self.number_of_steps+1, 1)
        variables = ['Steps']
        for ivar, (var, var_data) in enumerate(self.residual_convergence_data.items()):
            variables.append(var)
            data[:, ivar+1] = var_data
        write_data_to_tecplot_format(filename, title, data, variables, zone)

    def write_timing_data_to_tec(self, filename):
        title = f'{self.project}_sfe_forward_timing_hist'
        zone = f'{self.project}'

        data = np.zeros((self.number_of_steps, len(self.timing_data)+1))
        data[:, 0] = np.arange(1, self.number_of_steps+1, 1)
        variables = ['Steps']
        for ivar, (var, var_data) in enumerate(self.timing_data.items()):
            variables.append(var)
            data[:, ivar+1] = var_data
        write_data_to_tecplot_format(filename, title, data, variables, zone)

    def write_preconditioner_data_to_tec(self, filename):
        title = f'{self.project}_sfe_forward_preconditioner_hist'
        zone = f'{self.project}'

        data = np.zeros((self.number_of_steps, len(self.preconditioner_data)+1))
        data[:, 0] = np.arange(1, self.number_of_steps+1, 1)
        variables = ['Steps']
        for ivar, (var, var_data) in enumerate(self.preconditioner_data.items()):
            variables.append(var)
            data[:, ivar+1] = var_data
        write_data_to_tecplot_format(filename, title, data, variables, zone)

    def set_convergence_data(self) -> dict:
        nonlinear_residual_data = self.extract_nonlinear_residual()
        linear_residual_data = self.extract_linear_residual()
        update_ratio_data = self.extract_update_ratio()
        cfl_data = self.extract_cfl()
        FOM_data = self.extract_FOM()

        return {**nonlinear_residual_data, **linear_residual_data, **update_ratio_data, **cfl_data, **FOM_data}

    def extract_nonlinear_residual(self) -> dict:
        nonlinear_residual_data = {}

        string = ["currentIteration"]

        nonlinear_residual_list = []
        for i in string:
            lines = grep(i, self.logfile)
            step_data = np.array([np.fromstring(line.split('=')[-1]) for line in lines])
            nonlinear_residual_list.append(step_data)

        variable_names = ["Density", "X-momentum", "Y-momentum", "Z-momentum",
                          "Energy"]

        if nonlinear_residual_list[0].shape[1] > 5:
            variable_names.append("Turbulence")

        self.number_of_steps = nonlinear_residual_list[0].shape[0]

        for var in variable_names:
            nonlinear_residual_data[var] = np.zeros(self.number_of_steps, dtype=float)

        for step in range(0, self.number_of_steps):
            for ivar, var in enumerate(variable_names):
                nonlinear_residual_data[var][step] = float(nonlinear_residual_list[0][step, ivar])

        self.nonlinear_residual_variable_names = variable_names

        return nonlinear_residual_data

    def extract_linear_residual(self) -> dict:
        linear_residual_data = {}

        string = ["Final Search direction"]

        linear_residual_list = []
        for i in string:
            os.system('grep "%s" %s | tr -s " " | cut -d " " -f16 > ltmp.dat' % (i, self.logfile))
            linear_residual_list.append(np.loadtxt('ltmp.dat'))
        os.remove('ltmp.dat')

        variable_names = ["Final Linear"]

        for var in variable_names:
            linear_residual_data[var] = np.zeros(self.number_of_steps, dtype=float)

        for step in range(0, self.number_of_steps):
            for var in variable_names:
                linear_residual_data[var][step] = float(linear_residual_list[0][step])

        self.linear_residual_variable_names = variable_names

        return linear_residual_data

    def extract_update_ratio(self) -> dict:
        update_ratio_data = {}

        string = ["rms_dq/rms_q ="]

        update_ratio_list = []
        for i in string:
            os.system('grep "%s" %s | tr -s " " | cut -d "=" -f4 | cut -d " " -f2 > ltmp.dat' % (i, self.logfile))
            update_ratio_list.append(np.loadtxt('ltmp.dat'))
        os.remove('ltmp.dat')

        variable_names = ["Linear update ratio"]

        for var in variable_names:
            update_ratio_data[var] = np.zeros(self.number_of_steps, dtype=float)

        for step in range(0, self.number_of_steps):
            for var in variable_names:
                update_ratio_data[var][step] = float(update_ratio_list[0][step])

        self.update_ratio_variable_names = variable_names

        return update_ratio_data

    def extract_cfl(self) -> dict:
        cfl_data = {}

        string = ["rms ="]

        cfl_list = []
        for i in string:
            os.system('grep "%s" %s | tr -s " " | cut -d "=" -f3 > ctmp.dat' % (i, self.logfile))
            cfl_list.append(np.loadtxt('ctmp.dat'))
        os.remove('ctmp.dat')

        variable_names = ["CFL"]

        for var in variable_names:
            cfl_data[var] = np.zeros(self.number_of_steps, dtype=float)

        for step in range(0, self.number_of_steps):
            for var in variable_names:
                cfl_data[var][step] = float(cfl_list[0][step])

        self.cfl_variable_names = variable_names

        return cfl_data

    def extract_FOM(self) -> dict:
        FOM_data = {}

        string = ["CL ="]

        FOM_list = []
        for i in string:
            os.system('grep "%s" %s | tr -s " " | cut -d " " -f3 > ftmp.dat' % (i, self.logfile))
            FOM_list.append(np.loadtxt('ftmp.dat'))
        os.remove('ftmp.dat')

        string = ["CD ="]
        for i in string:
            os.system('grep "%s" %s | tr -s " " | cut -d " " -f6 > ftmp.dat' % (i, self.logfile))
            FOM_list.append(np.loadtxt('ftmp.dat'))
        os.remove('ftmp.dat')

        FOM_list = np.array(FOM_list).transpose()

        variable_names = ["CL", "CD"]

        for var in variable_names:
            FOM_data[var] = np.zeros(self.number_of_steps, dtype=float)

        for step in range(0, self.number_of_steps):
            for ivar, var in enumerate(variable_names):
                FOM_data[var][step] = float(FOM_list[step, ivar])

        self.FOM_variable_names = variable_names

        return FOM_data

    def extract_preconditioner_data(self) -> dict:
        preconditioner_data = {}
        preconditioner_list = []
        self.read_preconditioner_data_from_mesh(preconditioner_list, self.logfile)
        preconditioner_list = np.array(preconditioner_list[0])

        variable_names = ["Amplification", "Rank"]
        for var in variable_names:
            preconditioner_data[var] = np.zeros(self.number_of_steps, dtype=float)
        for step in range(0, self.number_of_steps):
            for ivar, var in enumerate(variable_names):
                preconditioner_data[var][step] = float(preconditioner_list[step, ivar])

        self.preconditioner_variable_names = variable_names

        return preconditioner_data

    def read_preconditioner_data_from_mesh(self, preconditioner_list, file):
        string = ["max preconditioner"]
        for i in string:
            os.system('grep "%s" %s | tr -s " " | cut -d "=" -f2,3 | cut -d " " -f2,5 > ptmp.dat' % (i, file))
            preconditioner_list.append(np.loadtxt('ptmp.dat'))
        os.remove('ptmp.dat')


class SFEGoalOrientedHistoryReader(SFEForwardHistoryReader):
    def __init__(self, data_directory: str, project_rootname: str):
        super().__init__(data_directory, project_rootname, 1)
        self.adjoint_prefix = 'adjoint'
        if self.dir == '' or project_rootname == '':
            self.set_empty_adjoint_data()
        else:
            self.read_adjoint_data()

    def set_empty_adjoint_data(self):
        self.number_of_adjoints = 0
        self.adjoint_data = {}

    def read_adjoint_data(self):
        self.number_of_adjoints = self.count_number_of_adjoints()
        if self.number_of_adjoints > 0:
            self.adjoint_data = self.extract_adjoint_data()

    def write_adjoint_data_to_tec(self, filename):
        title = f'{self.project}_sfe_adjoint_hist'
        zone = f'{self.project}'

        data = np.zeros((self.number_of_adjoints, len(self.adjoint_data)+1))
        data[:, 0] = np.arange(1, self.number_of_adjoints+1, 1)
        variables = ['Meshes']
        for ivar, (var, var_data) in enumerate(self.adjoint_data.items()):
            variables.append(var)
            data[:, ivar+1] = var_data
        write_data_to_tecplot_format(filename, title, data, variables, zone)

    def count_number_of_adjoints(self):
        adjoint_num = 1
        while os.path.isfile(f'{self.dir}/{self.adjoint_prefix}{adjoint_num:02}.out'):
            adjoint_num += 1
        return adjoint_num - 1

    def extract_adjoint_data(self) -> dict:
        adjoint_data = {}
        preconditioner_data = {}
        preconditioner_list = []
        linear_residual_data = {}
        lr_string = ["Final Search direction"]
        linear_residual_list = []
        timing_data = {}
        all_timing_list = []
        timing_string = [
            "Wall clock time for adjoint RHS", "Wall clock time for adjoint LHS", "init wall clock time",
            "core wall clock time", "Preconditioner update wall clock time",
            "Preconditioner application wall clock time", "Matrix vector product wall clock time",
            "Wall clock time for linear solve"]

        for imesh in range(1, self.number_of_adjoints+1):
            file = f'{self.dir}/{self.adjoint_prefix}{imesh:02}.out'
            self.read_preconditioner_data_from_mesh(preconditioner_list, file)
            for i in lr_string:
                os.system('grep "%s" %s | tr -s " " | cut -d " " -f6,16 > altmp.dat' % (i, file))
                linear_residual_list.append(np.loadtxt('altmp.dat'))
            os.remove('altmp.dat')
            timing_list = []
            for i in timing_string:
                os.system('grep "%s" %s | tr -s " " | cut -d "=" -f2 | tr -d " " > atmp.dat' % (i, file))
                timing_list.append(np.loadtxt('atmp.dat'))
            all_timing_list.append(np.array(timing_list).transpose())
            os.remove('atmp.dat')

        preconditioner_list = np.array(preconditioner_list)
        linear_residual_list = np.array(linear_residual_list)
        all_timing_list = np.array(all_timing_list)

        precond_names = ["Preconditioner Amplification", "Preconditioner Rank"]
        for var in precond_names:
            preconditioner_data[var] = np.zeros(self.number_of_adjoints, dtype=float)
        for step in range(0, self.number_of_adjoints):
            for ivar, var in enumerate(precond_names):
                preconditioner_data[var][step] = float(preconditioner_list[step, ivar])

        linear_names = ["Search Directions", "Final Linear"]
        for var in linear_names:
            linear_residual_data[var] = np.zeros(self.number_of_adjoints, dtype=float)
        for step in range(0, self.number_of_adjoints):
            for ivar, var in enumerate(linear_names):
                linear_residual_data[var][step] = float(linear_residual_list[step, ivar])

        timing_names = ["RHS [s]", "LHS [s]", "Linear method init [s]", "Linear method core [s]",
                        "Preconditioner update [s]", "Preconditioner apply [s]", "Mat-vec product [s]", "Linear solve [s]"]
        for var in timing_names:
            timing_data[var] = np.zeros(self.number_of_adjoints, dtype=float)
        for step in range(0, self.number_of_adjoints):
            for ivar, var in enumerate(timing_names):
                timing_data[var][step] = float(all_timing_list[step][ivar])

        adjoint_data = {**preconditioner_data, **linear_residual_data, **timing_data}

        # print(f'SFEGoalOrientedHistoryReader loaded data for {self.number_of_adjoints} adjoint solutions')

        return adjoint_data
