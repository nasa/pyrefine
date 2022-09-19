import os
from typing import List

from .base import RefineBase
from pbs4py import PBS


class RefineGoalOriented(RefineBase):
    """
    Refine goal-oriented adaptation metric. Options for the 'opt-goal' or
    cons-visc' versions of the metric
    """

    def __init__(self, project_name: str,
                 pbs: PBS = None,
                 mask_strong_bc: bool = False):
        super().__init__(project_name, pbs)

        #: bool: Mask strong boundaries in the adjoint field to create a smooth adjoint field
        self.mask_strong_bc = mask_strong_bc

        self._known_metric_forms = ['opt-goal', 'cons-visc']
        self.metric_form = 'opt-goal'

        #: float: Reference Mach number. Only needed for metric_from=`'cons-visc'`
        self.mach = -1.0

        #: float: Reference Reynolds number. Only needed for metric_from=`'cons-visc'`
        self.reynolds_number = -1.0

        #: float: Reference Temperature in Kelvin. Only needed for metric_from=`'cons-visc'`
        self.temperature = -1.0

        self.use_buffer = False

    @property
    def metric_form(self) -> str:
        """
        | The type of goal oriented metric to use in refine.
        | Options are:
        | 1. 'opt-goal' - the Euler metric
        | 2. 'cons_visc' - the viscous metric. Requires also setting the
             properties: mach, reynolds_number, and temperature

        :type: str
        """
        return self._metric_form

    @metric_form.setter
    def metric_form(self, metric: str):
        if metric not in self._known_metric_forms:
            raise ValueError('Unkown metric form for goal-oriented refine.')
        self._metric_form = metric

    def set_metric_form_opt_goal(self):
        """
        Set the type of goal oriented metric to 'opt-goal'
        """
        self.metric_form = 'opt-goal'

    def set_metric_form_cons_visc(self, mach, reynolds_number, temperature):
        """
        Set the type of goal oriented metric to cons-visc and set related
        properties.

        Parameters
        ----------
        mach: float
            The reference Mach number
        reynolds_number: float
            The reference Reynolds number
        temperature: float
            The reference temperature in Kelvin
        """
        self.metric_form = 'cons-visc'
        self.mach = mach
        self.reynolds_number = reynolds_number
        self.temperature = temperature

    def run(self, istep: int, complexity: float):
        """
        Given a primal and dual field in the form of prim_dual.solb
        and complexity, call refine to compute a goal-oriented metric and adapt.
        """
        print('Running goal-oriented refine')

        job_name = f'refine{istep:02d}'
        command_list = self._create_command_list_for_pbs_job(istep, complexity)
        self.pbs.launch(job_name, command_list)
        self._check_for_new_grid_and_solution_restart_files(istep)

    def _create_command_list_for_pbs_job(self, istep, complexity):
        current = self._create_project_rootname(istep)
        next = self._create_project_rootname(istep+1)
        volume_solb = f'{current}_volume.solb'

        command_list = []
        self._add_commands_to_shuffle_solution_solb_files(command_list, current, volume_solb)

        ref_command = self._create_goal_oriented_refine_command(istep, complexity)
        command_list.append(self.pbs.create_mpi_command(ref_command, f'refine{istep:02d}'))

        interp_command = self._create_interpolate_to_next_mesh_command(current, next, volume_solb)
        command_list.append(self.pbs.create_mpi_command(interp_command, f'refine_interp{istep:02d}'))
        return command_list

    def _check_for_new_grid_and_solution_restart_files(self, istep):
        next = self._create_project_rootname(istep+1)
        expected_file = f'{next}.lb8.ugrid'
        if not os.path.exists(expected_file):
            raise FileNotFoundError(
                f'Expected file: {expected_file} was not found. Something failed with refine when computing the next grid.')

        expected_file = f'{next}-restart.solb'
        if not os.path.exists(expected_file):
            raise FileNotFoundError(
                f'Expected file: {expected_file} was not found. Something failed with refine when computing the interpolated restart.')

    def _add_commands_to_shuffle_solution_solb_files(self, command_list: List[str],
                                                     current: str,
                                                     volume_solb: str):
        command_list.append(f'cp {volume_solb} {current}_flow.solb')
        command_list.append(f'cp prim_dual.solb {volume_solb}')

    def _create_interpolate_to_next_mesh_command(self, current, next, volume_solb):
        return f'refmpi interpolate {current}.meshb {volume_solb} {next}.meshb {next}_volume_init.solb'

    def _create_goal_oriented_refine_command(self, istep: int, complexity: float):
        current = self._create_project_rootname(istep)
        next = self._create_project_rootname(istep+1)

        command = f'refmpi loop {current} {next} {complexity}'
        command = self._add_common_ref_loop_options(command)
        command = self._add_metric_form_to_ref_loop_command(command)

        if self.mask_strong_bc:
            command += f' --mask --fun3d-mapbc {current}.mapbc'
        return command

    def _add_metric_form_to_ref_loop_command(self, command):
        if self.metric_form == 'opt-goal':
            command += ' --opt-goal'
        elif self.metric_form == 'cons-visc':
            self._check_that_cons_visc_reference_values_have_been_set()
            command += f' --cons-visc {self.mach} {self.reynolds_number} {self.temperature}'
        return command

    def _check_that_cons_visc_reference_values_have_been_set(self):
        if self.mach < 0.0:
            raise ValueError('Using cons-visc metric but mach has not been set to a physical value')
        if self.reynolds_number < 0.0:
            raise ValueError('Using cons-visc metric but reynolds_number has not been set to a physical value')
        if self.temperature < 0.0:
            raise ValueError('Using cons-visc metric but temperature has not been set to a physical value')
