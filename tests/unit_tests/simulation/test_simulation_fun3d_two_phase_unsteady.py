import os
import pytest
import f90nml

from pyrefine.simulation.fun3d_two_phase_unsteady import SimulationFun3dTwoPhase, SimulationSFETwoPhase
from pbs4py import FakePBS
from pyrefine.directory_utils import cd

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_fun3d_two_phase_unsteady_files'

fv_project = 'sphere'
sfe_project = 'box'


@pytest.fixture
def fv():
    return SimulationFun3dTwoPhase(fv_project, FakePBS())


@pytest.fixture
def sfe():
    return SimulationSFETwoPhase(sfe_project, FakePBS())


def test_fv_update_transient_inputs(fv: SimulationFun3dTwoPhase):
    istep = 3
    with cd(test_dir):
        nml = f90nml.read('fun3d.nml')
        fv._update_transient_phase_inputs_in_nml(istep, nml)
        assert fv.transient_steps == 35
        assert nml['code_run_control']['steps'] == fv.transient_steps
        assert nml['global']['volume_animation_freq'] == -1


def test_fv_update_transient_inputs_with_transient_steps(fv: SimulationFun3dTwoPhase):
    istep = 3
    transient_steps = 20
    fv.transient_steps = transient_steps
    with cd(test_dir):
        nml = f90nml.read('fun3d.nml')
        fv._update_transient_phase_inputs_in_nml(istep, nml)
        assert nml['code_run_control']['steps'] == transient_steps
        assert fv.transient_steps == transient_steps
        assert nml['global']['volume_animation_freq'] == -1


def check_metric_nml_values(nml, fv: SimulationFun3dTwoPhase):
    assert nml['code_run_control']['steps'] == fv.metric_steps
    assert nml['global']['volume_animation_freq'] == fv.metric_frequency
    assert nml['code_run_control']['restart_read'] == 'on_nohistorykept'
    assert nml['volume_output_variables']['mach'] == True
    assert nml['volume_output_variables']['primitive_variables'] == False
    assert nml['volume_output_variables']['turb1'] == False


def test_fv_update_metric_inputs(fv: SimulationFun3dTwoPhase):
    istep = 3
    with cd(test_dir):
        nml = f90nml.read('fun3d.nml')
        fv._update_metric_phase_inputs_in_nml(istep, nml)
        assert fv.metric_steps == 35
        assert fv.metric_frequency == 10
        check_metric_nml_values(nml, fv)


def test_fv_update_metric_inputs_with(fv: SimulationFun3dTwoPhase):
    istep = 3
    freq = 15
    steps = 30
    with cd(test_dir):
        nml = f90nml.read('fun3d.nml')
        fv.metric_frequency = freq
        fv.metric_steps = steps
        fv._update_metric_phase_inputs_in_nml(istep, nml)
        assert fv.metric_steps == steps
        assert fv.metric_frequency == freq
        check_metric_nml_values(nml, fv)


def test_sfe_steady_cfg_filenames(sfe: SimulationSFETwoPhase):
    job_name = 'steady'
    assert '../sfe.cfg_steady' == sfe._get_template_sfe_cfg_filename(job_name)

    sfe.sfe_cfg = 'sfe.cfg1'
    assert '../sfe.cfg1' == sfe._get_template_sfe_cfg_filename(job_name)


def test_sfe_unsteady_cfg_filenames(sfe: SimulationSFETwoPhase):
    job_name = 'unsteady'
    assert '../sfe.cfg_unsteady' == sfe._get_template_sfe_cfg_filename(job_name)

    sfe.sfe_cfg_unsteady = 'sfe.cfg1'
    assert '../sfe.cfg1' == sfe._get_template_sfe_cfg_filename(job_name)


def test_sfe_steady_nml_filenames(sfe: SimulationSFETwoPhase):
    job_name = 'steady'
    assert '../fun3d.nml_steady' == sfe._get_template_fun3d_nml_filename(job_name)

    sfe.fun3d_nml = 'fun3d.nml1'
    assert '../fun3d.nml1' == sfe._get_template_fun3d_nml_filename(job_name)


def test_sfe_unsteady_nml_filenames(sfe: SimulationSFETwoPhase):
    job_name = 'unsteady'
    assert '../fun3d.nml_unsteady' == sfe._get_template_fun3d_nml_filename(job_name)

    sfe.fun3d_nml_unsteady = 'fun3d.nml1'
    assert '../fun3d.nml1' == sfe._get_template_fun3d_nml_filename(job_name)


def test_sfe_expected_file_list(sfe: SimulationSFETwoPhase):
    expected = ['fun3d.nml_steady', 'sfe.cfg_steady',
                'fun3d.nml_unsteady', 'sfe.cfg_unsteady',
                'box01.meshb', 'box01.mapbc']
    actual = sfe.get_expected_file_list()
    assert len(actual) == len(expected)
    for a in actual:
        assert a in expected
