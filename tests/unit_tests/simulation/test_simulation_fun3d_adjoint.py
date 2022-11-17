import os
import pytest
from pathlib import Path
from pyrefine.shell_utils import rm
import f90nml

from pyrefine.simulation.fun3d_adjoint import SimulationFun3dSFEAdjoint
from pbs4py import FakePBS, PBS
from pyrefine.directory_utils import cd
from pyrefine.simulation.sfe_cfg import SFEconfig

from test_simulation_fun3d import check_expected_files

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_fun3d_adjoint_files'


@pytest.fixture
def sim():
    simulation = SimulationFun3dSFEAdjoint('box', pbs=FakePBS(), fwd_omp_threads=2, adj_omp_threads=8)
    return simulation


def test_expected_file_list(sim: SimulationFun3dSFEAdjoint):
    expected = ['box01.meshb', 'box01.mapbc',
                'fun3d.nml_forward', 'sfe.cfg_forward',
                'fun3d.nml_adjoint', 'sfe.cfg_adjoint']
    actual = sim.get_expected_file_list()
    check_expected_files(expected, actual)


def test_check_for_prim_dual_solb(sim: SimulationFun3dSFEAdjoint):
    with cd(test_dir):
        istep = 2
        expected_file = 'prim_dual.solb'
        os.system(f'touch {expected_file}')
        sim._check_for_prim_dual_solb()
        os.system(f'rm {expected_file}')
        with pytest.raises(FileNotFoundError):
            sim._check_for_prim_dual_solb()


def test_set_nml_to_not_write_restart_file(sim: SimulationFun3dSFEAdjoint):
    with cd(test_dir):
        nml = f90nml.read(sim.fun3d_nml_adjoint)
        sim._set_nml_to_not_write_restart_file(nml)
        assert nml['code_run_control']['no_restart']


def test_update_sfe_cfg_files_for_adjoint(sim: SimulationFun3dSFEAdjoint):
    sfe_cfg = SFEconfig()

    sim._update_sfe_cfg_fields_for_adjoint(1, sfe_cfg)
    assert 'import_adjoint_from' not in sfe_cfg

    sim.import_adjoint_from_previous_mesh = False
    sim._update_sfe_cfg_fields_for_adjoint(2, sfe_cfg)
    assert 'import_adjoint_from' not in sfe_cfg

    sim.import_adjoint_from_previous_mesh = True
    sim._update_sfe_cfg_fields_for_adjoint(2, sfe_cfg)
    assert sfe_cfg['import_adjoint_from'] == 'box02_volume_init.solb'


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


class SimulationFun3dSFEAdjointNoInputFiles(SimulationFun3dSFEAdjoint):
    def _prepare_input_files(self, istep: int, job_name: str):
        pass

    def _save_a_copy_of_solver_inputs(self, istep, job_name):
        pass


@pytest.fixture
def sim_no_input_files():
    simulation = SimulationFun3dSFEAdjointNoInputFiles(
        'box', pbs=FakePBS(),
        fwd_omp_threads=2, adj_omp_threads=20, external_wall_distance=False)
    return simulation


def test_fun3d_forward_command(sim_no_input_files: SimulationFun3dSFEAdjointNoInputFiles):

    pbs = PbsSpy()
    pbs.mpiexec = 'mpirun'
    pbs.expected_jobname = 'forward05'
    pbs.expected_commands.append(
        'OMP_NUM_THREADS=2 OMP_PLACES=cores OMP_PROC_BIND=close mpirun -np 20 nodet_mpi &> forward05.out')
    pbs.expected_output_files = ['box05_volume.solb', 'box05-distance.solb']

    sim_no_input_files.pbs = pbs

    step = 5

    # run first with expected files present
    for file in pbs.expected_output_files:
        Path(file).touch()

    sim_no_input_files._run_forward_simulation(step)

    # run next with expected files not present
    for file in pbs.expected_output_files:
        rm(file)

    with pytest.raises(FileNotFoundError):
        sim_no_input_files._run_forward_simulation(step)


def test_fun3d_adjoint_command(sim_no_input_files: SimulationFun3dSFEAdjointNoInputFiles):

    pbs = PbsSpy()
    pbs.mpiexec = 'mpirun'
    pbs.expected_jobname = 'adjoint05'
    pbs.expected_commands.append(
        'OMP_NUM_THREADS=20 OMP_PLACES=cores OMP_PROC_BIND=close mpirun -np 2 nodet_mpi &> adjoint05.out')
    pbs.expected_output_files = ['prim_dual.solb']

    sim_no_input_files.pbs = pbs

    step = 5

    # run first with expected files present
    for file in pbs.expected_output_files:
        Path(file).touch()

    sim_no_input_files._run_adjoint_simulation(step)

    # run next with expected files not present
    for file in pbs.expected_output_files:
        rm(file)

    with pytest.raises(FileNotFoundError):
        sim_no_input_files._run_adjoint_simulation(step)
