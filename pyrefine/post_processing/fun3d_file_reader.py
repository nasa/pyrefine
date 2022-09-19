import numpy as np
from pathlib import Path
from typing import List

from .tecplot_writer import write_data_to_tecplot_format
from .post_processing_command import PostProcessingCommand
from pyrefine.shell_utils import grep, tail


class Fun3dAdaptationSteadyHistoryReader:
    def __init__(self, data_directory: str, project_rootname: str, number_of_meshes: int = -1):
        """
        Class for post-processing an adaptation run with FUN3D.

        Parameters
        ----------
        data_directory:
            Location where the history files are

        project_rootname:
            base name of project (without mesh number)

        number_of_meshes:
            number of meshes to read. If left as the default value of -1, the number of meshes
            will be counted based on the files found in the ``data_directory``
        """
        self.data_directory = data_directory
        self.project_rootname = project_rootname

        self.commands: List[PostProcessingCommand] = []

        #: int: number of meshes that were read
        self.number_of_meshes = 0

        #: np.ndarray: number of nodes in each mesh
        self.number_of_nodes = np.zeros(0)

        #: dict: history of values. Key is the variable name. Value is the numpy array with the history of that variable.
        self.final_hist_values = {}

        if self.data_directory != '' and project_rootname != '':
            self._read_data(number_of_meshes)

    def _read_data(self, number_of_meshes=0):
        if number_of_meshes > 0:
            self.number_of_meshes = number_of_meshes
        else:
            self.number_of_meshes = self._count_number_of_meshes()
        self.number_of_nodes = self._read_number_of_nodes_for_all_meshes()
        self.final_hist_values = self._read_final_line_of_hist_file_for_all_meshes()

        self.execute_commands()

    def execute_commands(self):
        """
        Iterate through user-specified commands

        The reader class is the invoker for the command design pattern
        """
        for command in self.commands:
            command.execute()

    def register_command(self, command: PostProcessingCommand):
        """
        Add a command to the post-processing list

        The reader class is the invoker for the command design pattern

        Parameters
        ----------
        command :
            A post-processing command to be added to the list.  These
            commands will be executed in a first-in, first-out sequence.

        Raises
        ======
        ValueError:
            Raises a value error if the command is not a valid
            PostProcessingCommand
        """
        if isinstance(command, PostProcessingCommand):
            self.commands.append(command)
        else:
            raise ValueError("The command must be a subclass of PostProcessingCommand")

    def _read_number_of_nodes_for_all_meshes(self) -> np.ndarray:
        number_of_nodes = np.zeros(self.number_of_meshes)
        for imesh in range(1, self.number_of_meshes+1):
            filepath = Path(f'{self.data_directory}/{self.project_rootname}{imesh:02}.grid_info')
            if filepath.exists():
                print(filepath)
                number_of_nodes[imesh-1] = self._read_number_of_nodes_from_grid_info(filepath)
            else:
                filepath = Path(f'{self.data_directory}/{self.project_rootname}{imesh:02}_flow_out')
                number_of_nodes[imesh-1] = self._read_number_of_nodes_from_flow_out(filepath)
        return number_of_nodes

    def _read_number_of_nodes_from_grid_info(self, file: str):
        node_line = grep('number of nodes', file, head=1)[0]
        return int(node_line.split(':')[-1])

    def _read_number_of_nodes_from_flow_out(self, file: str):
        with open(file, 'r') as infile:
            for line in infile.readlines():
                if 'nnodes' in line:
                    nnodes = int(line.split()[-1])
                    break
            else:
                raise RuntimeError(f"Did not find nnodes in {file}")
        return nnodes

    def _count_number_of_meshes(self):
        base_path = Path(self.data_directory)
        grid_info_files = list(base_path.glob(f'{self.project_rootname}*.grid_info'))
        flow_out_files = list(base_path.glob(f'{self.project_rootname}*flow_out'))
        if len(grid_info_files) == 0 and len(flow_out_files) == 0:
            raise RuntimeError(f"Could not find grid_info or flow_out files in {self.data_directory}")

        mesh_num = 1
        while (base_path / f'{self.project_rootname}{mesh_num:02}.grid_info').exists():
            mesh_num += 1

        # Try to recover if grid info files were irregular
        if mesh_num == 1:
            while (base_path / f'{self.project_rootname}{mesh_num:02}_flow_out').exists():
                mesh_num += 1
        return mesh_num - 1

    def _read_final_line_of_hist_file_for_all_meshes(self) -> dict:
        hist_data = {}
        for imesh in range(1, self.number_of_meshes+1):
            project = f'{self.project_rootname}{imesh:02}'
            file = f'{self.data_directory}/{project}_hist.dat'
            if imesh == 1:
                variable_names = self._read_hist_variable_names(file)
                for var in variable_names:
                    hist_data[var] = np.zeros(self.number_of_meshes, dtype=float)
            final_line = tail(file, n=1)[0]
            values = final_line.split()
            for ivar, var in enumerate(variable_names):
                hist_data[var][imesh-1] = float(values[ivar])
        return hist_data

    def _read_hist_variable_names(self, hist_file: str):
        variable_line = grep('VARIABLES', hist_file)[0]
        variables_string = variable_line.split("=")[-1]
        variables = variables_string.split('" "')
        for ivar in range(len(variables)):
            variables[ivar] = variables[ivar].replace('"', '').strip()
        return variables

    def write_data_to_tec(self, filename: str):
        """
        Write the history information to a tecplot file

        Parameters
        ----------
        filename
        """
        title = f'{self.project_rootname}_adapt_hist'
        zone = f'{self.project_rootname}'

        data = np.zeros((self.number_of_meshes, len(self.final_hist_values)+1))
        data[:, 0] = self.number_of_nodes
        variables = ['Number of Nodes']
        for ivar, (var, var_data) in enumerate(self.final_hist_values.items()):
            variables.append(var)
            data[:, ivar+1] = var_data
        write_data_to_tecplot_format(filename, title, data, variables, zone)

    def write_data_to_csv(self, filename: str):
        """
        Write the history information to a csv file

        Parameters
        ----------
        filename
        """
        data = np.zeros((self.number_of_meshes, len(self.final_hist_values)+1))
        data[:, 0] = self.number_of_nodes
        variables = ['Number of Nodes']
        for ivar, (var, var_data) in enumerate(self.final_hist_values.items()):
            variables.append(var)
            data[:, ivar+1] = var_data
        header = "\"" + ('\",\"').join(variables) + "\""
        np.savetxt(filename, data, header=header, comments='', delimiter=",")
