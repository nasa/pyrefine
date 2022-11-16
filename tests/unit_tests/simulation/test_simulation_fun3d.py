import os
import pytest
import f90nml

from pyrefine.simulation.fun3d import SimulationFun3dFV, SimulationFun3dSFE
from pbs4py import FakePBS
from pyrefine.directory_utils import cd

from test_distance import refine_expected_dist_command, distance_test_dir

fv_project = 'sphere'
sfe_project = 'box'

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_fun3d_files'


@pytest.fixture
def fv():
    return SimulationFun3dFV(fv_project, FakePBS())


@pytest.fixture
def sfe():
    return SimulationFun3dSFE(sfe_project, FakePBS())


def check_expected_files(expected, actual):
    assert len(expected) == len(actual)
    for e in expected:
        assert e in actual


def clean_up_files(files):
    for file in files:
        os.system(f'rm {file}')


def check_files_exist(files):
    for file in files:
        assert os.path.isfile(file)


def test_fv_expected_file_list(fv: SimulationFun3dFV):
    expected = ['sphere01.meshb', 'sphere01.mapbc', 'fun3d.nml']
    actual = fv.get_expected_file_list()
    check_expected_files(expected, actual)


def test_fv_expected_file_list_with_moving_body(fv: SimulationFun3dFV):
    expected = ['sphere01.meshb', 'sphere01.mapbc', 'fun3d.nml', 'moving_body.input']
    fv.expect_moving_body_input = True
    actual = fv.get_expected_file_list()
    check_expected_files(expected, actual)


def test_create_fun3d_command(fv: SimulationFun3dFV):
    istep = 3
    expected = 'mpiexec nodet_mpi &> flow03.out'
    assert expected == fv._create_fun3d_command(istep)


def test_create_fun3d_command_with_clo(fv: SimulationFun3dFV):
    istep = 4
    fv.fun3d_command_line_args = '--gamma 1.0'
    expected = 'mpiexec nodet_mpi --gamma 1.0 &> flow04.out'
    assert expected == fv._create_fun3d_command(istep)


def test_fun3d_command_with_alternative_output_name(fv: SimulationFun3dFV):
    istep = 8
    expected = 'mpiexec nodet_mpi &> static08.out'
    assert expected == fv._create_fun3d_command(istep, job_name='static')


def test_sfe_expected_file_list(sfe: SimulationFun3dSFE):
    expected = ['box01.meshb', 'box01.mapbc', 'fun3d.nml', 'sfe.cfg']
    actual = sfe.get_expected_file_list()
    check_expected_files(expected, actual)


def test_distance_command(fv: SimulationFun3dFV):
    istep = 3
    fv.project_name = 'test'
    with cd(distance_test_dir):
        assert refine_expected_dist_command == fv._create_distance_command(istep)


def test_fv_command_list(fv: SimulationFun3dFV):
    istep = 3
    job_name = 'flow'
    fv.project_name = 'test'
    expected = [refine_expected_dist_command,
                'mpiexec nodet_mpi &> flow03.out']

    with cd(distance_test_dir):
        commands = fv._create_list_of_commands_to_run(istep, job_name)

    assert len(expected) == len(commands)
    for c, e in zip(commands, expected):
        assert c == e


def test_fv_command_list_no_external_distance(fv: SimulationFun3dFV):
    istep = 4
    job_name = 'flow'
    fv.project_name = 'test'
    fv.external_wall_distance = False
    expected = ['mpiexec nodet_mpi &> flow04.out']

    with cd(distance_test_dir):
        commands = fv._create_list_of_commands_to_run(istep, job_name)

    assert len(expected) == len(commands)
    for c, e in zip(commands, expected):
        assert c == e


def test_fv_command_list_skip_external_distance(fv: SimulationFun3dFV):
    istep = 4
    job_name = 'flow'
    fv.project_name = 'test'
    fv.external_wall_distance = True
    expected = ['mpiexec nodet_mpi &> flow04.out']

    with cd(distance_test_dir):
        commands = fv._create_list_of_commands_to_run(istep, job_name, skip_external_distance=True)

    assert len(expected) == len(commands)
    for c, e in zip(commands, expected):
        assert c == e


def test_check_for_distance_file(fv: SimulationFun3dFV):
    with cd(test_dir):
        istep = 2
        expected_file = 'sphere02-distance.solb'
        os.system(f'touch {expected_file}')
        fv._check_for_distance_file(istep)
        os.system(f'rm {expected_file}')
        with pytest.raises(FileNotFoundError):
            fv._check_for_distance_file(istep)


def test_check_for_solb_file(fv: SimulationFun3dFV):
    with cd(test_dir):
        istep = 3
        expected_file = 'sphere03_volume.solb'
        os.system(f'touch {expected_file}')
        fv._check_for_volume_solb(istep)
        os.system(f'rm {expected_file}')
        with pytest.raises(FileNotFoundError):
            fv._check_for_volume_solb(istep)


