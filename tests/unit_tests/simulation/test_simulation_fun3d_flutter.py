import pytest
from pyrefine.simulation.fun3d_flutter import SimulationFlutterFV
from pbs4py import FakePBS
from test_simulation_fun3d import check_expected_files


@pytest.fixture
def fv():
    return SimulationFlutterFV('box', FakePBS())


def test_expected_file_list(fv: SimulationFlutterFV):
    expected = ['box01.meshb', 'box01.mapbc',
                'fun3d.nml_fixed',
                'fun3d.nml_static', 'moving_body.input_static',
                'fun3d.nml_dynamic', 'moving_body.input_dynamic']
    actual = fv.get_expected_file_list()
    check_expected_files(expected, actual)


def test_fixed_simulation_command_line_args(fv: SimulationFlutterFV):
    job_name = 'fixed'
    expected = ' --write_massoud_file'
    assert expected == fv._get_simulation_specific_fun3d_command_line_args_str(job_name)


def test_static_simulation_command_line_args(fv: SimulationFlutterFV):
    job_name = 'static'
    expected = ' --aeroelastic_internal'
    assert expected == fv._get_simulation_specific_fun3d_command_line_args_str(job_name)


def test_dynamic_simulation_command_line_args(fv: SimulationFlutterFV):
    job_name = 'dynamic'
    expected = ' --aeroelastic_internal'
    assert expected == fv._get_simulation_specific_fun3d_command_line_args_str(job_name)


def test_fun3d_nml_filenames(fv: SimulationFlutterFV):
    for job_name in ['fixed', 'static', 'dynamic']:
        assert f'../fun3d.nml_{job_name}' == fv._get_template_fun3d_nml_filename(job_name)


def test_fun3d_nml_alternate_filenames(fv: SimulationFlutterFV):
    fv.fun3d_nml_fixed = 'fun3d.nml_fixed2'
    fv.fun3d_nml_static = 'fun3d.nml_static2'
    fv.fun3d_nml_dynamic = 'fun3d.nml_dynamic2'
    for job_name in ['fixed', 'static', 'dynamic']:
        assert f'../fun3d.nml_{job_name}2' == fv._get_template_fun3d_nml_filename(job_name)


def test_moving_body_filenames(fv: SimulationFlutterFV):
    for job_name in ['static', 'dynamic']:
        assert f'../moving_body.input_{job_name}' == fv._get_template_moving_body_filename(job_name)


def test_moving_body_alternate_filenames(fv: SimulationFlutterFV):
    fv.moving_body_input_static = 'moving_body.input_static2'
    fv.moving_body_input_dynamic = 'moving_body.input_dynamic2'
    for job_name in ['static', 'dynamic']:
        assert f'../moving_body.input_{job_name}2' == fv._get_template_moving_body_filename(job_name)


def test_project_mode_shape_default(fv: SimulationFlutterFV):
    istep = 2
    with pytest.raises(NotImplementedError):
        fv._project_mode_shapes(istep)
