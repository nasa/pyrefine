import pytest
from pyrefine.refine.uniform_region import UniformRegionBase, UniformBox, UniformCylinder


def test_base_class_command_exception():
    region = UniformRegionBase()

    with pytest.raises(NotImplementedError):
        region.get_commandline_arguments()


def test_base_class_limit():
    region = UniformRegionBase()

    with pytest.raises(ValueError):
        region.limit = 'not_a_limit_type'

    valid_options = ['floor', 'ceil']
    for option in valid_options:
        region.limit = option
        assert region.limit == option


def test_uniform_box_command_with_default_options():
    region = UniformBox()
    expected_arg = f' --uniform box ceil 0.100000 0.100000 0.000000 0.000000 0.000000 1.000000 1.000000 1.000000'
    assert region.get_commandline_arguments() == expected_arg


def test_uniform_box_command_with_nondefault_options():
    xmin = -1.0
    ymin = -2.0
    zmin = -3.0
    xmax = 3.0
    ymax = 4.0
    zmax = 5.0
    region = UniformBox(xmin, ymin, zmin, xmax, ymax, zmax)
    region.limit = 'floor'
    region.decay_distance = 0.02
    region.h0 = 1.4
    expected_arg = f' --uniform box floor 1.400000 0.020000 -1.000000 -2.000000 -3.000000 3.000000 4.000000 5.000000'
    assert region.get_commandline_arguments() == expected_arg


def test_uniform_cylinder_command_with_default_options():
    region = UniformCylinder()
    expected_arg = f' --uniform cyl ceil 0.100000 0.100000 0.000000 0.000000 0.000000 0.000000 0.000000 1.000000 1.000000 1.000000'
    assert region.get_commandline_arguments() == expected_arg


def test_uniform_cylinder_command_with_nondefault_options():
    x1 = 1.0
    y1 = -1.0
    z1 = 2.0
    r1 = 4.0
    x2 = 1.6
    y2 = 4.3
    z2 = 2.9
    r2 = 5.0
    region = UniformCylinder(x1, y1, z1, r1, x2, y2, z2, r2)
    region.limit = 'floor'
    region.decay_distance = 0.03
    region.h0 = 2.3
    expected_arg = f' --uniform cyl floor 2.300000 0.030000 1.000000 -1.000000 2.000000 1.600000 4.300000 2.900000 4.000000 5.000000'
    assert region.get_commandline_arguments() == expected_arg
