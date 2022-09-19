from typing import List
from .monitor_quantity import ControllerMonitorQuantity
from pyrefine.shell_utils import grep


class ControllerMonitorForcesFUN3D(ControllerMonitorQuantity):
    def __init__(self, project_name, pbs=None,
                 monitor_cd=True, monitor_cl=False,
                 monitor_cmx=False, monitor_cmy=False, monitor_cmz=False,
                 monitor_cx=False, monitor_cy=False, monitor_cz=False):
        """
        A controller to double the complexity of the adaptation based on the
        convergence of one or more integrated loads from the FUN3D forces file.

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        monitor_cd: bool
            Whether to monitor the drag coefficient
        monitor_cl: bool
            Whether to monitor the lift coefficient
        monitor_cmx: bool
            Whether to monitor the x-moment coefficient
        monitor_cmy: bool
            Whether to monitor the y-moment coefficient
        monitor_cmz: bool
            Whether to monitor the z-moment coefficient
        monitor_cx: bool
            Whether to monitor the x force coefficient
        monitor_cy: bool
            Whether to monitor the y force coefficient
        monitor_cz: bool
            Whether to monitor the z force coefficient
        """
        super().__init__(project_name, pbs)
        self.monitor_dict = {}
        self.monitor_dict['Cd'] = monitor_cd
        self.monitor_dict['Cl'] = monitor_cl
        self.monitor_dict['Cmx'] = monitor_cmx
        self.monitor_dict['Cmy'] = monitor_cmy
        self.monitor_dict['Cmz'] = monitor_cmz
        self.monitor_dict['Cx'] = monitor_cx
        self.monitor_dict['Cy'] = monitor_cy
        self.monitor_dict['Cz'] = monitor_cz

    def get_monitored_quantities_for_step(self, istep):
        """
        function to extract list of quantities to be monitored from the
        simulation corresponding to adaptation cycle `istep`.

        Parameters
        ----------
        istep: int
            Adaptation step number

        Returns
        -------
        quantities: list of floats
            Variables to be monitored
        """
        forces_file = f'{self._create_project_rootname(istep)}.forces'
        values = [self._read_cost_function_from_forces_file(forces_file, key)
                  for key, value in self.monitor_dict.items() if value]
        return values

    def _read_cost_function_from_forces_file(self, forces_file, cost_function_name):
        regex_scientific_number = '-*[0-9].[0-9]+[Ee]\+*-*[0-9][0-9]'
        regex_for_cost_function_name_and_value = f'{cost_function_name}[ ]*=[ ]*{regex_scientific_number}'
        cost_function_string = grep(regex_for_cost_function_name_and_value, forces_file, tail=1, match_only=True)
        return float(cost_function_string[0].split("=")[-1])


class ControllerMonitorForcesSFE(ControllerMonitorQuantity):
    def __init__(self, project_name, pbs=None, monitor_cd=True, monitor_cl=False):
        """
        A controller to double the complexity of the adaptation based on the
        convergence of CD and/or CL for SFE. SFE computes its own forces
        based on FE integration over the surface, but doesn't write a separate
        force file, so we pull the CD and CL from the simulation log file

        Parameters
        ----------
        project_name: str
            The root name of the project (without any mesh numbers)
        pbs: :class:PBS
            PBS queue helper
        monitor_cd: bool
            Whether to monitor the drag coefficient
        monitor_cl: bool
            Whether to monitor the lift coefficient
        """
        super().__init__(project_name, pbs)
        self.monitor_cd = monitor_cd
        self.monitor_cl = monitor_cl

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
        project = self._create_project_rootname(istep)
        log_file = f'{project}_sfe.out'
        values = []
        if self.monitor_cl:
            values.append(self._read_cost_function_from_log_file(log_file, 'CL'))
        if self.monitor_cd:
            values.append(self._read_cost_function_from_log_file(log_file, 'CD'))
        return values

    def _read_cost_function_from_log_file(self, log_file, cost_function_name):
        regex_scientific_number = '-*[0-9].[0-9]+[Ee]\+*-*[0-9][0-9]'
        regex_for_cost_function_name_and_value = f'{cost_function_name}[ ]*=[ ]*{regex_scientific_number}'
        cost_function_string = grep(regex_for_cost_function_name_and_value, log_file, tail=1, match_only=True)
        return float(cost_function_string[0].split("=")[-1])
