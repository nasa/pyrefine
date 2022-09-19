from .distance_base import DistanceBase


class DistanceTinf(DistanceBase):
    """
    Computes the distance field using the ParallelDistanceCalculator from
    T-infinity
    """

    def create_distance_command(self, istep):
        grid_file = f'{self._create_project_rootname(istep)}.lb8.ugrid'
        mapbc_file = f'{self._create_project_rootname(istep)}.mapbc'
        wall_tags_string = self._get_wall_boundary_tags(mapbc_file)
        raw_command = f'ParallelDistanceCalculator {grid_file} --commas {wall_tags_string}'
        return self.pbs.create_mpi_command(raw_command, f'distance{istep:02d}')

    def _get_wall_boundary_tags(self, mapbc_file: str):
        """
        find the viscous wall (4000) boundary tags in the mapbc file

        Parameters
        ----------
        mapbc_file: str
            The mapbc file to read

        Returns
        -------
        wall_tags_string: str
            The list of wall bc tags in a string delimited by commas
        """

        wall_tags = []

        with open(mapbc_file, 'r') as fh:
            line = fh.readline()
            nbc = int(line)
            for bc in range(1, nbc+1):
                line = fh.readline()
                if '4000' in line:
                    wall_tags.append(str(bc))

        comma = ","
        wall_tags_string = comma.join(wall_tags)
        return wall_tags_string
