import datetime
import os
from typing import List

import f90nml

from pyrefine.shell_utils import cp

from .base import SimulationBase
from .distance_refine import DistanceRefine


class SimulationFun3dFV(SimulationBase):
    def __init__(self, project_name, pbs=None, external_wall_distance=True, omp_threads=None, ranks_per_node=None):
        """
        Runs fun3d finite volume analysis. Each time that run is called, the fun3d.nml
        in the adaptation root directory will be read, the distance and restart solb inputs will
        be adjusted to account for the current adaptation cycle number, and then use nodet_mpi to
        run the simulation.

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
        ranks_per_node: int
            Number of mpi ranks per node. By default, all available ranks are used. This option is used
            for hybrid CPU/GPU simulations and should be left as None otherwise.
        """
        super().__init__(project_name, pbs)
        self.omp_threads = omp_threads
        self.ranks_per_node = ranks_per_node

        #: bool: Whether a distance field from an external calculator is needed
        self.external_wall_distance = external_wall_distance

        #: str: Name of the namelist file in the adaptation root directory
        self.fun3d_nml = "fun3d.nml"

        #: str: The command line arguments that will be added to calls to nodet_mpi
        self.fun3d_command_line_args = ""

        #: bool: Whether the simulation should read the refine-interpolated
        #: solution, i.e., whether or not to use the flow_initialization nml.
        self.import_solution_from_previous_mesh = True

        #: bool: Whether to expect a moving_body.input file in the root directory
        self.expect_moving_body_input = False

        #: str: moving_body.input file name in root directory
        self.moving_body_input = "moving_body.input"

        #: :class:`~pyrefine.simulation.distance_base.DistanceBase`: the distance calculator
        self.distance = DistanceRefine(project_name, pbs)

        #: str: type of file to write expect for fields written
        self.field_file_extension = "solb"

        #: list: list of extra input files that should also be copied into the Flow directory
        self.extra_input_files = []

        #: bool: Whether to expect an ascent_actions_default.yaml file in the root directory
        self.ascent_visualization = False

        #: str: ascent_actions_default.yaml file name in root directory
        self.ascent_visualization_input = "ascent_actions_default.yaml"

        #: bool: Whether to launch NVIDIA MPS with pyrefine
        self.launch_mps = False

    def get_expected_file_list(self):
        expected_files = [self.fun3d_nml]
        if self.expect_moving_body_input:
            expected_files.append(self.moving_body_input)
        if self.ascent_visualization:
            expected_files.append(self.ascent_visualization_input)
        expected_files.extend(self.extra_input_files)
        return expected_files

    def run(self, istep: int):
        print("Running the flow simulation")
        start_time = datetime.datetime.now()
        print(f'Flow{istep} Queue Start Time: {start_time}')
        self._run_fun3d_simulation(istep, "flow")
        end_time = datetime.datetime.now()
        elapsed_time = end_time - start_time
        print(f'Flow{istep} Queue End Time: {end_time}')
        print(f'Flow{istep} Elapsed Time: {elapsed_time}')

    def _run_fun3d_simulation(self, istep: int, job_name: str, skip_external_distance=False):
        self._prepare_input_files(istep, job_name)
        self._save_a_copy_of_solver_inputs(istep, job_name)
        command_list = self._create_list_of_commands_to_run(istep, job_name, skip_external_distance)
        self.pbs.launch(f"{job_name}{istep:02d}", command_list)
        self._check_for_output_files(istep, job_name)

    def _check_for_output_files(self, istep, job_name):
        if self.external_wall_distance:
            self._check_for_distance_file(istep)
        self._check_for_volume_output(istep)

    def _check_for_distance_file(self, istep):
        expected_file = self.distance.create_distance_filename(istep)
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(f"Expected file: {expected_file} was not found. Distance calculator failed.")

    def _check_for_volume_output(self, istep):
        project = self._create_project_rootname(istep)
        expected_file = f"{project}_volume.{self.field_file_extension}"
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(f"Expected file: {expected_file} was not found. Something failed with flow solver.")

    def _prepare_input_files(self, istep: int, job_name: str):
        self._prepare_fun3d_nml(istep, job_name)
        if self.expect_moving_body_input:
            self._prepare_moving_body_input(istep, job_name)
        if self.ascent_visualization:
            self._prepare_ascent_visualization_input(istep, job_name)

    def _prepare_fun3d_nml(self, istep, job_name):
        nml = f90nml.read(self._get_template_fun3d_nml_filename(job_name))
        import_from = self._read_restart_solb(istep)
        self._update_fun3d_nml_fields(istep, job_name, nml, import_from)
        nml.write("fun3d.nml", force=True)

    def _get_template_fun3d_nml_filename(self, job_name):
        return f"../{self.fun3d_nml}"

    def _read_restart_solb(self, istep):
        return istep > 1 and self.import_solution_from_previous_mesh

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        self._set_project_rootname_in_nml(istep, nml)
        if self.external_wall_distance:
            self._set_distance_from_file_in_nml(istep, nml)
        if import_from:
            self._set_import_from_in_nml(istep, nml)
        # note: FV does not use openmp and should not use this
        if (self.__class__ is not SimulationFun3dFV):
            self._set_openmp_inputs_in_nml(nml, self.omp_threads)

    def _set_project_rootname_in_nml(self, istep: int, nml: f90nml.Namelist):
        nml["project"]["project_rootname"] = self._create_project_rootname(istep)

    def _set_import_from_in_nml(self, istep: int, nml: f90nml.Namelist):
        # if namelist not defined, skip it to enable restarting from scratch
        if "flow_initialization" in nml:
            if "import_from" in nml["flow_initialization"]:
                nml["flow_initialization"]["import_from"] = f"{self._create_project_rootname(istep)}-restart.solb"

    def _set_distance_from_file_in_nml(self, istep: int, nml: f90nml.Namelist):
        nml["special_parameters"]["distance_from_file"] = self.distance.create_distance_filename(istep)

    def _set_openmp_inputs_in_nml(self, nml: f90nml.Namelist, omp_threads: int):
        value = True if omp_threads is not None else False
        if (value):
            nml["code_run_control"]["use_openmp"] = value
            nml["code_run_control"]["grid_coloring"] = value

    def _prepare_moving_body_input(self, istep: int, job_name: str):
        cp(self._get_template_moving_body_filename(job_name), "moving_body.input")

    def _prepare_ascent_visualization_input(self, istep: int, job_name: str):
        cp(self._get_template_ascent_visualization_filename(job_name), "ascent_actions.yaml")
        name = self._create_project_rootname(istep)
        with open("ascent_actions.yaml") as f:
            updated_file=f.read().replace('{project}', name)
        with open("ascent_actions.yaml", "w") as f:
            f.write(updated_file)

    def _get_template_moving_body_filename(self, job_name):
        return f"../{self.moving_body_input}"

    def _get_template_ascent_visualization_filename(self, job_name):
        return f"../{self.ascent_visualization_input}"

    def _save_a_copy_of_solver_inputs(self, istep, job_name):
        job_name_with_step_number = f"{job_name}{istep:02d}"
        cp("fun3d.nml", f"fun3d.nml_{job_name_with_step_number}")
        if self.expect_moving_body_input:
            cp("moving_body.input", f"moving_body.input_{job_name_with_step_number}")

    def _create_list_of_commands_to_run(self, istep, job_name, skip_external_distance=False) -> List[str]:
        command_list = []
        if self.external_wall_distance and not skip_external_distance:
            command_list.append(self._create_distance_command(istep))
        if self.launch_mps:
            command_list.append(self.pbs.create_mpi_command("nvidia-cuda-mps-control -d", "mps", ranks_per_node=1))
        command_list.append(self._create_fun3d_command(istep, job_name))
        time_command_start = f'printf "Flow{istep} Start Time: " && date'
        time_command_end = f'printf "Flow{istep} End Time: " && date'
        command_list.insert(0, time_command_start)
        command_list.append(time_command_end)
        return command_list

    def _create_distance_command(self, istep: int):
        self.distance.pbs = self.pbs
        self.distance.project_name = self.project_name
        return self.distance.create_distance_command(istep)

    def _create_fun3d_command(self, istep: int, job_name="flow") -> str:
        job_name_with_number = f"{job_name}{istep:02d}"

        command = self._get_simulation_nodet(job_name)
        command += self._get_user_specified_fun3d_command_line_args_str()
        command += self._get_simulation_specific_fun3d_command_line_args_str(job_name)
        return self.pbs.create_mpi_command(command, job_name_with_number, self.omp_threads, self.ranks_per_node)

    def _get_user_specified_fun3d_command_line_args_str(self):
        if len(self.fun3d_command_line_args) > 0:
            return f" {self.fun3d_command_line_args}"
        return ""

    def _get_simulation_nodet(self, job_name) -> str:
        return "nodet_mpi"

    def _get_simulation_specific_fun3d_command_line_args_str(self, job_name) -> str:
        return ""


