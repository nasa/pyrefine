import numpy as np
import ast
from typing import List

from .base import ControllerBase
from pbs4py import PBS


class ControllerMonitorQuantity(ControllerBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        A controller to double the complexity of the adaptation based on the
        convergence of some quantity(s) of interest like lift or drag.

        To monitor a quantity, you should subclass and implement the
        :func:`~get_monitored_quantities_for_step` method.


        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int: The maximum number of steps to take per complexity level if
        #:   the monitored quantities do not converge
        self.maximum_steps_per_complexity = 20

        #: float: The relative tolerance used in monitoring the convergence of
        #:   the quantities of interest
        self.relative_tolerance = 0.01

        #: float: the multiplier applied to the complexity when the complexity needs to be updated.
        #:  The default value is 2.0.
        self.complexity_multiplier = 2.0

    def compute_complexity(self, istep: int, current_complexity: float) -> float:
        """
        Compute the complexity for the upcoming step based in the convergence
        or one of more integrated quantities

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
        if self._first_call_of_a_new_run(istep):
            current_complexity = self.initial_complexity
            self._reset_monitored_state()
            return current_complexity

        if self._beginning_of_a_restart(current_complexity):
            current_complexity = self._read_controller_restart_state()
        else:
            self._get_monitored_state(istep-1)

        self._save_controller_state(current_complexity)

        if self._complexity_should_be_increased():
            current_complexity *= self.complexity_multiplier
            self._reset_monitored_state()

        print("Complexity:", current_complexity)
        return current_complexity

    def _first_call_of_a_new_run(self, istep: int) -> bool:
        # note: controller called with istep+1 at the end of step 1 in order to set complexity for next adaptation cycle
        return istep == 2

    def _beginning_of_a_restart(self, current_complexity):
        return current_complexity is None

    def _complexity_should_be_increased(self):
        if self._taken_minimum_number_of_steps_at_complexity(self.steps_at_current_complexity):
            if self._reached_max_steps_at_complexity_level(self.steps_at_current_complexity):
                print('Reached maximum number of steps at current complexity. Increasing complexity')
                return True
            elif self._monitored_quantities_are_converged(self.quantity_history):
                print('Monitored quantities converged. Increasing complexity')
                return True
        return False

    def _reset_monitored_state(self):
        self.steps_at_current_complexity = 0
        self.quantity_history = []

    def _get_monitored_state(self, istep: int):
        self.quantity_history.append(self.get_monitored_quantities_for_step(istep))
        self.steps_at_current_complexity += 1

    def _taken_minimum_number_of_steps_at_complexity(self, steps_at_current_complexity: int):
        return steps_at_current_complexity > 3

    def _reached_max_steps_at_complexity_level(self, steps_at_current_complexity: int):
        return steps_at_current_complexity > self.maximum_steps_per_complexity

    def _monitored_quantities_are_converged(self, quantity_history):
        """
        Two previous steps are within the relative tolerance of the current step
        """
        array = np.array(quantity_history)
        normalized_differences = np.abs((array[-3:-1, :] - array[-1, :]) / array[-1, :])
        return np.all(normalized_differences < self.relative_tolerance)

    def _save_controller_state(self, current_complexity, output_filename='controller_state.txt'):
        state = {'current_complexity': current_complexity,
                 'steps_at_current_complexity': self.steps_at_current_complexity,
                 'quantity_history': self.quantity_history}
        with open(output_filename, 'w') as f:
            f.write(str(state))
            f.write('\n')

    def _read_controller_restart_state(self, restart_file='controller_state.txt'):
        try:
            with open(restart_file, 'r') as f:
                state = ast.literal_eval(f.read())
            current_complexity = state['current_complexity']
            self.steps_at_current_complexity = state['steps_at_current_complexity']
            self.quantity_history = state['quantity_history']
        except:
            raise RuntimeError('Unable to read previous controller state during restart')
        return current_complexity

    def get_monitored_quantities_for_step(self, istep: int) -> List[float]:
        """
        function to extract list of quantities to be monitored from the
        simulation corresponding to adaptation cycle `istep`.

        Parameters
        ----------
        istep:
            Adaptation step number

        Returns
        -------
        quantities:
            Variables to be monitored
        """
        raise NotImplementedError('monitoring controllers must implement method to get monitored_quantities for step')
