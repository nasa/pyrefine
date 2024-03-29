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
        return f'{self.project_name}{istep:02d}'
