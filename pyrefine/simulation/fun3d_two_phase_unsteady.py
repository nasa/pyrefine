import os
import f90nml

from .fun3d import SimulationFun3dFV, SimulationFun3dSFE


class SimulationFun3dTwoPhase(SimulationFun3dFV):
    def __init__(self, project_name, pbs=None, external_wall_distance=True):
        """
        Runs two unsteady fun3d finite volume analyses.
        The first one settles transients associated with restarting from the
        interpolated solution.
        The second one is for collecting flow field snapshots for the metric

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

        #: int or None: The number of steps to run in the simulation to settle
        #:   transients created from interpolating the solution. Default behavior
        #:   (None) is to read it from the fun3d.nml
        self.transient_steps = None

        #: int or None: The number of steps to run in the simulation phase where
        #:   the solution will be saved for computing the metric. Default behavior
        #:   (None) is to read it from the fun3d.nml
        self.metric_steps = None

        #: int: The frequency at which volume files will be written for metric computation.
        #: Set to volume_animation_freq for metric collection phase of the simulation. Default
        #: behavior is to read volume_animation_freq from the namelist
        self.metric_frequency = None

    def run(self, istep):
        """
        Prep the fun3d namelist and submit a job to run the flow solver
        """
        print('Running the flow simulation to settle transients')
        self._run_fun3d_simulation(istep, 'transient')

        print('Running the flow simulation to collect metric')
        self._run_fun3d_simulation(istep, 'metric', skip_external_distance=False)

    def _update_transient_phase_inputs_in_nml(self, istep: int, nml: f90nml.Namelist):
        if self.transient_steps is None:
            self.transient_steps = nml['code_run_control']['steps']
        else:
            nml['code_run_control']['steps'] = self.transient_steps
        nml['global']['volume_animation_freq'] = -1

    def _update_metric_phase_inputs_in_nml(self, istep: int, nml: f90nml.Namelist):
        nml['code_run_control']['restart_read'] = 'on_nohistorykept'

        if self.metric_steps is None:
            self.metric_steps = nml['code_run_control']['steps']
        else:
            nml['code_run_control']['steps'] = self.metric_steps

        if self.metric_frequency is None:
            self.metric_frequency = nml['global']['volume_animation_freq']
        else:
            nml['global']['volume_animation_freq'] = self.metric_frequency

        # write out Mach number volume files for metric computation
        nml['volume_output_variables']['mach'] = True
        nml['volume_output_variables']['primitive_variables'] = False
        nml['volume_output_variables']['turb1'] = False

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        if job_name == 'transient':
            self._update_transient_phase_inputs_in_nml(istep, nml)
        else:
            self._update_metric_phase_inputs_in_nml(istep, nml)
            import_from = False
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)

    def _check_for_output_files(self, istep: int, job_name: str):
        if job_name == 'transient':
            super()._check_for_output_files(istep, job_name)
        else:
            self._check_for_metric_file(self, istep)

    def _check_for_metric_file(self, istep: int):
        project = self._create_project_rootname(istep)
        expected_file = f'{project}_volume_timestep{self.metric_frequency}.solb'
        if not os.path.exists(expected_file):
            raise FileNotFoundError(
                f'Expected file: {expected_file} was not found. Something likely failed with flow solver.')


class SimulationSFETwoPhase(SimulationFun3dSFE):
    def __init__(self, project_name, pbs=None, external_wall_distance=True):
        """
        Runs two fun3d SFE analyses.
        The first one is a steady analysis to converge the intepolated solution.
        The second one is unsteady for collecting flow field snapshots for the
        metric.

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

        self.fun3d_nml = 'fun3d.nml_steady'

        #: str: unsteady phase's fun3d.nml
        self.fun3d_nml_unsteady = 'fun3d.nml_unsteady'

        self.sfe_cfg = 'sfe.cfg_steady'

        #: str: unsteady phase's sfe.cfg
        self.sfe_cfg_unsteady = 'sfe.cfg_unsteady'

    def get_expected_file_list(self):
        expected_files = super().get_expected_file_list()
        expected_files.extend([self.sfe_cfg_unsteady, self.fun3d_nml_unsteady])
        return expected_files

    def run(self, istep):
        print('Running steady fun3d solver')
        self._run_fun3d_simulation(istep, 'steady')

        print('Running unsteady fun3d solver')
        self._run_fun3d_simulation(istep, 'unsteady', skip_external_distance=True)

    def _get_template_sfe_cfg_filename(self, job_name):
        if job_name == 'steady':
            return f'../{self.sfe_cfg}'
        else:
            return f'../{self.sfe_cfg_unsteady}'

    def _get_template_fun3d_nml_filename(self, job_name):
        if job_name == 'steady':
            return f'../{self.fun3d_nml}'
        else:
            return f'../{self.fun3d_nml_unsteady}'

    def _update_fun3d_nml_fields(self, istep: int, job_name: str, nml: f90nml.Namelist, import_from=True):
        if job_name == 'unsteady':
            import_from = False
        super()._update_fun3d_nml_fields(istep, job_name, nml, import_from)
