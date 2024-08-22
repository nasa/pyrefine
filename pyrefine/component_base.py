import subprocess
from typing import List

from pbs4py import PBS


class ComponentBase:
    def __init__(self, project_name: str, pbs: PBS = None):
        #: str: The root name of the project (without any mesh numbers)
        self.project_name = project_name

        #: :class:PBS: The pbs queue helper object
        self.pbs = pbs

        #: int: target number of mesh vertices per cpu core for pbs jobs
        self.vertices_per_cpu_core = None

    def get_expected_file_list(self) -> List[str]:
        """
        Tell the adaptation driver what files related to this component
        should be in the adaptation root directory

        Returns
        -------
        expected_files:
            The list of strings with the names of files. If no root directory
            files are needed by this component, return None
        """
        return []

    def _create_project_rootname(self, istep: int) -> str:
        return f"{self.project_name}{istep:02d}"

    def _get_vertex_count(self, istep: int):
        """
        Calls ref examine on the mesh to determine the number of nodes
        """
        filename = f"{self._create_project_rootname(istep)}.lb8.ugrid"
        command = ["ref", "examine", filename]
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            command_output = result.stdout

            lines = command_output.splitlines()
            for line in lines:
                if line.startswith(" 0:"):
                    parts = line.split()
                    if len(parts) > 1:
                        return int(parts[1])
            raise ValueError("Could not find a line starting with '0:'")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Cound not run ref examine on grid: {e.stderr}")
