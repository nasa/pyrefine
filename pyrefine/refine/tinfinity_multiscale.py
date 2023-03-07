import os
from pbs4py import PBS

from .base import RefineBase


class TinfinityMultiscale(RefineBase):
    def __init__(
            self, project_name: str, pbs: PBS = None, solution_file_extension='_volume.solb',
            field_file_extensions=['_sampling_geom1.solb']):
        super().__init__(project_name, pbs)
        self.field_file_extensions = field_file_extensions
        self.solution_file_extension = solution_file_extension

    def run(self, istep: int, complexity: float):
        print('Running t-infinity adapt step')
        self._run_tinfinity(istep, complexity)

    def _run_tinfinity(self, istep: int, complexity: float):

        commands = ['inf extensions --load adaptation']
        for field in self.field_file_extensions:
            if self._using_csv_file(field):
                commands.append(self._create_csv_to_snap_command(istep, field))
            commands.append(self._create_multiscale_metric_command(istep, complexity, field))

        if self._have_multiple_fields():
            commands.append(self._create_metric_intersect_command(istep))

        commands.append(self._create_adapt_command(istep))
        commands.append(self._create_interpolate_solution_command(istep))

        ugrid_file = self._get_ugrid_mesh_filename(istep+1)
        commands.append(self._create_translate_command(ugrid_file, istep+1))

        job_name = f'infinity{istep:02d}'
        self.pbs.launch(job_name, commands)
        self._check_for_expected_output_files(istep)

    def _using_csv_file(self, field):
        return 'csv' in field

    def _using_solb_file(self, field):
        return 'solb' in field

    def _check_for_expected_output_files(self, istep):
        self._check_for_ugrid_mesh_file(istep+1)
        self._check_for_meshb_file(istep+1)
        self._check_for_flow_restart_file(istep+1)

    def _check_for_ugrid_mesh_file(self, istep):
        expected_file = self._get_ugrid_mesh_filename(istep)
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(
                f'Expected file: {expected_file} was not found. Something failed with t-infinity')

    def _check_for_meshb_file(self, istep):
        expected_file = self._get_meshb_filename(istep)
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(
                f'Expected file: {expected_file} was not found. Something failed with t-infinity')

    def _check_for_flow_restart_file(self, istep):
        expected_file = self._get_restart_solb_filename(istep)
        if not os.path.isfile(expected_file):
            raise FileNotFoundError(
                f'Expected file: {expected_file} was not found. Something failed with t-infinity')

    def _create_csv_to_snap_command(self, istep: int, field: str):
        project_root = self._create_project_rootname(istep)
        field_root = self._get_field_root_name_from_field_ext(field)
        flow_output_file = f'{project_root}{field}'
        snap_file = self._get_flow_field_snap_filename(istep, field)
        raw_command = f'inf csv-to-snap --file {flow_output_file} -o {snap_file}'
        return self.pbs.create_mpi_command(raw_command, f'{project_root}{field_root}_csv_to_snap')

    def _create_multiscale_metric_command(self, istep: int, complexity: float, field: str):
        mesh_file = self._get_ugrid_mesh_filename(istep)
        snap_file = self._get_flow_field_snap_filename(istep, field)
        metric_snap = self._get_metric_snap_filename(istep, field)
        raw_command = f'inf metric --mesh {mesh_file} --snap {snap_file} -o {metric_snap} --target-node-count {2*complexity}'

        project_root = self._create_project_rootname(istep)
        field_root = self._get_field_root_name_from_field_ext(field)
        return self.pbs.create_mpi_command(raw_command, f'{project_root}{field_root}_metric')

    def _create_metric_intersect_command(self, istep):
        mesh_file = self._get_ugrid_mesh_filename(istep)

        field_snap_files = []
        for field in self.field_file_extensions:
            field_snap_files.append(self._get_metric_snap_filename(istep, field))
        field_metric_snaps = ' '.join(field_snap_files)

        out_snap = self._get_combined_metric_snap_filename(istep)
        raw_command = f'inf metric --mesh {mesh_file} --metrics {field_metric_snaps} -o {out_snap} --intersect'

        project_root = self._create_project_rootname(istep)
        return self.pbs.create_mpi_command(raw_command, f'{project_root}_intersect_metric')

    def _create_adapt_command(self, istep: int) -> str:
        this_mesh = self._get_meshb_filename(istep)
        next_mesh = self._get_meshb_filename(istep+1)

        if self._have_multiple_fields():
            metric_snap = self._get_combined_metric_snap_filename(istep)
        else:
            metric_snap = self._get_first_metric_snap_filename(istep)

        raw_command = f'inf adapt --mesh {this_mesh} --metric {metric_snap} -o {next_mesh}'

        project_root = self._create_project_rootname(istep)
        return self.pbs.create_mpi_command(raw_command, f'{project_root}_adapt')

    def _create_interpolate_solution_command(self, istep):
        this_mesh = self._get_meshb_filename(istep)
        next_mesh = self._get_meshb_filename(istep+1)

        volume_solution = f'{self._create_project_rootname(istep)}{self.solution_file_extension}'
        next_restart = self._get_restart_solb_filename(istep+1)

        # TODO add --fields {fields}?
        raw_command = f'inf interpolate --source {this_mesh} --target {next_mesh} --snap {volume_solution} -o {next_restart}'

        project_root = self._create_project_rootname(istep)
        return self.pbs.create_mpi_command(raw_command, f'{project_root}_interpolate')

    def _get_flow_field_snap_filename(self, istep: int, field: str) -> str:
        field_root = self._get_field_root_name_from_field_ext(field)
        if self._using_solb_file(field):
            return f'{self._create_project_rootname(istep)}{field_root}.solb'
        else:
            return f'{self._create_project_rootname(istep)}{field_root}.snap'

    def _get_metric_snap_filename(self, istep: int, field: str) -> str:
        field_root = self._get_field_root_name_from_field_ext(field)
        return f'{self._create_project_rootname(istep)}{field_root}_metric.snap'

    def _get_field_root_name_from_field_ext(self, field: str) -> str:
        return field.split('.')[0]

    def _get_meshb_filename(self, istep: int):
        return f'{self._create_project_rootname(istep)}.meshb'

    def _get_combined_metric_snap_filename(self, istep: int):
        return f'{self._create_project_rootname(istep)}_combined_metric.snap'

    def _get_first_metric_snap_filename(self, istep: int):
        field_root = self._get_field_root_name_from_field_ext(self.field_file_extensions[0])
        return self._get_metric_snap_filename(istep, field_root)

    def _have_multiple_fields(self) -> bool:
        return len(self.field_file_extensions) > 1

    def _get_restart_solb_filename(self, istep):
        return f'{self._create_project_rootname(istep)}-restart.solb'
