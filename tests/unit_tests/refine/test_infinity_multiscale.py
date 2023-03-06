import pytest

from pyrefine.refine.tinfinity_multiscale import TinfinityMultiscale
from pbs4py import PBS

project = 'om6ste'


@pytest.fixture
def infinity():
    pbs = PBS()
    pbs.mpiexec = 'mpiexec'
    return TinfinityMultiscale(project, pbs=pbs, field_file_extensions=['_sample1.solb'])


@pytest.fixture
def infinity_csv():
    pbs = PBS()
    pbs.mpiexec = 'mpiexec'
    return TinfinityMultiscale(project, pbs=pbs, field_file_extensions=['_sample1.csv'])


@pytest.fixture
def infinity_two_field():
    pbs = PBS()
    pbs.mpiexec = 'mpiexec'
    return TinfinityMultiscale(project, pbs=pbs, field_file_extensions=['_sample1.csv', '_sample3.csv'])


def test_csv_to_snap_command(infinity_csv: TinfinityMultiscale):
    istep = 2
    field = '_sample1.csv'
    command = infinity_csv._create_csv_to_snap_command(istep, field)
    expected = 'mpiexec inf csv-to-snap --file om6ste02_sample1.csv -o om6ste02_sample1.snap &> om6ste02_sample1_csv_to_snap.out'
    assert command == expected


def test_solb_to_snap_command(infinity: TinfinityMultiscale):
    istep = 2
    field = '_sampling_geom1.solb'
    command = infinity._create_solb_to_snap_command(istep, field)
    expected = 'mpiexec inf plot --mesh om6ste02.meshb --snap om6ste02_sampling_geom1.solb -o om6ste02_sampling_geom1.snap &> om6ste02_sampling_geom1_solb_to_snap.out'
    assert command == expected


def test_create_multiscale_metric_command_csv(infinity_csv: TinfinityMultiscale):
    istep = 3
    complexity = 15000
    field = '_sample2.csv'
    command = infinity_csv._create_multiscale_metric_command(istep, complexity, field)
    expected = 'mpiexec inf metric --mesh om6ste03.lb8.ugrid --snap om6ste03_sample2.snap -o om6ste03_sample2_metric.snap --target-node-count 30000 &> om6ste03_sample2_metric.out'
    assert command == expected


def test_create_multiscale_metric_command(infinity: TinfinityMultiscale):
    istep = 3
    complexity = 15000
    field = '_sample2.solb'
    command = infinity._create_multiscale_metric_command(istep, complexity, field)
    expected = 'mpiexec inf metric --mesh om6ste03.lb8.ugrid --snap om6ste03_sample2.snap -o om6ste03_sample2_metric.snap --target-node-count 30000 &> om6ste03_sample2_metric.out'
    assert command == expected


def test_create_multiscale_intersect_command(infinity_two_field: TinfinityMultiscale):
    istep = 2
    command = infinity_two_field._create_metric_intersect_command(istep)
    expected = 'mpiexec inf metric --mesh om6ste02.lb8.ugrid --metrics om6ste02_sample1_metric.snap om6ste02_sample3_metric.snap -o om6ste02_combined_metric.snap --intersect &> om6ste02_intersect_metric.out'
    assert command == expected


def test_create_adapt_command_one_field(infinity: TinfinityMultiscale):
    istep = 2
    command = infinity._create_adapt_command(istep)
    expected = 'mpiexec inf adapt --mesh om6ste02.meshb --metric om6ste02_sample1_metric.snap -o om6ste03.meshb &> om6ste02_adapt.out'
    assert command == expected


def test_create_adapt_command_two_field(infinity_two_field: TinfinityMultiscale):
    istep = 2
    command = infinity_two_field._create_adapt_command(istep)
    expected = 'mpiexec inf adapt --mesh om6ste02.meshb --metric om6ste02_combined_metric.snap -o om6ste03.meshb &> om6ste02_adapt.out'
    assert command == expected


def test_create_interpolate_solution_command(infinity: TinfinityMultiscale):
    istep = 3
    command = infinity._create_interpolate_solution_command(istep)
    expected = 'mpiexec inf interpolate --source om6ste03.meshb --target om6ste04.meshb --snap om6ste03_volume.solb -o om6ste04-restart.solb &> om6ste03_interpolate.out'
    assert command == expected


class PbsSpy(PBS):
    def __init__(self, profile_filename=''):
        self.expected_commands = []
        self.expected_jobname = ''
        self.expected_output_files = []
        super().__init__(profile_file=profile_filename)

    def launch(self, job_name, job_body) -> str:
        assert job_name == self.expected_jobname
        assert len(job_body) == len(self.expected_commands)
        for expected, command in zip(self.expected_commands, job_body):
            assert expected == command
