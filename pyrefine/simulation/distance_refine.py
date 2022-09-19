from .distance_base import DistanceBase


class DistanceRefine(DistanceBase):
    """
    Computes the distance field using the Refine distance calculator

    Parameters
    ----------
    project_name: str
        The root name of the project (without any mesh numbers)
    pbs: :class:PBS
        PBS queue helper
    """
    def create_distance_command(self, istep: int) -> str:
        project = self._create_project_rootname(istep)
        grid_file = f'{project}.lb8.ugrid'
        mapbc_file = f'{project}.mapbc'
        distance_file = self.create_distance_filename(istep)
        raw_command =  f'refmpi distance {grid_file} {distance_file} --fun3d {mapbc_file}'
        return self.pbs.create_mpi_command(raw_command, f'distance{istep:02d}')
