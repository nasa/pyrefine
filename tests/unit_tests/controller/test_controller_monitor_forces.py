import pytest
import os

from pyrefine.controller.monitor_forces import ControllerMonitorForcesFUN3D, ControllerMonitorForcesSFE
from pyrefine.directory_utils import cd

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_controller_monitor_forces_files'

fv_forces_file = 'test01.forces'
sfe_log_file = 'test01_sfe.out'


@pytest.fixture
def fv_controller():
    return ControllerMonitorForcesFUN3D('test')


@pytest.fixture
def sfe_controller():
    return ControllerMonitorForcesSFE('test')


def test_fv_read_cost_function_from_forces_file(fv_controller: ControllerMonitorForcesFUN3D):

    expected_cl = 0.1320172E-06
    expected_cd = 0.8737128E-05
    expected_cy = -0.1427028E-01

    with cd(test_dir):
        assert pytest.approx(expected_cl) == fv_controller._read_cost_function_from_forces_file(fv_forces_file, 'Cl')
        assert pytest.approx(expected_cd) == fv_controller._read_cost_function_from_forces_file(fv_forces_file, 'Cd')
        assert pytest.approx(expected_cy) == fv_controller._read_cost_function_from_forces_file(fv_forces_file, 'Cy')


def test_fv_get_monitored_quantities(fv_controller: ControllerMonitorForcesFUN3D):

    istep = 1
    expected_cl = 0.1320172E-06
    expected_cd = 0.8737128E-05
    expected_cy = -0.1427028E-01
    expected_output = [expected_cd, expected_cl, expected_cy]

    with cd(test_dir):
        fv_controller.monitor_dict['Cl'] = True
        fv_controller.monitor_dict['Cd'] = True
        fv_controller.monitor_dict['Cy'] = True
        actual_output = fv_controller.get_monitored_quantities_for_step(istep)

        assert len(actual_output) == len(expected_output)
        for a, e in zip(actual_output, expected_output):
            a == pytest.approx(e)


def test_sfe_read_cost_function_from_forces_file(sfe_controller: ControllerMonitorForcesSFE):

    expected_cl = 1.3850644752e-01
    expected_cd = 5.7642936922e-02

    with cd(test_dir):
        assert pytest.approx(expected_cl) == sfe_controller._read_cost_function_from_log_file(sfe_log_file, 'CL')
        assert pytest.approx(expected_cd) == sfe_controller._read_cost_function_from_log_file(sfe_log_file, 'CD')


def test_sfe_get_monitored_quantities(sfe_controller: ControllerMonitorForcesSFE):
    istep = 1
    expected_cl = 1.3850644752e-01
    expected_cd = 5.7642936922e-02
    expected_output = [expected_cl, expected_cd]

    with cd(test_dir):
        sfe_controller.monitor_cl = True
        sfe_controller.monitor_cd = True
        actual_output = sfe_controller.get_monitored_quantities_for_step(istep)

        assert len(actual_output) == len(expected_output)
        for a, e in zip(actual_output, expected_output):
            a == pytest.approx(e)


def test_sfe_get_monitored_state(sfe_controller: ControllerMonitorForcesSFE):

    istep = 1
    expected_cl = 1.3850644752e-01
    expected_cd = 5.7642936922e-02
    expected_output = [[expected_cl, expected_cd]]

    with cd(test_dir):
        sfe_controller.monitor_cl = True
        sfe_controller.monitor_cd = True
        sfe_controller.quantity_history = []
        sfe_controller.steps_at_current_complexity = 2
        sfe_controller._get_monitored_state(istep)

        assert len(sfe_controller.quantity_history) == len(expected_output)
        for aa, ee in zip(sfe_controller.quantity_history, expected_output):
            assert len(aa) == len(ee)
            for a, e in zip(aa, ee):
                a == pytest.approx(e)
