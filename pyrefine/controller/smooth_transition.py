from .base import ControllerBase
from pbs4py import PBS


class ControllerSmoothTransition(ControllerBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        A controller to smoothly transition between complexity levels
        instead of increasing the complexity by complexity_multiplier
        over a single adaptation cycle.
        This smoother transition can help maintain solver robustness on cases
        where flow features like shocks may move as the mesh refines.

        An example of the complexity schedule with the default parameters of
        ``steps_per_complexity=5``, ``complexity_multiplier=2``,
        and ``steps_per_transition = 4``:
        the first 5 steps will have the initial complexity.
        Over the next 4 steps, the complexity will gradually increase.
        For step 10, the complexity will be double the initial complexity.
        This pattern of 5 fixed complexity steps and doubling over 4 transition
        steps will continue until the adaptation is stopped.

        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int: The number of meshes at constant complexity.
        self.steps_per_complexity = 5

        #: float: The multiplicative factor to mutiple the complexity by
        self.complexity_multiplier = 2.0

        #: int: The number of meshes used to transition to the next complexity
        self.steps_per_transition = 4

    def _compute_phase_step_info(self, istep):
        steps_per_phase = self.steps_per_complexity + self.steps_per_transition

        # starting at 1
        step_within_phase = (istep-1) % steps_per_phase + 1
        phase = (istep - step_within_phase) // steps_per_phase
        return phase, step_within_phase

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
        exponent, phase, local_step, transition_step = self._compute_complexity_phase(istep)
        complexity = self.initial_complexity * self.complexity_multiplier**(exponent)

        if local_step <= self.steps_per_complexity:
            print(f'Complexity: {complexity} level: {phase}, refinement step: {local_step} of {self.steps_per_complexity}')
        else:
            print(
                f'Complexity: {complexity} level: {phase}, transition step: {transition_step} of {self.steps_per_transition}')

        return complexity

    def _compute_complexity_phase(self, istep):
        phase, local_step = self._compute_phase_step_info(istep)

        if self._in_transition(local_step):
            transition_step = local_step - self.steps_per_complexity
        else:
            transition_step = 0

        exponent = phase + transition_step / (self.steps_per_transition+1)
        return exponent, phase, local_step, transition_step

    def _in_transition(self, local_step):
        return local_step > self.steps_per_complexity
