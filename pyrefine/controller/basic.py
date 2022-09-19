from .base import ControllerBase
from pbs4py import PBS


class ControllerBasic(ControllerBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        Multiplies the complexity every :attr:`~steps_per_complexity` steps by a fixed factor,
        :attr:`~complexity_multiplier`. The default behavior is to double
        the complexity every 5 steps.

        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int: The number of meshes per complexity. The default value is 5.
        self.steps_per_complexity = 5

        #: float: the multiplier applied to the complexity when the complexity needs to be updated.
        #:  The default value is 2.0.
        self.complexity_multiplier = 2.0

    def save_restart_files_this_step(self, istep: int) -> bool:
        if self.restart_save_frequency is not None:
            save_freq = self.restart_save_frequency
        else:
            save_freq = self.steps_per_complexity
        return (istep % save_freq == 0)

    def compute_complexity(self, istep: int, current_complexity: float) -> float:
        """
        Basic complexity schedule that will double the value after n iterations

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
        complexity = (self.initial_complexity *
                      self.complexity_multiplier ** ((istep - 1) // self.steps_per_complexity))
        print("Complexity:", complexity)
        return complexity
