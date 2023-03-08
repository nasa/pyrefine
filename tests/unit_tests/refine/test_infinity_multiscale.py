import pytest

from pbs4py import PBS, FakePBS
from pyrefine.refine.tinfinity_multiscale import TinfinityMultiscale
from pyrefine.shell_utils import rm

project = 'om6ste'


@pytest.fixture
def infinity():
    pbs = FakePBS()
    pbs.mpiexec = 'mpiexec'
    return TinfinityMultiscale(project, pbs=pbs, field_file_extensions=['_sample_geom1.solb'])


@pytest.fixture
def infinity_csv():
    pbs = FakePBS()
    pbs.mpiexec = 'mpiexec'
    return TinfinityMultiscale(project, pbs=pbs, field_file_extensions=['_sample1.csv'])


@pytest.fixture
def infinity_two_field():
    pbs = FakePBS()
    pbs.mpiexec = 'mpiexec'
    return TinfinityMultiscale(project, pbs=pbs, field_file_extensions=['_sample_geom1.solb', '_sample_geom3.solb'])


def test_csv_to_snap_command(infinity_csv: TinfinityMultiscale):
    istep = 2
    field = '_sample1.csv'
    command = infinity_csv._create_csv_to_snap_command(istep, field)
    expected = 'mpiexec inf csv-to-snap --file om6ste02_sample1.csv -o om6ste02_sample1.snap &> om6ste02_sample1_csv_to_snap.out'
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
    expected = 'mpiexec inf metric --mesh om6ste03.lb8.ugrid --snap om6ste03_sample2.solb -o om6ste03_sample2_metric.snap --target-node-count 30000 &> om6ste03_sample2_metric.out'
    assert command == expected


def test_create_multiscale_intersect_command(infinity_two_field: TinfinityMultiscale):
    istep = 2
    command = infinity_two_field._create_metric_intersect_command(istep)
    expected = 'mpiexec inf metric --mesh om6ste02.lb8.ugrid --metrics om6ste02_sample_geom1_metric.snap om6ste02_sample_geom3_metric.snap -o om6ste02_combined_metric.snap --intersect &> om6ste02_intersect_metric.out'
    assert command == expected


def test_create_adapt_command_one_field(infinity: TinfinityMultiscale):
    istep = 2
    command = infinity._create_adapt_command(istep)
    expected = 'mpiexec inf adapt --mesh om6ste02.meshb --metric om6ste02_sample_geom1_metric.snap -o om6ste03.meshb &> om6ste02_adapt.out'
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


def test_check_for_ugrid_with_no_file(infinity: TinfinityMultiscale):
    istep = 1
    with pytest.raises(FileNotFoundError):
        infinity._check_for_ugrid_mesh_file(istep)


def test_check_for_meshb_with_no_file(infinity: TinfinityMultiscale):
    istep = 1
    with pytest.raises(FileNotFoundError):
        infinity._check_for_meshb_file(istep)


def test_check_for_restart_file_with_no_file(infinity: TinfinityMultiscale):
    istep = 1
    with pytest.raises(FileNotFoundError):
        infinity._check_for_flow_restart_file(istep)


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
        for filename in self.expected_output_files:
            open(filename, 'a').close()

    def clean_up_files(self):
        for filename in self.expected_output_files:
            rm(filename)


def test_multiscale_run(infinity_two_field: TinfinityMultiscale):
    istep = 5
    complexity = 350.0

    pbs = PbsSpy()
    pbs.mpiexec = 'mpirun'
    pbs.expected_jobname = 'infinity05'
    pbs.expected_commands = [
        'inf extensions --load adaptation',
        'mpirun inf metric --mesh om6ste05.lb8.ugrid --snap om6ste05_sample_geom1.solb -o om6ste05_sample_geom1_metric.snap --target-node-count 700.0 &> om6ste05_sample_geom1_metric.out',
        'mpirun inf metric --mesh om6ste05.lb8.ugrid --snap om6ste05_sample_geom3.solb -o om6ste05_sample_geom3_metric.snap --target-node-count 700.0 &> om6ste05_sample_geom3_metric.out',
        'mpirun inf metric --mesh om6ste05.lb8.ugrid --metrics om6ste05_sample_geom1_metric.snap om6ste05_sample_geom3_metric.snap -o om6ste05_combined_metric.snap --intersect &> om6ste05_intersect_metric.out',
        'mpirun inf adapt --mesh om6ste05.meshb --metric om6ste05_combined_metric.snap -o om6ste06.meshb &> om6ste05_adapt.out',
        'mpirun inf interpolate --source om6ste05.meshb --target om6ste06.meshb --snap om6ste05_volume.solb -o om6ste06-restart.solb &> om6ste05_interpolate.out',
        'ref translate om6ste06.meshb om6ste06.lb8.ugrid']
    pbs.expected_output_files = ['om6ste06.meshb', 'om6ste06.lb8.ugrid', 'om6ste06-restart.solb']
    infinity_two_field.pbs = pbs
    infinity_two_field.run(istep, complexity)

    pbs.clean_up_files()