class SimulationFun3dSFE(SimulationFun3dFV):
    def __init__(self, project_name, pbs=None, external_wall_distance=True, omp_threads=None, ranks_per_node=None):
        """
        Runs fun3d stabilized finite element analysis. Does the same actions as the
        FV version but also handles the sfe.cfg file.

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
        ranks_per_node: int
            Number of mpi ranks per node. By default, all available ranks are used. This option is used
            for hybrid CPU/GPU simulations and should be left as None otherwise.
        """
        super().__init__(project_name, pbs, external_wall_distance, omp_threads)

        self.sfe_cfg = "sfe.cfg"

    def get_expected_file_list(self):
        expected_files = super().get_expected_file_list()
        expected_files.append(self.sfe_cfg)
        return expected_files

    def _save_a_copy_of_solver_inputs(self, istep, job_name):
        super()._save_a_copy_of_solver_inputs(istep, job_name)
        cp("sfe.cfg", f"sfe.cfg_{job_name}{istep:02d}")

    def _prepare_input_files(self, istep: int, job_name: str):
        self._prepare_sfe_cfg(istep, job_name)
        super()._prepare_input_files(istep, job_name)

    def _prepare_sfe_cfg(self, istep: int, job_name: str):
        cp(self._get_template_sfe_cfg_filename(job_name), "sfe.cfg")

    def _get_template_sfe_cfg_filename(self, job_name):
        return f"../{self.sfe_cfg}"
