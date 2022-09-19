import pytest
import os

from pyrefine.controller.base import ControllerBase
from pyrefine.directory_utils import cd

test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/test_controller_base_files'


@ pytest.fixture
def controller():
    controller = ControllerBase('test', pbs=None)
    return controller


def test_for_early_stop(controller: ControllerBase):
    for istep in range(1, 6):
        assert not controller.check_for_early_stop_condition(istep)


def test_default_compute_complexity(controller: ControllerBase):
    with pytest.raises(NotImplementedError):
        complexity = controller.compute_complexity(1, 1000.)


def test_default_update_inputs(controller: ControllerBase):
    controller.update_inputs(2)


def test_default_restart_save_frequency(controller: ControllerBase):
    for istep in range(1, 6):
        assert controller._save_restart_files_on_this_step(istep)


def test_restart_save_frequency(controller: ControllerBase):
    controller.restart_save_frequency = 4
    assert not controller._save_restart_files_on_this_step(1)
    assert not controller._save_restart_files_on_this_step(2)
    assert controller._save_restart_files_on_this_step(4)
    assert not controller._save_restart_files_on_this_step(6)
    assert controller._save_restart_files_on_this_step(8)


def check_cleanup_lists(expected, actual):
    assert len(expected) == len(actual)
    for a, e in zip(actual, expected):
        assert a == e


def test_cleanup_list_not_on_restart(controller: ControllerBase):
    controller.restart_save_frequency = 2
    expected_list = (controller.file_extensions_to_cleanup_every_step +
                     controller.file_extensions_to_save_only_on_restart_iterations)
    cleanup_list = controller._form_cleanup_extension_list_for_step(istep=1)
    check_cleanup_lists(expected_list, cleanup_list)


def test_cleanup_list_on_restart(controller: ControllerBase):
    controller.restart_save_frequency = 2
    expected_list = controller.file_extensions_to_cleanup_every_step.copy()
    cleanup_list = controller._form_cleanup_extension_list_for_step(istep=2)
    check_cleanup_lists(expected_list, cleanup_list)


def test_create_project_rootname():
    base = 'sphere'
    controller = ControllerBase(base)
    assert controller._create_project_rootname(0) == 'sphere00'
    assert controller._create_project_rootname(11) == 'sphere11'
    assert controller._create_project_rootname(100) == 'sphere100'


def test_cleanup(controller: ControllerBase):
    files_not_to_delete = ['test01.other_file', 'test02.other_file', 'test02.txt']
    files_to_delete_for_step1 = ['test01.ugrid', 'test01.txt']
    files_to_delete_for_step2 = ['test02.ugrid']

    controller.set_file_extensions_to_save_only_on_restart_iterations(['.txt'])
    controller.set_file_extensions_to_cleanup_every_step(['.ugrid'])
    controller.restart_save_frequency = 2

    all_files = files_not_to_delete + files_to_delete_for_step1 + files_to_delete_for_step2
    files_after_step1 = files_not_to_delete + files_to_delete_for_step2
    with cd(test_dir):
        for file in all_files:
            os.system(f'touch {file}')

        controller.save_all = True
        controller.cleanup(1)
        for file in all_files:
            assert os.path.isfile(file)

        controller.save_all = False
        controller.cleanup(1)
        for file in files_to_delete_for_step1:
            assert not os.path.isfile(file)
        for file in files_after_step1:
            assert os.path.isfile(file)

        controller.cleanup(2)
        for file in files_to_delete_for_step2:
            assert not os.path.isfile(file)
        for file in files_not_to_delete:
            assert os.path.isfile(file)
            os.system(f'rm {file}')
