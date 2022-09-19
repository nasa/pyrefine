import numpy as np
import f90nml

from .base import ControllerBase
from pbs4py import PBS


class ControllerAoaSweep(ControllerBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        A controller to perform an angle of attack sweep.
        There are two phases to the process. A fixed angle of attack phase
        where the complexity is (potentially) increases on a fixed schedule.
        Multiple complexity phases can occur per angle of attack.
        An angle of attack adjustment phase occurs between fixed angle of attack
        phases. In the adjustment phase, complexity is held fixed while the
        problem is incremented to the next angle of attack.

        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int: At a fixed aoa, the number of adaptation cycles before increasing the complexity
        self.steps_per_complexity_at_aoa = 5

        #: float: The multiplicative factor to mutiple the complexity by
        self.complexity_multiplier = 2.0

        #: int: The number of complexity levels at each angle of attack
        self.complexity_levels_per_aoa = 2

        #: int: The number of adaptation cycles used to transition to the next angle of attack step
        self.steps_per_aoa_transition = 5

        #: float: The angle of attack step size at which analyze. (transition moves between step_size)
        self.aoa_step_size = 1.0

        #: float: Initial angle of attack in degrees
        self.initial_aoa = 0.0

        #: list[str]: The list of fun3d namelist files to adjust the angle of attack in
        self.fun3d_nml_list = ['fun3d.nml']

    def update_inputs(self, istep):
        """
        Update the angle of attack based on the schedule
        """
        aoa = self._compute_angle_of_attack(istep)
        self._set_angle_of_attack_in_fun3d_nmls(aoa)

    def _set_angle_of_attack_in_fun3d_nmls(self, aoa):
        for nml_file in self.fun3d_nml_list:
            nml = f90nml.read(f'../{nml_file}')
            nml['reference_physical_properties']['angle_of_attack'] = aoa
            nml.write(f'../{nml_file}', force=True)

    def _compute_phase_info(self, istep):
        steps_per_aoa = (self.steps_per_complexity_at_aoa * self.complexity_levels_per_aoa
                         + self.steps_per_aoa_transition)

        step_within_phase = istep % steps_per_aoa
        phase = (istep - step_within_phase) // steps_per_aoa
        return phase, step_within_phase

    def _compute_angle_of_attack(self, istep):
        phase, step_within_phase = self._compute_phase_info(istep)

        base_aoa = self.initial_aoa + phase * self.aoa_step_size

        transition_step = step_within_phase - self.steps_per_complexity_at_aoa * self.complexity_levels_per_aoa
        aoa_sweep = np.linspace(0.0, self.aoa_step_size, num=self.steps_per_aoa_transition+1)
        transition_aoa = aoa_sweep[transition_step] if transition_step > 0 else 0

        return base_aoa + transition_aoa

    def compute_complexity(self, istep: int, current_complexity: float) -> float:
        """

        Parameters
        ----------
        istep:
            Adaptation step number
        current_complexity:
            The current complexity in the driver. If doing a restart, the current
            complexity will be `None`

        Returns
        -------
        complexity:
        """
        complexity_phase = self._compute_complexity_phase(istep)
        complexity = self.initial_complexity * self.complexity_multiplier**(complexity_phase)

        print("Complexity:", complexity)
        return complexity

    def _compute_complexity_phase(self, istep: int) -> int:
        phase, local_step = self._compute_phase_info(istep)

        if self._in_aoa_adjustment_phase(local_step):
            local_step = self._floor_step_to_end_of_last_const_aoa_phase()

        return (phase * self.complexity_levels_per_aoa +
                (local_step - 1) // self.steps_per_complexity_at_aoa)

    def _in_aoa_adjustment_phase(self, local_step: int) -> bool:
        return local_step > self.steps_per_complexity_at_aoa * self.complexity_levels_per_aoa

    def _floor_step_to_end_of_last_const_aoa_phase(self) -> int:
        return self.steps_per_complexity_at_aoa * self.complexity_levels_per_aoa
