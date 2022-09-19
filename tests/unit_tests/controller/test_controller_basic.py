import pytest
from pyrefine.controller.basic import ControllerBasic


@pytest.fixture
def controller():
    controller = ControllerBasic('test', pbs=None)
    return controller


def test_complexity_schedule(controller: ControllerBasic):
    controller.initial_complexity = 100

    multipler = 1.5
    controller.complexity_multiplier = multipler

    controller.steps_per_complexity = 3

    nsteps = 3 * controller.steps_per_complexity
    current_complexity = controller.initial_complexity

    for istep in range(1, nsteps+1):
        complexity = controller.compute_complexity(istep, current_complexity)
        if istep <= controller.steps_per_complexity:
            assert complexity == controller.initial_complexity
        elif istep <= controller.steps_per_complexity*2:
            assert complexity == multipler * controller.initial_complexity
        elif istep <= controller.steps_per_complexity*3:
            assert complexity == multipler * multipler * controller.initial_complexity


def test_defaultsave_restart_files_this_step_logic(controller: ControllerBasic):
    steps_per_complexity = 3
    controller.steps_per_complexity = steps_per_complexity

    # clean up schedule defaults to steps_per_complexity if not setting restart_save_freq
    assert not controller.save_restart_files_this_step(1)
    assert controller.save_restart_files_this_step(steps_per_complexity)
    assert controller.save_restart_files_this_step(steps_per_complexity*2)


def test_clean_up_schedule(controller: ControllerBasic):
    restart_save = 2
    controller.restart_save_frequency = restart_save

    assert controller.save_restart_files_this_step(restart_save)
    assert controller.save_restart_files_this_step(restart_save*2)
    assert not controller.save_restart_files_this_step(restart_save*2+1)
