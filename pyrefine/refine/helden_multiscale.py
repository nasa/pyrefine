from pbs4py import PBS

from pyrefine.refine.base import RefineBase


class HeldenMultiscale(RefineBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        super().__init__(project_name, pbs)

        #: str: The middle part of the filename which refine should look for the
        #: scalar on which to base the metric on. For example,
        #: bscw-box20[_sampling_geom1].solb
        # #: where the body is the part in square brackets
        #: and after the project name + adaptation cycle number (bscw-box20).
        #: The default name is "_sampling_geom1"
        self.sampling_data_filename_body = "_sampling_geom1"

        #: int or float: The lp norm value for the refine metric computation. Larger values
        #:  will target the regions of highest error more but may underresolve
        #:  lower gradient regions too much. The default value is 4.
        self.lp_norm = 4

        # ref source options

        #: float. Can be set to limit the smallest size of the mesh edges default is not to include
        self.mininum_allowed_spacing = None

        #: float: miminum distance from the wall to allow Helden sources to be added.
        #: Typically the top of the boundary layer.
        self.minimum_source_distance = None

        #: float: the wall distance limit beyond which Helden sources will not be added.
        #: Can be used to stop the adaptation closer or further from the surface than what refine's
        #: buffer will do.
        self.maximum_source_distance = None

        #: heldenmesh options.

        #: str: the heldenmesh input file where the sources will be appended. If unset, will default to "{project}.hm"
        self.heldenmesh_input_template = None

    def translate_mesh(self, istep=1):
        pass

    def get_expected_file_list(self):
        project = self._create_project_rootname(1)
        first_mesh_file = f"{project}.lb8.ugrid"
        first_mapbc_file = f"{project}.mapbc"
        helden_input_file = self._get_heldenmesh_input_file_name()
        helden_restart_file = f"{self.project_name}.rst"
        expected_files = [first_mesh_file, first_mapbc_file, helden_input_file, helden_restart_file]
        return expected_files

    def run(self, istep: int, complexity: float):
        print("Running refine and Heldenmesh")
        commands = []
        commands.append(self._get_command_to_generate_metric_file_with_ref_multiscale(istep, complexity))
        commands.append(self._get_command_to_generate_helden_sources_with_ref_source(istep))
        commands.extend(self._get_commands_to_append_sources_to_input_template(istep))
        commands.append(self._get_command_to_run_heldenmesh(istep))
        commands.append(self._get_command_to_move_heldenmesh_output_mesh_to_next_iteration_number(istep))
        commands.append(self._get_command_to_interpolate_solution_to_new_mesh(istep))
        self.pbs.launch(f"refine{istep:02}", commands)

    def _get_command_to_generate_metric_file_with_ref_multiscale(self, istep, complexity):
        project = self._create_project_rootname(istep)
        metric_scalar_file = f"{project}{self.sampling_data_filename_body}.solb"
        command = f"ref multiscale {project}.lb8.ugrid {metric_scalar_file} {complexity} metric.solb"
        command += f" --norm-power {self.lp_norm}"
        if self.use_buffer:
            command += " --buffer"
        return command

    def _get_command_to_generate_helden_sources_with_ref_source(self, istep):
        project = self._create_project_rootname(istep)
        command = f"ref_source {project}.lb8.ugrid metric.solb"

        if self.mininum_allowed_spacing is not None:
            command += f" --smin {self.mininum_allowed_spacing}"

        command = self._add_distance_flags_to_ref_source(command, istep)
        command += f" > ref_source{istep:02d}.out 2>&1"
        return command

    def _add_distance_flags_to_ref_source(self, command, istep):
        if self.maximum_source_distance is not None or self.minimum_source_distance is not None:
            project = self._create_project_rootname(istep)
            command += f" --distance {project}-distance.solb"
        if self.minimum_source_distance is not None:
            command += f" --dmin {self.minimum_source_distance}"
        if self.maximum_source_distance is not None:
            command += f" --dmax {self.maximum_source_distance}"
        return command

    def _get_commands_to_append_sources_to_input_template(self, istep):
        project = self._create_project_rootname(istep + 1)
        input_file = self._get_heldenmesh_input_file_name()
        return [f"cat {input_file} > {project}.input", f"cat hm_src.txt  >> {project}.input"]

    def _get_heldenmesh_input_file_name(self):
        return self.heldenmesh_input_template or f"{self.project_name}.hm"

    def _get_command_to_run_heldenmesh(self, istep):
        project = self._create_project_rootname(istep + 1)
        input_file = f"{project}.input"
        command = f"heldenmesh_64bit {input_file} > helden{istep+1:02d}.out 2>&1"
        return command

    def _get_command_to_move_heldenmesh_output_mesh_to_next_iteration_number(self, istep):
        project = self._create_project_rootname(istep + 1)
        return f"mv {self.project_name}.lb8.ugrid {project}.lb8.ugrid"

    def _get_command_to_interpolate_solution_to_new_mesh(self, istep):
        project = self._create_project_rootname(istep)
        next_project = self._create_project_rootname(istep + 1)
        command = f"refmpi interpolate {project}.lb8.ugrid {project}_volume.solb {next_project}.lb8.ugrid {next_project}-restart.solb"
        return self.pbs.create_mpi_command(command, f"ref_interpolate{istep:02d}")
