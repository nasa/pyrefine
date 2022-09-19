import pytest
from pyrefine.simulation.base import SimulationBase


def test_default_run():
    sim = SimulationBase('test')
    with pytest.raises(NotImplementedError):
        sim.run(1)
