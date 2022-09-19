from calendar import c
import os
import pytest
import filecmp

import numpy as np

from pyrefine.simulation.sfe_cfg import SFEconfig

test_directory = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def cfg_test0():
    cfg = SFEconfig(f'{test_directory}/sfe_cfg_test_files/sfe_test0.cfg', convert_read_arrays=True)
    return cfg


@pytest.fixture
def cfg_test0_no_convert_arrays():
    cfg = SFEconfig(f'{test_directory}/sfe_cfg_test_files/sfe_test0.cfg')
    return cfg


def test_reading_floats_from_sfe_cfg(cfg_test0):
    assert type(cfg_test0['float0']) == float
    assert cfg_test0['float0'] == pytest.approx(1.0)

    assert type(cfg_test0['float1']) == float
    assert cfg_test0['float1'] == pytest.approx(2.05)

    assert type(cfg_test0['float2']) == float
    assert cfg_test0['float2'] == pytest.approx(0.05)

    assert type(cfg_test0['float3']) == float
    assert cfg_test0['float3'] == pytest.approx(12.0)

    assert type(cfg_test0['float4']) == float
    assert cfg_test0['float4'] == pytest.approx(1.0e-5)

    assert type(cfg_test0['float5']) == float
    assert cfg_test0['float5'] == pytest.approx(1.0e+5)

    assert type(cfg_test0['float_6']) == float
    assert cfg_test0['float_6'] == pytest.approx(2.0e+3)


def test_reading_ints_sfe_cfg(cfg_test0):
    assert type(cfg_test0['int0']) == int
    assert cfg_test0['int0'] == 3

    assert type(cfg_test0['int1']) == int
    assert cfg_test0['int1'] == 500

    assert type(cfg_test0['int2']) == int
    assert cfg_test0['int2'] == -1


def test_reading_int_arrays_sfe_cfg(cfg_test0):
    expected = np.array([1, 4, 4, 5])
    assert (cfg_test0['int_array_plus'] == expected).all()

    assert (cfg_test0['int_array'] == expected).all()


def test_reading_int_arrays_sfe_cfg(cfg_test0_no_convert_arrays):
    assert cfg_test0_no_convert_arrays['int_array_plus'] == '1 + 4 + 4 + 5'

    assert cfg_test0_no_convert_arrays['int_array(0)'] == 1
    assert cfg_test0_no_convert_arrays['int_array(1)'] == 4
    assert cfg_test0_no_convert_arrays['int_array(2)'] == 4
    assert cfg_test0_no_convert_arrays['int_array(3)'] == 5


def test_reading_bools_from_sfe_cfg(cfg_test0):
    assert type(cfg_test0['bool0']) == bool
    assert cfg_test0['bool0'] == True

    assert type(cfg_test0['bool1']) == bool
    assert cfg_test0['bool1'] == False

    assert type(cfg_test0['bool2']) == bool
    assert cfg_test0['bool2'] == False

    assert type(cfg_test0['bool3']) == bool
    assert cfg_test0['bool3'] == True


def test_reading_strings_sfe_cfg(cfg_test0):
    assert type(cfg_test0['str_input']) == str
    assert cfg_test0['str_input'] == 'hello world'

    assert type(cfg_test0['str_input1']) == str
    assert cfg_test0['str_input1'] == 'hello1world'

    assert type(cfg_test0['str_input2']) == str
    assert cfg_test0['str_input2'] == '1hello'

    assert type(cfg_test0['str_input3']) == str
    assert cfg_test0['str_input3'] == 'hello 1 world'


def test_creating_sfe_cfg_from_scratch():
    output_file = f'{test_directory}/test_output_files/output_create_sfe_cfg_from_scratch.cfg'
    golden_file = f'{test_directory}/sfe_cfg_test_files/golden_from_scratch.cfg'
    golden_file1 = f'{test_directory}/sfe_cfg_test_files/golden_from_scratch1.cfg'

    cfg = SFEconfig()
    cfg['value0'] = 1.2e-7
    cfg['int0'] = 5
    cfg['str_input'] = 'hello_world'
    cfg['bool0'] = True
    cfg['bool1'] = False
    cfg.write(output_file, force=True)
    assert filecmp.cmp(output_file, golden_file)

    cfg['int0'] = 8
    cfg['int_array'] = np.array([1, 3, 4])
    cfg['bool_array'] = np.array([[True, False, False], [False, True, False]])
    cfg['bool_list'] = [[True, False, False], [False, True, False]]
    cfg['float_3darray'] = np.array([[[1.2, 3.5], [4.3, 2.1]], [[-0.4, 2.3], [5.7, -9.1]]])
    cfg['str_4d'] = np.array(['surface']).reshape((1, 1, 1, 1))
    cfg.write(output_file, force=True)

    assert filecmp.cmp(output_file, golden_file1)

    with pytest.raises(FileExistsError):
        cfg.write(output_file, force=False)

    cfg['str_5d'] = np.array(['surface']).reshape((1, 1, 1, 1, 1))
    with pytest.raises(ValueError):
        cfg.write(output_file, force=True)
