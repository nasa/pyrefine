from pyrefine.component_base import ComponentBase


class DistanceBase(ComponentBase):
    """
    Calculator for the distance field
    """

    def create_distance_command(self, istep: int) -> str:
        """
        Create a string with the distance command
        """
        return ''

    def create_distance_filename(self, istep: int) -> str:
        project = self._create_project_rootname(istep)
        return f'{project}-distance.solb'
