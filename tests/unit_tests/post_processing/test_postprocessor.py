#!/usr/bin/env python3
import os
import pytest
from pytest import approx
from pyrefine.post_processing.fun3d_file_reader import Fun3dAdaptationSteadyHistoryReader as F3DReader
from pyrefine.post_processing.post_processing_command import PostProcessingCommand

test_directory = os.path.dirname(os.path.abspath(__file__))


def test_get_nnodes_from_grid_info():
    reader = F3DReader('', '')
    nnodes = reader._read_number_of_nodes_from_grid_info(
        f'{test_directory}/post_processing_test_files/test_m05.grid_info')
    assert(nnodes == 1078413)


def test_get_nnodes_from_flow_out():
    reader = F3DReader('', '')
    nnodes = reader._read_number_of_nodes_from_flow_out(
        f'{test_directory}/post_processing_test_files/test_m01_flow_out')
    assert(nnodes == 1044556)


def test_f3d_reader():
    reader = F3DReader(f'{test_directory}/post_processing_test_files', 'test_m')
    print(reader.final_hist_values)
    assert(reader.final_hist_values['C_L'][2] == approx(0.3300000000E+00))
    assert(reader.final_hist_values['C_D'][2] == approx(0.1530000000E+01))


def test_raise_error_if_no_files_found():
    with pytest.raises(RuntimeError):
        reader = F3DReader(test_directory, 'test_m')


def test_count_files_without_grid_info():
    reader = F3DReader(f'{test_directory}/post_processing_test_files', 'test_m')
    assert(reader.number_of_meshes == 3)


def test_lift_over_drag_without_user_defined_init():
    """ Add a simple post-processing function to the reader """
    class LOverDCommand(PostProcessingCommand):
        def execute(self):
            """ Override method from abstract base class"""
            c_l = self.target.final_hist_values['C_L']
            c_d = self.target.final_hist_values['C_D']
            self.target.final_hist_values['L/D'] = c_l / c_d

    reader = F3DReader(f'{test_directory}/post_processing_test_files', 'test_m')
    reader.register_command(LOverDCommand(reader))
    reader.execute_commands()
    expected_l_over_d = 0.3300000000E+00 / 0.1530000000E+01
    assert(reader.final_hist_values['L/D'][2] == approx(expected_l_over_d))


def test_lift_over_drag():
    """ Add a simple post-processing function to the reader """
    class LOverDCommand(PostProcessingCommand):
        def __init__(self, target):
            self.target_ = target

        def execute(self):
            """ Override method from abstract base class"""
            c_l = self.target_.final_hist_values['C_L']
            c_d = self.target_.final_hist_values['C_D']
            self.target_.final_hist_values['L/D'] = c_l / c_d

    reader = F3DReader(f'{test_directory}/post_processing_test_files', 'test_m')
    reader.register_command(LOverDCommand(reader))
    reader.execute_commands()
    expected_l_over_d = 0.3300000000E+00 / 0.1530000000E+01
    assert(reader.final_hist_values['L/D'][2] == approx(expected_l_over_d))


def test_raise_error_on_invalid_command():
    class BadCommand():
        def postprocess(self):
            pass

    reader = F3DReader('', '')
    with pytest.raises(ValueError):
        reader.register_command(BadCommand())
