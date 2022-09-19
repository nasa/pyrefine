#!/usr/bin/env python
from pyrefine.component_base import ComponentBase


class SimulationBase(ComponentBase):
    """
    Driver for the simulation step
    """

    def run(self, istep: int):
        """
        Run the sequence of simulations for a given adaptation cycle
        """
        raise NotImplementedError("Simulation classes must implement run method")
