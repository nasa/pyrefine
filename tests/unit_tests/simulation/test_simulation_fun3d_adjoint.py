import os
import pytest
import f90nml

from pyrefine.simulation.fun3d_adjoint import SimulationFun3dSFEAdjoint
from pyrefine import FakePBS
from pyrefine.directory_utils import cd
from pyrefine.simulation.sfe_cfg import SFEconfig

from test_simulation_fun3d import check_expected_files

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_fun3d_adjoint_files'


@pytest.fixture
def sim():
    simulation = SimulationFun3dSFEAdjoint('box', FakePBS())
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