def test_read_restart_solb(fv: SimulationFun3dFV):
    fv.import_solution_from_previous_mesh = True

    assert not fv._read_restart_solb(1)
    assert fv._read_restart_solb(2)
    assert fv._read_restart_solb(3)

    fv.import_solution_from_previous_mesh = False
    assert not fv._read_restart_solb(1)


def test_fv_save_a_copy_of_inputs(fv: SimulationFun3dFV):
    with cd(test_dir):
        istep = 4
        job_name = 'flow'

        expected_outputs = ['fun3d.nml_flow04']
        clean_up_files(expected_outputs)
        fv._save_a_copy_of_solver_inputs(istep, job_name)
        check_files_exist(expected_outputs)
        clean_up_files(expected_outputs)


def test_fv_save_a_copy_of_inputs_with_moving(fv: SimulationFun3dFV):
    with cd(test_dir):
        istep = 5
        job_name = 'flow'
        fv.expect_moving_body_input = True

        expected_outputs = ['fun3d.nml_flow05', 'moving_body.input_flow05']
        clean_up_files(expected_outputs)
        fv._save_a_copy_of_solver_inputs(istep, job_name)
        check_files_exist(expected_outputs)
        clean_up_files(expected_outputs)


def test_sfe_save_a_copy_of_inputs(sfe: SimulationFun3dSFE):
    with cd(test_dir):
        istep = 4
        job_name = 'flow'

        expected_outputs = ['fun3d.nml_flow04', 'sfe.cfg_flow04']
        clean_up_files(expected_outputs)
        sfe._save_a_copy_of_solver_inputs(istep, job_name)
        check_files_exist(expected_outputs)
        clean_up_files(expected_outputs)


def test_sfe_save_a_copy_of_inputs_with_moving(sfe: SimulationFun3dSFE):
    with cd(test_dir):
        istep = 4
        job_name = 'adjoint'

        expected_outputs = ['fun3d.nml_adjoint04', 'sfe.cfg_adjoint04', 'moving_body.input_adjoint04']
        sfe.expect_moving_body_input = True
        clean_up_files(expected_outputs)
        sfe._save_a_copy_of_solver_inputs(istep, job_name)
        check_files_exist(expected_outputs)
        clean_up_files(expected_outputs)


def test_update_openmp_inputs(fv: SimulationFun3dFV):
    with cd(test_dir):
        nml = f90nml.read(fv.fun3d_nml)
        fv._set_openmp_inputs_in_nml(nml, omp_threads=3)
        assert nml['code_run_control']['use_openmp']
        assert nml['code_run_control']['grid_coloring']

        fv._set_openmp_inputs_in_nml(nml, omp_threads=None)
        assert not nml['code_run_control']['use_openmp']
        assert not nml['code_run_control']['grid_coloring']


def test_set_distance_from_file_in_nml(fv: SimulationFun3dFV):
    with cd(test_dir):
        nml = f90nml.read(fv.fun3d_nml)

        istep = 4
        expected = 'sphere04-distance.solb'
        fv._set_distance_from_file_in_nml(istep, nml)
        assert expected == nml['special_parameters']['distance_from_file']


def test_set_import_from_in_nml(fv: SimulationFun3dFV):
    with cd(test_dir):
        nml = f90nml.read(fv.fun3d_nml)

        istep = 9
        expected = 'sphere09-restart.solb'
        fv._set_import_from_in_nml(istep, nml)
        assert expected == nml['flow_initialization']['import_from']


def test_set_project_rootname_in_nml(fv: SimulationFun3dFV):
    with cd(test_dir):
        nml = f90nml.read(fv.fun3d_nml)

        istep = 3
        expected = 'sphere03'
        fv._set_project_rootname_in_nml(istep, nml)
        assert expected == nml['project']['project_rootname']


def test_get_fun3d_nml_filename(fv: SimulationFun3dFV):
    assert '../fun3d.nml' == fv._get_template_fun3d_nml_filename('flow')


def test_get_alternate_fun3d_nml_filename(fv: SimulationFun3dFV):
    fv.fun3d_nml = 'fun3d.nml_alt'
    assert '../fun3d.nml_alt' == fv._get_template_fun3d_nml_filename('flow')


def test_get_sfe_cfg_name(sfe: SimulationFun3dSFE):
    job_name = 'flow'
    assert '../sfe.cfg' == sfe._get_template_sfe_cfg_filename(job_name)

    sfe.sfe_cfg = 'sfe.cfg_alt'
    assert '../sfe.cfg_alt' == sfe._get_template_sfe_cfg_filename(job_name)


def test_get_moving_body_input_name(fv: SimulationFun3dFV):
    job_name = 'flow'
    assert '../moving_body.input' == fv._get_template_moving_body_filename(job_name)

    fv.moving_body_input = 'moving_body.input_alt'
    assert '../moving_body.input_alt' == fv._get_template_moving_body_filename(job_name)
