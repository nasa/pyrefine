import datetime
import os

from pbs4py import PBS

from .base import RefineBase


class RefineMultiscale(RefineBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        Refine for steady analysis (single solution field) and the multiscale
        metric based on Mach number

        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int or float: The lp norm value for the refine metric computation. Larger values
        #:  will target the regions of highest error more but may underresolve
        #:  lower gradient regions too much. The default value is 4.
        self.lp_norm = 4

        #: str: The name or file of the scalar field used as the interpolant.
        #:  mach (default), incomp (incompressible vel magnitude),
        #:  htot, pressure, density, temperature, or file.
        self.interpolant = "mach"

        #: str: The label for the interpolant file option.
        self.interpolant_label = "sampling_geom1"

    def run(self, istep: int, complexity: float):
        """
        Runs refine to calculate a multiscale metric, generate a new mesh, and
        interpolate the solution to the new mesh.
        """
        print("Running multiscale refine")
        start_time = datetime.datetime.now()
        print(f"Refine{istep} Queue Start Time: {start_time}")
        self._run_multiscale_refine(istep, complexity)
        end_time = datetime.datetime.now()
        elapsed_time = end_time - start_time
        print(f"Refine{istep} Queue End Time: {end_time}")
        print(f"Refine{istep} Elapsed Time: {elapsed_time}")

    def _run_multiscale_refine(self, istep: int, complexity: float):
        ref_command = self._create_multiscale_refine_command(istep, complexity)
        job_name = f"refine{istep:02d}"

        time_command_start = f'printf "Refine{istep} Start Time: " && date'
        time_command_end = f'printf "Refine{istep} End Time: " && date'

        command_list = [time_command_start, self.pbs.create_mpi_command(ref_command, job_name)]
        if self.rescale_2D_length > 0:
            command_list.extend(self.create_rescale_2d_command_list(istep + 1))
        command_list.append(time_command_end)

        self.pbs.launch(job_name, command_list)
        self._check_for_refine_output_files(istep)

    def _check_for_refine_output_files(self, istep):
        next = self._create_project_rootname(istep + 1)
        expected_files = [f"{next}.meshb", f"{next}.lb8.ugrid", f"{next}-restart.solb"]
        for expected_file in expected_files:
            if not os.path.isfile(expected_file):
                raise FileNotFoundError(f"Expected file: {expected_file} was not found. Something failed with refine")

    def _create_multiscale_refine_command(self, istep: int, complexity: float) -> str:
        current = self._create_project_rootname(istep)
        next = self._create_project_rootname(istep + 1)

        self._create_interpolant_option(istep)

        command = f"refmpi loop {current} {next} {complexity}"
        command += self._create_multiscale_command_line_options()
        return self._add_common_ref_loop_options(command)

    def _create_multiscale_command_line_options(self) -> str:
        return f" --norm-power {self.lp_norm} --interpolant {self.interpolant}"

    def _create_interpolant_option(self, istep):
        current = self._create_project_rootname(istep)
        last = self._create_project_rootname(istep - 1)

        print(f"current, last = {current}, {last}")
        if self.interpolant == "file":
            self.interpolant = f"{current}_{self.interpolant_label}.solb"

        if self.interpolant == f"{last}_{self.interpolant_label}.solb":
            self.interpolant = f"{current}_{self.interpolant_label}.solb"


class RefineMultiscaleFixedPoint(RefineMultiscale):
    """
    Refine's fixed point metric for unsteady analysis where there are multiple
    snapshots of the flow field.
    Multiscale metric based on Mach number.
    """

    def __init__(self, project_name: str, pbs: PBS = None):
        """
        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int: The start of the sampling window from which refine should compute the metric.
        self.window_first_step = -1

        #: int: The end of the sampling window from which refine should compute the metric.
        self.window_last_step = -1

        #: int: The sampling frequency in the window from which refine should
        #:  compute the metric.
        self.window_metric_freq = -1

        #: str: The middle part of the filename which refine should look for the
        #: scalar on which to base the metric on. For example,
        #: bscw-box20[_sampling_geom1_timestep]1000.solb #: where the body is
        #: the part in square brackets before the timestep number
        #: (1000) and after the project name + adaptation cycle number (bscw-box20).
        #: The default name is "_sampling_geom1_timestep"
        self.sampling_data_filename_body = "_sampling_geom1_timestep"

        self.hlres = False
        self.mach = -1.0
        self.reynolds_number = -1.0

    def set_timestep_range_and_frequency(self, first_step, last_step, metric_freq):
        """
        Set the window of timesteps from which refine should compute the metric
        and set the metric step frequency, i.e. the frequency at which solution
        files were saved during the analysis in window.

        Parameters
        ----------
        first_step: int
        last_step: int
        metric_freq: int
        """
        self.window_first_step = first_step
        self.window_last_step = last_step
        self.window_metric_freq = metric_freq

    def set_hlres(self, mach, reynolds_number):
        """
        Set the window of timesteps from which refine should compute the metric
        and set the metric step frequency, i.e. the frequency at which solution
        files were saved during the analysis in window.

        Parameters
        ----------
        mach: float
            The reference Mach number
        reynolds_number: float
            The reference Reynolds number per unit length
        """
        self.hlres = True
        self.mach = mach
        self.reynolds_number = reynolds_number

    def run(self, istep: int, complexity: float):
        """
        Run refine in fixed-point mode for unsteady problems
        """
        print("Running multiscale refine (fixed point)")
        self._check_that_window_values_are_valid()
        self._run_multiscale_refine(istep, complexity)

    def _create_multiscale_command_line_options(self) -> str:
        options = super()._create_multiscale_command_line_options()

        file_body = self.sampling_data_filename_body
        first_step = self.window_first_step
        freq = self.window_metric_freq
        last_step = self.window_last_step
        options += f" --fixed-point {file_body} {first_step} {freq} {last_step}"

        if self.hlres:
            self._check_that_hrles_values_are_valid()
            # tags should be the same so just use the project01 mapbc
            project = self._create_project_rootname(1)
            options += f" --hrles {self.mach} {self.reynolds_number} --fun3d-mapbc {project}.mapbc"
        return options

    def _check_that_window_values_are_valid(self):
        if self.window_first_step < 0:
            raise ValueError("Refine window_first_step not set. Must specify window parameters")
        if self.window_last_step < 0:
            raise ValueError("Refine window_last_step not set. Must specify window parameters")
        if self.window_metric_freq < 0:
            raise ValueError("Refine window_metric_freq not set. Must specify window parameters")

    def _check_that_hrles_values_are_valid(self):
        if self.mach < 0.0:
            raise ValueError("Refine mach not set. Must specify if running with hrles option")
        if self.reynolds_number < 0.0:
            raise ValueError("Refine reynolds number not set. Must specify if running with hrles option")
