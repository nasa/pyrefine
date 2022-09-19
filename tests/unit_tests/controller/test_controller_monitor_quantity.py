import pytest
import os
import filecmp

from pyrefine.controller.monitor_quantity import ControllerMonitorQuantity
from pyrefine.directory_utils import cd

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_controller_monitor_quantity_files'


@pytest.fixture
def controller():
    controller = ControllerMonitorQuantity('test')
    return controller


def test_convergence_logic_one_value(controller: ControllerMonitorQuantity):
    controller.relative_tolerance = 0.01

    values = [[2.0], [2.0], [2.0]]
    assert controller._monitored_quantities_are_converged(values)

    values.append([2.0])
    assert controller._monitored_quantities_are_converged(values)

    values[0][0] = 1.0
    assert controller._monitored_quantities_are_converged(values)


def test_converged_logic_within_tolerance(controller: ControllerMonitorQuantity):
    controller.relative_tolerance = 0.01

    values = [[100.1], [99.1], [100.0]]
    assert controller._monitored_quantities_are_converged(values)

    values.append([100.0])
    assert controller._monitored_quantities_are_converged(values)

    values[0][0] = 1.0
    assert controller._monitored_quantities_are_converged(values)


def test_converged_logic_out_of_tolerance(controller: ControllerMonitorQuantity):
    controller.relative_tolerance = 0.01

    values = [[99.0], [99.0], [101.0]]
    assert not controller._monitored_quantities_are_converged(values)

    values = [[102.0], [102.0], [100.0]]
    assert not controller._monitored_quantities_are_converged(values)

    values = [[100.0], [100.0], [102.0], [100.0]]
    assert not controller._monitored_quantities_are_converged(values)


def test_converged_logic_multiple_within_tolerance(controller: ControllerMonitorQuantity):
    controller.relative_tolerance = 0.01

    values = [[100.1, 1001.0], [99.1, 991.0], [100.0, 1000.0]]
    assert controller._monitored_quantities_are_converged(values)

    values.append([100.0, 1000.0])
    assert controller._monitored_quantities_are_converged(values)

    values[0][0] = 1.0
    assert controller._monitored_quantities_are_converged(values)


def test_converged_logic_multiple_with_one_not_in_tolerance(controller: ControllerMonitorQuantity):
    controller.relative_tolerance = 0.01

    values = [[100.1, 1001.0], [99.1, 989.0], [100.0, 1000.0]]
    assert not controller._monitored_quantities_are_converged(values)

    values.append([100.0, 1000.0])
    assert not controller._monitored_quantities_are_converged(values)

    values[0][0] = 1.0
    assert not controller._monitored_quantities_are_converged(values)


def test_taken_minimum_number_of_steps_at_complexity(controller: ControllerMonitorQuantity):
    for i in [1, 2, 3]:
        assert not controller._taken_minimum_number_of_steps_at_complexity(i)
    for i in [4, 5, 6, 7, 8]:
        assert controller._taken_minimum_number_of_steps_at_complexity(i)


def test_reached_max_steps_at_complexity(controller: ControllerMonitorQuantity):
    controller.maximum_steps_per_complexity = 5
    assert not controller._reached_max_steps_at_complexity_level(4)
    assert not controller._reached_max_steps_at_complexity_level(5)
    assert controller._reached_max_steps_at_complexity_level(6)


def test_reset_monitored_state(controller: ControllerMonitorQuantity):
    controller.quantity_history = [[1, 2]]
    controller.steps_at_current_complexity = 5

    controller._reset_monitored_state()
    assert controller.quantity_history == []
    assert controller.steps_at_current_complexity == 0


def check_quantity_history(actual, expected):
    assert len(actual) == len(expected)

    if len(actual) > 0:
        for aa, ee in zip(actual, expected):
            assert len(aa) == len(ee)
            if len(aa) > 0:
                for a, e in zip(aa, ee):
                    assert a == pytest.approx(e)


def test_controller_state_reading_and_writing(controller: ControllerMonitorQuantity):
    with cd(test_dir):
        expected_complexity = 234.5
        expected_steps_at_current_complexity = 4
        expected_history = [[1.334, 1.42], [4.32,  5.44]]

        current_complexity = controller._read_controller_restart_state()

        assert pytest.approx(expected_complexity) == current_complexity
        assert expected_steps_at_current_complexity == controller.steps_at_current_complexity
        check_quantity_history(controller.quantity_history, expected_history)

        test_output = 'controller_test.txt'
        controller._save_controller_state(current_complexity, test_output)
        assert filecmp.cmp(test_output, 'controller_state.txt')
        os.system(f'rm {test_output}')


def test_controller_reading_with_bad_file(controller: ControllerMonitorQuantity):
    with pytest.raises(RuntimeError):
        controller._read_controller_restart_state(restart_file='file_that_doesnt_exist.txt')


def test_default_get_monitored_quantities_for_step(controller: ControllerMonitorQuantity):
    with pytest.raises(NotImplementedError):
        controller.get_monitored_quantities_for_step(1)


def test_first_call_of_a_new_run(controller: ControllerMonitorQuantity):
    assert controller._first_call_of_a_new_run(2)
    for i in [3, 4, 5, 6]:
        assert not controller._first_call_of_a_new_run(i)


def test_beginning_of_a_restart(controller: ControllerMonitorQuantity):
    assert controller._beginning_of_a_restart(current_complexity=None)
    assert not controller._beginning_of_a_restart(current_complexity=1044.0)


def test_if_complexity_should_be_increased_not_enough_steps(controller: ControllerMonitorQuantity):
    controller.steps_at_current_complexity = 2
    assert not controller._complexity_should_be_increased()


def test_if_complexity_should_be_increased_unconverged_history(controller: ControllerMonitorQuantity):
    controller.steps_at_current_complexity = 5
    controller.maximum_steps_per_complexity = 20
    unconverged_history = [[1.2], [1.7], [1.8], [1.9], [2.3]]
    controller.quantity_history = unconverged_history
    assert not controller._complexity_should_be_increased()


def test_if_complexity_should_be_increased_converged_history(controller: ControllerMonitorQuantity):
    controller.steps_at_current_complexity = 5
    controller.maximum_steps_per_complexity = 20
    converged_history = [[1.2], [1.7], [1.8], [1.8], [1.8]]
    controller.quantity_history = converged_history
    assert controller._complexity_should_be_increased()


def test_if_complexity_should_be_increased_max_steps_at_complexity(controller: ControllerMonitorQuantity):
    controller.steps_at_current_complexity = 6
    controller.maximum_steps_per_complexity = 5
    unconverged_history = [[1.2], [1.7], [1.3], [1.8], [1.4]]
    controller.quantity_history = unconverged_history
    assert controller._complexity_should_be_increased()
