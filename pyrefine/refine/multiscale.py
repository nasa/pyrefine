import os

from .base import RefineBase
from pbs4py import PBS


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

        #: str: The name of the scalar field used as the interpolant.
        #:  mach (default), incomp (incompressible vel magnitude),
        #:  htot, pressure, density, temperature.
        self.interpolant = 'mach'

    def run(self, istep: int, complexity: float):
        """
        Runs refine to calculate a multiscale metric, generate a new mesh, and
        interpolate the solution to the new mesh.
        """
        print('Running multiscale refine')
        self._run_multiscale_refine(istep, complexity)

    def _run_multiscale_refine(self, istep: int, complexity: float):
        ref_command = self._create_multiscale_refine_command(istep, complexity)

        job_name = f'refine{istep:02d}'
        command_list = [self.pbs.create_mpi_command(ref_command, job_name)]
        self.pbs.launch(job_name, command_list)
        self._check_for_refine_output_files(istep)

    def _check_for_refine_output_files(self, istep):
        next = self._create_project_rootname(istep+1)
        expected_files = [f'{next}.meshb',
                          f'{next}.lb8.ugrid',
                          f'{next}-restart.solb']
        for expected_file in expected_files:
            if not os.path.isfile(expected_file):
                raise FileNotFoundError(
                    f'Expected file: {expected_file} was not found. Something failed with refine')

    def _create_multiscale_refine_command(self, istep: int, complexity: float) -> str:
        current = self._create_project_rootname(istep)
        next = self._create_project_rootname(istep+1)

        command = f'refmpi loop {current} {next} {complexity}'
        command += self._create_multiscale_command_line_options()
        return self._add_common_ref_loop_options(command)

    def _create_multiscale_command_line_options(self) -> str:
        return f' --norm-power {self.lp_norm} --interpolant {self.interpolant}'


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
        self.sampling_data_filename_body = '_sampling_geom1_timestep'

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

    def run(self, istep: int, complexity: float):
        """
        Run refine in fixed-point mode for unsteady problems
        """
        print('Running multiscale refine (fixed point)')
        self._check_that_window_values_are_valid()
        self._run_multiscale_refine(istep, complexity)

    def _create_multiscale_command_line_options(self) -> str:
        options = super()._create_multiscale_command_line_options()

        file_body = self.sampling_data_filename_body
        first_step = self.window_first_step
        freq = self.window_metric_freq
        last_step = self.window_last_step
        return options + f' --fixed-point {file_body} {first_step} {freq} {last_step}'

    def _check_that_window_values_are_valid(self):
        if self.window_first_step < 0:
            raise ValueError('Refine window_first_step not set. Must specify window parameters')
        if self.window_last_step < 0:
            raise ValueError('Refine window_last_step not set. Must specify window parameters')
        if self.window_metric_freq < 0:
            raise ValueError('Refine window_metric_freq not set. Must specify window parameters')
