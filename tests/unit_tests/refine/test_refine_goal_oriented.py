import pytest

from pyrefine.refine.goal_oriented import RefineGoalOriented
from pbs4py import FakePBS

project = 'box'


@pytest.fixture
def refine():
    return RefineGoalOriented(project)


def test_metric_form(refine: RefineGoalOriented):
    for metric in refine._known_metric_forms:
        refine.metric_form = metric
        assert refine.metric_form == metric

    with pytest.raises(ValueError):
        refine.metric_form = 'not_a_real_metric'

    refine.set_metric_form_opt_goal()
    assert 'opt-goal' == refine.metric_form

    refine.set_metric_form_cons_visc(-1., -1., -1.)
    assert 'cons-visc' == refine.metric_form


def test_add_shuffle_commands(refine: RefineGoalOriented):
    current = 'test01'
    volume_solb = 'test01_volume.solb'

    expected = ['fake_command',
                'cp test01_volume.solb test01_flow.solb',
                'cp prim_dual.solb test01_volume.solb']

    actual = ['fake_command']
    refine._add_commands_to_shuffle_solution_solb_files(actual, current, volume_solb)
    assert len(expected) == len(actual)
    for a, e in zip(actual, expected):
        assert a == e


def test_interpolate_command(refine: RefineGoalOriented):
    current = 'test02'
    next = 'test03'
    volume_solb = 'test02_volume.solb'
    expected = 'refmpi interpolate test02.meshb test02_volume.solb test03.meshb test03_volume_init.solb'
    assert expected == refine._create_interpolate_to_next_mesh_command(current, next, volume_solb)


def test_check_of_cons_visc_inputs(refine: RefineGoalOriented):
    with pytest.raises(ValueError):
        refine._check_that_cons_visc_reference_values_have_been_set()

    refine.mach = 1.0
    with pytest.raises(ValueError):
        refine._check_that_cons_visc_reference_values_have_been_set()

    refine.reynolds_number = 2.0
    with pytest.raises(ValueError):
        refine._check_that_cons_visc_reference_values_have_been_set()

    refine.temperature = 3.0
    refine._check_that_cons_visc_reference_values_have_been_set()


def test_goal_oriented_refine_command_default(refine: RefineGoalOriented):
    istep = 2
    complexity = 1000.0
    expected = 'refmpi loop box02 box03 1000.0 --gradation -1 --opt-goal'
    assert expected == refine._create_goal_oriented_refine_command(istep, complexity)


def test_goal_oriented_refine_command_opt_goal_nondefault(refine: RefineGoalOriented):
    istep = 3
    complexity = 2000.0
    refine.gradation = 10.0
    refine.mask_strong_bc = True
    expected = 'refmpi loop box03 box04 2000.0 --gradation 10.0 --opt-goal --mask --fun3d-mapbc box03.mapbc'
    assert expected == refine._create_goal_oriented_refine_command(istep, complexity)


def test_goal_oriented_refine_command_cons_visc(refine: RefineGoalOriented):
    istep = 4
    complexity = 2000.0
    mach = 3.0
    reynolds = 5.4
    temperature = 273.4
    refine.set_metric_form_cons_visc(mach, reynolds, temperature)
    expected = 'refmpi loop box04 box05 2000.0 --gradation -1 --cons-visc 3.0 5.4 273.4'
    assert expected == refine._create_goal_oriented_refine_command(istep, complexity)


def test_full_command_list(refine: RefineGoalOriented):
    refine.pbs = FakePBS()
    istep = 3
    complexity = 3000.0
    expected = [
        'cp box03_volume.solb box03_flow.solb', 'cp prim_dual.solb box03_volume.solb',
        'mpiexec refmpi loop box03 box04 3000.0 --gradation -1 --opt-goal &> refine03.out',
        'mpiexec refmpi interpolate box03.meshb box03_volume.solb box04.meshb box04_volume_init.solb &> refine_interp03.out']
    actual = refine._create_command_list_for_pbs_job(istep, complexity)
    assert len(expected) == len(actual)
    for a, e in zip(actual, expected):
        assert a == e
