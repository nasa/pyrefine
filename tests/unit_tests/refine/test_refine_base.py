import pytest

from pyrefine.refine.base import RefineBase
from pyrefine.refine.uniform_region import UniformRegionBase

project = "sphere"


@pytest.fixture
def refine():
    return RefineBase(project)


def test_default_run(refine: RefineBase):
    with pytest.raises(NotImplementedError):
        refine.run(1, 10.0)


def test_first_ugrid_filename(refine: RefineBase):
    expected = "sphere01.lb8.ugrid"
    istep = 1
    assert expected == refine._get_ugrid_mesh_filename(istep)


def test_translate_mesh_command(refine: RefineBase):
    expected = "ref translate sphere01.meshb sphere01.lb8.ugrid"
    ugrid = refine._get_ugrid_mesh_filename(1)
    assert expected == refine._create_translate_command(ugrid, istep=1)


def test_translate_mesh_command_step2(refine: RefineBase):
    istep = 2
    expected = "ref translate sphere02.meshb sphere02.lb8.ugrid"
    ugrid = refine._get_ugrid_mesh_filename(2)
    assert expected == refine._create_translate_command(ugrid, istep)


def test_translate_mesh_command_with_extrude(refine: RefineBase):
    istep = 1
    refine.extrude_2d_mesh_to_3d = True
    expected = "ref translate sphere01.meshb sphere01.lb8.ugrid --extrude"
    ugrid = refine._get_ugrid_mesh_filename(1)
    assert expected == refine._create_translate_command(ugrid, istep)


def test_add_gradation(refine: RefineBase):
    initial_command = "test"
    assert "test --gradation -1" == refine._add_gradation_to_ref_loop_command(initial_command)

    refine.gradation = 4.0
    assert "test --gradation 4.0" == refine._add_gradation_to_ref_loop_command(initial_command)


def test_add_aspect_ratio_default_input(refine: RefineBase):
    initial_command = "test"
    assert "test" == refine._add_aspect_ratio_to_ref_loop_command(initial_command)


def test_add_aspect_ratio_valid_input(refine: RefineBase):
    initial_command = "test"
    refine.aspect_ratio = 2.0
    assert "test --aspect-ratio 2.0" == refine._add_aspect_ratio_to_ref_loop_command(initial_command)

    refine.aspect_ratio = 1.0
    assert "test --aspect-ratio 1.0" == refine._add_aspect_ratio_to_ref_loop_command(initial_command)


def test_add_aspect_ratio_invalid_input(refine: RefineBase):
    initial_command = "test"
    refine.aspect_ratio = 0.5
    assert "test" == refine._add_aspect_ratio_to_ref_loop_command(initial_command)

    refine.aspect_ratio = -1
    assert "test" == refine._add_aspect_ratio_to_ref_loop_command(initial_command)


def test_add_uniform_refinement_regions_no_regions(refine: RefineBase):

    initial_command = "test"
    assert initial_command == refine._add_uniform_refinement_regions_command(initial_command)


def test_add_uniform_refinement_regions_with_regions(refine: RefineBase):
    initial_command = "test"

    class FakeRegion(UniformRegionBase):
        def __init__(self, options):
            self.options = options

        def get_commandline_arguments(self) -> str:
            return self.options

    refine.uniform_regions.append(FakeRegion(" --option1"))
    refine.uniform_regions.append(FakeRegion(" --option2"))

    assert "test --option1 --option2" == refine._add_uniform_refinement_regions_command(initial_command)


def test_comm_ref_loop_options_defaults(refine: RefineBase):
    initial_command = "test"
    expected = "test --gradation -1"
    assert expected == refine._add_common_ref_loop_options(initial_command)


def test_comm_ref_loop_options_nondefaults(refine: RefineBase):
    refine.use_buffer = True
    refine.use_kexact = True
    refine.use_deforming = True
    refine.use_balance_full = True
    refine.number_of_sweeps = 3
    initial_command = "test"
    expected = "test --gradation -1 --buffer --kexact --deforming --balance-full -s 3"
    assert expected == refine._add_common_ref_loop_options(initial_command)


def test_rescale_2D_length_commands(refine: RefineBase):
    refine.rescale_2D_length = 2.0
    commands = refine.create_rescale_2d_command_list(3)
    expected = [
        """scale_aflr3 <<EOF
sphere03.lb8.ugrid
sphere03_scaled.lb8.ugrid
1 2.0 1
EOF""",
        "mv sphere03_scaled.lb8.ugrid sphere03.lb8.ugrid",
    ]

    assert len(commands) == len(expected)
    for cmd, exp in zip(commands, expected):
        assert cmd == exp
