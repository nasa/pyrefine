import pytest
from pyrefine.controller.smooth_transition import ControllerSmoothTransition


@pytest.fixture
def controller():
    controller = ControllerSmoothTransition('test')
    controller.initial_complexity = 1000
    controller.steps_per_complexity = 5
    controller.complexity_multiplier = 2.0
    controller.steps_per_transition = 4
    return controller


def test_compute_phase_step_info(controller: ControllerSmoothTransition):
    for step in range(1, 3*9):
        phase, step_within_phase = controller._compute_phase_step_info(step)
        if step <= 9:
            assert phase == 0
            assert step_within_phase == step
        elif step <= 2*9:
            assert phase == 1
            assert step_within_phase == step - 9
        else:
            assert phase == 2
            assert step_within_phase == step - 9*2


def test_compute_complexity(controller: ControllerSmoothTransition):
    initial_complexity = controller.initial_complexity
    complexity = initial_complexity

    for step in range(1, 28):
        complexity = controller.compute_complexity(step, complexity)
        if step <= 5:
            assert complexity == pytest.approx(initial_complexity)
        elif step == 6:
            assert complexity == pytest.approx(initial_complexity * 2**(0+1./5.))
        elif step == 7:
            assert complexity == pytest.approx(initial_complexity * 2**(0+2./5.))
        elif step == 8:
            assert complexity == pytest.approx(initial_complexity * 2**(0+3./5.))
        elif step == 9:
            assert complexity == pytest.approx(initial_complexity * 2**(0+4./5.))
        elif step <= 14:
            assert complexity == pytest.approx(initial_complexity * 2.0)
        elif step == 15:
            assert complexity == pytest.approx(initial_complexity * 2**(1+1./5.))
        elif step == 16:
            assert complexity == pytest.approx(initial_complexity * 2**(1+2./5.))
        elif step == 17:
            assert complexity == pytest.approx(initial_complexity * 2**(1+3./5.))
        elif step == 18:
            assert complexity == pytest.approx(initial_complexity * 2**(1+4./5.))
        elif step <= 23:
            assert complexity == pytest.approx(initial_complexity * 2.0 ** 2.0)
        elif step == 24:
            assert complexity == pytest.approx(initial_complexity * 2**(2+1./5.))
        elif step == 25:
            assert complexity == pytest.approx(initial_complexity * 2**(2+2./5.))
        elif step == 26:
            assert complexity == pytest.approx(initial_complexity * 2**(2+3./5.))
        elif step == 27:
            assert complexity == pytest.approx(initial_complexity * 2**(2+4./5.))


def test_compute_complexity_constant_transition(controller: ControllerSmoothTransition):
    initial_complexity = controller.initial_complexity
    controller.steps_per_complexity = 1
    controller.complexity_multiplier = 1.2
    controller.steps_per_transition = 5
    complexity = initial_complexity

    for step in range(1, 28):
        complexity = controller.compute_complexity(step, complexity)
        assert complexity == initial_complexity * 1.2 ** ((step-1)/6.0)
