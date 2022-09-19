from typing import List
from pbs4py import PBS
from pyrefine.component_base import ComponentBase
from pyrefine.shell_utils import rm


class ControllerBase(ComponentBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        Driver for the complexity controller and updating any other inputs

        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper

        """
        #: str: The root name of the project (without any mesh numbers)
        self.project_name = project_name

        #: :class:PBS: The pbs queue helper object
        self.pbs = pbs

        #: float: Complexity at iteration 1 of the adaptation cycle
        self.initial_complexity = 1000.0

        #: int: How often to save a meshb and -restart.solb file for restarting.
        self.restart_save_frequency = None

        #: bool: Set to True to keep all files (no clean up operations).
        self.save_all = False

        #: List[str]: extensions of files to remove at the end of each adaptation cycle
        #             if save_all is True
        self.file_extensions_to_cleanup_every_step = [".lb8.ugrid", "-distance.solb", ".flow",
                                                      "-mach.solb", "-metric.solb", "_volume*.solb",
                                                      "-prim-adj.solb", ]

        #: List[str]: extensions of files to remove at the end of each adaptation cycle except for
        #             steps that are multiples of restart_save_frequency.
        self.file_extensions_to_save_only_on_restart_iterations = [".meshb", "-restart.solb"]

    def set_file_extensions_to_cleanup_every_step(self, extensions: List[str]):
        """
        If left unchecked, the directories growing quickly during the adaptation
        process. The basic controller will delete some intermediate files
        to reduce directory size. The list of file extensions to be deleted  at
        the end of each adaptation cycle can be customized with this function.

        The cleanup functionality can be turned off with
        :func:`~controller_basic.ControllerBase.save_all`

        Parameters
        ----------
        extensions:
            list of strings representing the end of the file names, e.g.
            for `rm {project_name}*.txt {project_name}*.dat`, set extensions=['.txt', '.dat']
        """
        self.file_extensions_to_cleanup_every_step = extensions

    def set_file_extensions_to_save_only_on_restart_iterations(self, extensions: List[str]):
        """
        If left unchecked, the directories growing quickly during the adaptation
        process. The basic controller will delete some intermediate files
        to reduce directory size. File extensions set with this method will be
        deleted at the end of adaptation cycle except restart steps as
        determined by :attr:`~controller_base.ControllerBase.restart_save_frequency`.
        The default extensions are [".meshb", "-restart.solb"]

        The cleanup functionality can be turned off with
        :attr:`~controller_basic.ControllerBase.save_all`

        Parameters
        ----------
        extensions:
            list of strings representing the end of the file names, e.g.
            for `rm {project}*.txt {project}*.dat`, set extensions=['.txt', '.dat']
        """
        self.file_extensions_to_save_only_on_restart_iterations = extensions

    def cleanup(self, istep: int):
        """
        Clean up files at the end of the adaptation cycle
        """
        if self.save_all:
            return

        project = self._create_project_rootname(istep)
        cleanup_extensions = self._form_cleanup_extension_list_for_step(istep)
        for ext in cleanup_extensions:
            rm(f'{project}*{ext}')

    def update_inputs(self, istep: int):
        """
        Update any input files for the given adaptation cycle
        """
        pass

    def compute_complexity(self, istep: int, current_complexity: float) -> float:
        """
        Compute the complexity for the upcoming adaptation cycle, istep.

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
        raise NotImplementedError('controllers must implement a complexity calculation')

    def check_for_early_stop_condition(self, istep: int) -> bool:
        """
        Check whether some condition has been met to stop the adaptation cycle
        loop but not raise an exception to kill python altogether

        Parameters
        ----------
        istep:
            Adaptation step number

        Returns
        -------
        early_stop:
        """
        return False

    def _form_cleanup_extension_list_for_step(self, istep: int) -> List[str]:
        cleanup_extensions = self.file_extensions_to_cleanup_every_step.copy()

        if not self._save_restart_files_on_this_step(istep):
            cleanup_extensions.extend(self.file_extensions_to_save_only_on_restart_iterations)
        return cleanup_extensions

    def _save_restart_files_on_this_step(self, istep: int) -> bool:
        if self.restart_save_frequency is not None:
            return (istep % self.restart_save_frequency == 0)
        return True
