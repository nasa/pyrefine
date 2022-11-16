import os

from pyrefine.simulation.distance_base import DistanceBase
from pyrefine.simulation.distance_refine import DistanceRefine
from pyrefine.simulation.distance_tinf import DistanceTinf
from pyrefine.directory_utils import cd
from pbs4py import FakePBS

# defined here since used by fun3d simulation test too
refine_expected_dist_command = 'mpiexec refmpi distance test03.lb8.ugrid test03-distance.solb --fun3d test03.mapbc &> distance03.out'
distance_test_dir = f'{os.path.dirname(os.path.abspath(__file__))}/distance_test_files'


def test_distance_tinf_command():
    istep = 4
    dist = DistanceTinf('test', FakePBS())
    tinf_expected_dist_command = 'mpiexec ParallelDistanceCalculator test04.lb8.ugrid --commas 3,4,5,6,7,8,9,10,11,12 &> distance04.out'
    with cd(distance_test_dir):
        assert tinf_expected_dist_command == dist.create_distance_command(istep)


def test_distance_base_command():
    dist = DistanceBase('test')
    assert '' == dist.create_distance_command(1)


def test_distance_base_expected_file_list():
    dist = DistanceBase('test')
    assert len(dist.get_expected_file_list()) == 0


def test_distance_base_distance_file():
    istep = 3
    dist = DistanceBase('test')
    expected = 'test03-distance.solb'
    assert expected == dist.create_distance_filename(istep)


def test_distance_refine_command():
    istep = 3
    dist = DistanceRefine('test', FakePBS())
    assert refine_expected_dist_command == dist.create_distance_command(istep)
