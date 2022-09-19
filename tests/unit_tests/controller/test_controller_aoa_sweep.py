import pytest
import f90nml
import os

from pyrefine.directory_utils import cd
from pyrefine.controller.aoa_sweep import ControllerAoaSweep

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_controller_aoa_sweep_files'


@pytest.fixture
def controller():
    controller = ControllerAoaSweep('test', pbs=None)
    controller.steps_per_complexity_at_aoa = 5
    controller.complexity_multiplier = 2.0
    controller.complexity_levels_per_aoa = 2
    controller.steps_per_aoa_transition = 4
    controller.aoa_step_size = 2.0
    controller.initial_aoa = 1.0
    return controller


def test_compute_phase_step_info(controller: ControllerAoaSweep):
    for step in range(1, 3*14):
        phase, step_within_phase = controller._compute_phase_info(step)
        if step < 14:
            assert phase == 0
            assert step_within_phase == step
        elif step < 2*14:
            assert phase == 1
            assert step_within_phase == step - 14
        else:
            assert phase == 2
            assert step_within_phase == step - 14*2


def test_compute_aoa_and_complexity(controller: ControllerAoaSweep):
    initial_complexity = controller.initial_complexity
    complexity = initial_complexity

    for step in range(1, 38):
        aoa = controller._compute_angle_of_attack(step)
        complexity = controller.compute_complexity(step, complexity)
        if step <= 5:
            assert aoa == pytest.approx(1.0)
            assert complexity == pytest.approx(initial_complexity)
        elif step <= 10:
            assert aoa == pytest.approx(1.0)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 11:
            assert aoa == pytest.approx(1.5)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 12:
            assert aoa == pytest.approx(2.0)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 13:
            assert aoa == pytest.approx(2.5)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 14:
            assert aoa == pytest.approx(3.0)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step <= 14+5:
            assert aoa == pytest.approx(3.0)
            assert complexity == pytest.approx(initial_complexity * 4)
        elif step <= 14+5+5:
            assert aoa == pytest.approx(3.0)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+1:
            assert aoa == pytest.approx(3.5)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+2:
            assert aoa == pytest.approx(4.0)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+3:
            assert aoa == pytest.approx(4.5)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+4:
            assert aoa == pytest.approx(5.0)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step <= 24+4+5:
            assert aoa == pytest.approx(5.0)
            assert complexity == pytest.approx(initial_complexity * 16)
        elif step <= 24+4+10:
            assert aoa == pytest.approx(5.0)
            assert complexity == pytest.approx(initial_complexity * 32)


def test_compute_aoa_and_complexity_negative_step_size(controller: ControllerAoaSweep):
    initial_complexity = controller.initial_complexity
    complexity = initial_complexity
    controller.aoa_step_size = -2.0

    for step in range(1, 38):
        aoa = controller._compute_angle_of_attack(step)
        complexity = controller.compute_complexity(step, complexity)
        if step <= 5:
            assert aoa == pytest.approx(1.0)
            assert complexity == pytest.approx(initial_complexity)
        elif step <= 10:
            assert aoa == pytest.approx(1.0)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 11:
            assert aoa == pytest.approx(0.5)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 12:
            assert aoa == pytest.approx(0.0)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 13:
            assert aoa == pytest.approx(-0.5)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step == 14:
            assert aoa == pytest.approx(-1.0)
            assert complexity == pytest.approx(initial_complexity * 2)
        elif step <= 14+5:
            assert aoa == pytest.approx(-1.0)
            assert complexity == pytest.approx(initial_complexity * 4)
        elif step <= 14+5+5:
            assert aoa == pytest.approx(-1.0)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+1:
            assert aoa == pytest.approx(-1.5)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+2:
            assert aoa == pytest.approx(-2.0)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+3:
            assert aoa == pytest.approx(-2.5)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step == 24+4:
            assert aoa == pytest.approx(-3.0)
            assert complexity == pytest.approx(initial_complexity * 8)
        elif step <= 24+4+5:
            assert aoa == pytest.approx(-3.0)
            assert complexity == pytest.approx(initial_complexity * 16)
        elif step <= 24+4+10:
            assert aoa == pytest.approx(-3.0)
            assert complexity == pytest.approx(initial_complexity * 32)


def test_update_aoa_in_nml(controller: ControllerAoaSweep):
    with cd(f'{test_dir}/Flow'):
        nml_list = ['fun3d.nml_forward', 'fun3d.nml_adjoint']
        controller.fun3d_nml_list = nml_list

        aoa = 3.0
        controller._set_angle_of_attack_in_fun3d_nmls(aoa)
        for nml_file in nml_list:
            nml = f90nml.read(f'../{nml_file}')
            assert pytest.approx(aoa) == nml['reference_physical_properties']['angle_of_attack']

        # reset to original values
        aoa = 2.0
        controller._set_angle_of_attack_in_fun3d_nmls(aoa)
        for nml_file in nml_list:
            nml = f90nml.read(f'../{nml_file}')
            assert pytest.approx(aoa) == nml['reference_physical_properties']['angle_of_attack']
