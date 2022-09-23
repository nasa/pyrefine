import os
import pytest
import f90nml

from pyrefine.simulation.fun3d_lfd import SimulationPapaFlutterLfd, SimulationModalFlutterLfd
from pbs4py import FakePBS
from test_simulation_fun3d import check_expected_files
from pyrefine.directory_utils import cd

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_fun3d_lfd_files'

papa_project = 'papa'
modal_project = 'modal'


@pytest.fixture
def papa():
    return SimulationPapaFlutterLfd(papa_project, FakePBS())


@pytest.fixture
def modal():
    return SimulationModalFlutterLfd(modal_project, FakePBS())


def test_papa_expected_file_list(papa: SimulationPapaFlutterLfd):
    expected = ['papa01.meshb', 'papa01.mapbc', 'fun3d.nml', 'sfe.cfg',
                'fun3d.nml_lfd', 'sfe.cfg_lfd', 'moving_body.input_lfd', 'flutter_terms.input']
    actual = papa.get_expected_file_list()
    check_expected_files(expected, actual)


def test_modal_expected_file_list(modal: SimulationModalFlutterLfd):
    expected = ['modal01.meshb', 'modal01.mapbc', 'fun3d.nml', 'sfe.cfg', 'fun3d.nml_lfd', 'sfe.cfg_lfd',
                'moving_body.input_lfd', 'flutter_terms.input', 'fun3d.nml_output_massoud', 'model.bdf', 'model.op2']
    actual = modal.get_expected_file_list()
    check_expected_files(expected, actual)


def test_papa_nml_filenames(papa: SimulationPapaFlutterLfd):
    job_name = 'steady'
    assert '../fun3d.nml' == papa._get_template_fun3d_nml_filename(job_name)
    job_name = 'lfd'
    assert f'../fun3d.nml_{job_name}' == papa._get_template_fun3d_nml_filename(job_name)


def test_modal_nml_filenames(modal: SimulationModalFlutterLfd):
    job_name = 'steady'
    assert '../fun3d.nml' == modal._get_template_fun3d_nml_filename(job_name)
    job_name = 'lfd'
    assert f'../fun3d.nml_{job_name}' == modal._get_template_fun3d_nml_filename(job_name)
    job_name = 'output_massoud'
    assert f'../fun3d.nml_{job_name}' == modal._get_template_fun3d_nml_filename(job_name)


def test_sfe_cfg_filenames(papa: SimulationPapaFlutterLfd):
    job_name = 'steady'
    assert '../sfe.cfg' == papa._get_template_sfe_cfg_filename(job_name)
    job_name = 'lfd'
    assert f'../sfe.cfg_{job_name}' == papa._get_template_sfe_cfg_filename(job_name)


def test_moving_body_filenames(papa: SimulationPapaFlutterLfd):
    job_name = 'steady'
    assert '../moving_body.input' == papa._get_template_moving_body_filename(job_name)
    job_name = 'lfd'
    assert f'../moving_body.input_{job_name}' == papa._get_template_moving_body_filename(job_name)


def test_simulation_nodet(papa: SimulationPapaFlutterLfd):
    job_name = 'steady'
    assert 'nodet_mpi' == papa._get_simulation_nodet(job_name)
    job_name = 'lfd'
    assert 'complex_nodet_mpi' == papa._get_simulation_nodet(job_name)


def test_papa_simulation_command_line_args(papa: SimulationPapaFlutterLfd):
    job_name = 'steady'
    assert ' --write_massoud_file' == papa._get_simulation_specific_fun3d_command_line_args_str(job_name)
    job_name = 'lfd'
    assert ' --aeroelastic_internal' == papa._get_simulation_specific_fun3d_command_line_args_str(job_name)


def test_modal_simulation_command_line_args(modal: SimulationModalFlutterLfd):
    job_name = 'steady'
    assert ' --aeroelastic_internal' == modal._get_simulation_specific_fun3d_command_line_args_str(job_name)
    job_name = 'lfd'
    assert ' --aeroelastic_internal' == modal._get_simulation_specific_fun3d_command_line_args_str(job_name)
    job_name = 'output_massoud'
    assert ' --write_massoud_file' == modal._get_simulation_specific_fun3d_command_line_args_str(job_name)


def test_papa_steady_fun3d_nml_fields(papa: SimulationPapaFlutterLfd):
    with cd(test_dir):
        istep = 4
        job_name = 'steady'
        nml = f90nml.read(papa.fun3d_nml)
        papa._update_fun3d_nml_fields(istep, job_name, nml)

        f = open('aoa.txt', 'r')
        aoa = float(f.read().splitlines()[0])
        f.close()

        assert aoa == nml['reference_physical_properties']['angle_of_attack']
        assert 'papa04-restart.solb' == nml['flow_initialization']['import_from']


def test_papa_lfd_fun3d_nml_fields(papa: SimulationPapaFlutterLfd):
    with cd(test_dir):
        istep = 4
        job_name = 'lfd'
        nml = f90nml.read(papa.fun3d_nml)
        papa._update_fun3d_nml_fields(istep, job_name, nml)

        f = open('aoa.txt', 'r')
        aoa = float(f.read().splitlines()[0])
        f.close()

        assert aoa == nml['reference_physical_properties']['angle_of_attack']
        assert not nml['flow_initialization']['import_from']


def test_modal_fun3d_nml_fields(modal: SimulationModalFlutterLfd):
    with cd(test_dir):
        istep = 4

        job_name = 'steady'
        nml = f90nml.read(modal.fun3d_nml)
        modal._update_fun3d_nml_fields(istep, job_name, nml)
        assert 'modal04-restart.solb' == nml['flow_initialization']['import_from']

        job_name = 'lfd'
        nml = f90nml.read(modal.fun3d_nml)
        modal._update_fun3d_nml_fields(istep, job_name, nml)
        assert not nml['flow_initialization']['import_from']

        job_name = 'output_massoud'
        nml = f90nml.read(modal.fun3d_nml)
        modal._update_fun3d_nml_fields(istep, job_name, nml)
        assert not nml['flow_initialization']['import_from']
