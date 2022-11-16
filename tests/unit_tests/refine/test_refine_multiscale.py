import pytest
from pathlib import Path
from pyrefine.shell_utils import rm

from pyrefine.refine.multiscale import RefineMultiscale, RefineMultiscaleFixedPoint
from pbs4py import PBS

project = 'sphere'


@pytest.fixture
def refine():
    return RefineMultiscale(project)


@pytest.fixture
def refine_fixedpoint():
    return RefineMultiscaleFixedPoint(project)


def test_default_multiscale_options(refine: RefineMultiscale):
    expected = ' --norm-power 4 --interpolant mach'
    assert expected == refine._create_multiscale_command_line_options()


def test_nondefault_multiscale_options(refine: RefineMultiscale):
    refine.lp_norm = 2
    refine.interpolant = 'htot'
    expected = ' --norm-power 2 --interpolant htot'
    assert expected == refine._create_multiscale_command_line_options()


def test_full_multiscale_command(refine: RefineMultiscale):
    istep = 5
    complexity = 350.0
    refine.lp_norm = 2
    refine.interpolant = 'htot'
    refine.gradation = 10.0
    refine.use_buffer = True
    expected = 'refmpi loop sphere05 sphere06 350.0 --norm-power 2 --interpolant htot --gradation 10.0 --buffer'
    assert expected == refine._create_multiscale_refine_command(istep, complexity)


def test_fixed_point_multiscale_options(refine_fixedpoint: RefineMultiscaleFixedPoint):
    start = 40
    end = 440
    freq = 3
    refine_fixedpoint.lp_norm = 5
    refine_fixedpoint.interpolant = 'htot'
    refine_fixedpoint.set_timestep_range_and_frequency(start, end, freq)
    refine_fixedpoint.sampling_data_filename_body = 'sample0_timestep'
    expected = ' --norm-power 5 --interpolant htot --fixed-point sample0_timestep 40 3 440'
    assert expected == refine_fixedpoint._create_multiscale_command_line_options()


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


def test_multiscale_run(refine: RefineMultiscale):
    istep = 5
    complexity = 350.0
    refine.lp_norm = 2
    refine.interpolant = 'htot'
    refine.gradation = 10.0
    refine.use_buffer = True

    pbs = PbsSpy()
    pbs.mpiexec = 'mpirun'
    pbs.expected_jobname = 'refine05'
    pbs.expected_commands.append(
        'mpirun refmpi loop sphere05 sphere06 350.0 --norm-power 2 --interpolant htot --gradation 10.0 --buffer &> refine05.out')
    pbs.expected_output_files = ['sphere06.meshb', 'sphere06.lb8.ugrid', 'sphere06-restart.solb']

    refine.pbs = pbs

    # run first with expected files present
    for file in pbs.expected_output_files:
        Path(file).touch()

    refine.run(istep, complexity)

    # run next with expected files not present
    for file in pbs.expected_output_files:
        rm(file)

    with pytest.raises(FileNotFoundError):
        refine.run(istep, complexity)


def test_multiscale_fixed_point_run(refine_fixedpoint: RefineMultiscaleFixedPoint):
    istep = 5
    complexity = 350.0
    refine_fixedpoint.lp_norm = 2
    refine_fixedpoint.interpolant = 'htot'
    refine_fixedpoint.gradation = 10.0
    refine_fixedpoint.use_buffer = True
    first_step = 1
    last_step = 200
    metric_freq = 50

    pbs = PbsSpy()
    pbs.mpiexec = 'mpirun'
    pbs.expected_jobname = 'refine05'
    pbs.expected_commands.append(
        'mpirun refmpi loop sphere05 sphere06 350.0 --norm-power 2 --interpolant htot --fixed-point _sampling_geom1_timestep 1 50 200 --gradation 10.0 --buffer &> refine05.out')
    pbs.expected_output_files = ['sphere06.meshb', 'sphere06.lb8.ugrid', 'sphere06-restart.solb']

    refine_fixedpoint.pbs = pbs

    # run first without setting sampling window
    with pytest.raises(ValueError):
        refine_fixedpoint.run(istep, complexity)

    for file in pbs.expected_output_files:
        Path(file).touch()

    refine_fixedpoint.set_timestep_range_and_frequency(first_step, last_step, metric_freq)
    refine_fixedpoint.run(istep, complexity)

    # run next with expected files not present
    for file in pbs.expected_output_files:
        rm(file)

    with pytest.raises(FileNotFoundError):
        refine_fixedpoint.run(istep, complexity)
