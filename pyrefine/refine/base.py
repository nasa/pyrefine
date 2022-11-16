import os
from typing import List

from pyrefine.component_base import ComponentBase
from pbs4py import PBS
from .uniform_region import UniformRegionBase


class RefineBase(ComponentBase):
    def __init__(self, project_name: str, pbs: PBS = None):

        #: str: The root name of the project (without any mesh numbers)
        self.project_name = project_name

        #: :class:PBS: The pbs queue helper object
        self.pbs = pbs

        # refine options
        #: int or float: Refine input that controls the amount of smoothing applied
        #:               to the metric field. The default value is -1.
        self.gradation = -1

        #: int or float: Refine input acts as an upper bound of element aspect ratio.
        #: The default value of -1 does not limit the aspect ratio, otherwise
        #: the value must be greater than or equal to 1.
        self.aspect_ratio = -1

        #: bool: Set extrude_2d_mesh_to_3d flag to True when using a 2D mesh of
        #: triangles that needs to be extruded to a single layer of prisms.
        self.extrude_2d_mesh_to_3d = False

        #: bool: Create a buffer region of gradually coarsening the mesh as it approaches
        #        the X-extent outer boundary.
        self.use_buffer = True

        #: bool: Use K-exact least-squares reconstruction.
        self.use_kexact = False

        #: bool: Use the deforming option in refine for meshes where coordinates in the
        #: simulation are different from the original mesh
        self.use_deforming = False

        #: None or int: The number of sweeps for refine. If None, use the refine default
        self.number_of_sweeps = None

        #: list: uniform refinement regions to be applied :class:`~pyrefine.refine.uniform_region.UniformRegionBase`:
        self.uniform_regions: List[UniformRegionBase] = []

    def translate_mesh(self):
        """
        Convert the first meshb file into a ugrid file
        """
        print("Converting first mesh")
        ugrid_file = self._create_first_ugrid_filename()
        command = self._create_translate_command(ugrid_file)

        os.system(command)
        if not os.path.isfile(ugrid_file):
            raise FileNotFoundError(f'Expected file: {ugrid_file} was not found. Failure in refine translate.')

    def _create_translate_command(self, ugrid_file: str):
        project = self._create_project_rootname(istep=1)
        first_mesh_file = f'{project}.meshb'
        command = f'ref translate {first_mesh_file} {ugrid_file}'
        if self.extrude_2d_mesh_to_3d:
            command += " --extrude"
        return command

    def _create_first_ugrid_filename(self) -> str:
        project = self._create_project_rootname(istep=1)
        return f'{project}.lb8.ugrid'

    def run(self, istep: int, complexity: float):
        """
        Compute the metric, generates the mesh, and interpolates the solution to the new mesh
        """
        raise NotImplementedError('Refine classes must implement the run method')

    def _add_aspect_ratio_to_ref_loop_command(self, command: str) -> str:
        if self.aspect_ratio >= (1 - 1e-7):
            return command + f' --aspect-ratio {self.aspect_ratio}'
        else:
            return command

    def _add_gradation_to_ref_loop_command(self, command: str) -> str:
        return command + f' --gradation {self.gradation}'

    def _add_uniform_refinement_regions_command(self, command: str) -> str:
        for region in self.uniform_regions:
            command += region.get_commandline_arguments()
        return command

    def _add_common_ref_loop_options(self, command: str) -> str:
        command = self._add_aspect_ratio_to_ref_loop_command(command)
        command = self._add_gradation_to_ref_loop_command(command)
        command = self._add_uniform_refinement_regions_command(command)
        if self.use_buffer:
            command += ' --buffer'
        if self.use_kexact:
            command += ' --kexact'
        if self.use_deforming:
            command += ' --deforming'
        if self.number_of_sweeps is not None:
            command += f' -s {self.number_of_sweeps}'
        return command
