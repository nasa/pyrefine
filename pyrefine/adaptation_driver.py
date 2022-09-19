#!/usr/bin/env python
from __future__ import division, print_function

import numpy as np
import os
from typing import List

from pbs4py import PBS
from .directory_utils import cd
from .shell_utils import cp, mkdir

from .component_base import ComponentBase
from .refine.multiscale import RefineMultiscale
from .simulation.fun3d import SimulationFun3dFV
from .controller.basic import ControllerBasic


class AdaptationDriver:
    """
    The standard adaptation driver which also can run a basic adaptation.

    The default components are set up to run a
    steady adaptation with FUN3D finite volume, increase the complexity
    after a fixed number of meshes, and use the Mach number multiscale metric.
    """

    def __init__(self, project_name: str, pbs: PBS):
        """
        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs: :class:
            PBS queue helper
        """

        #: str: The root name of the project (without any mesh numbers)
        self.project_name = project_name

        #: :class:PBS: The pbs queue helper object
        self.pbs = pbs

        #: int: First iteration to run in adaptation process
        self.start_iteration = 1

        #: int: Last iteration to run in the adaptation process
        self.final_iteration = 50

        self.current_complexity = None

        #: int: How many mesh vertices per cpu core. Used when determining how many
        #:      compute nodes to request. The default value is 10000.
        self.vertices_per_cpu_core = 10000

        #: :class:`~pyrefine.simulation.base.SimulationBase`: the simulation driver object
        self.simulation = SimulationFun3dFV(project_name)

        #: :class:`~pyrefine.controller.base.ControllerBase`: the complexity schedule controller object
        self.controller = ControllerBasic(project_name)

        #: :class:`~pyrefine.refine.base.RefineBase`: the refine driver object
        self.refine = RefineMultiscale(project_name)

    def set_iterations(self, start_iteration, final_iteration):
        """
        Set the starting and ending iteration of the adaptation cycle.
        The default starting iteration is 1 which is a new adaptation.
        For restarts, set the starting value to the iteration you want to
        begin with. The default final iteration is 50.

        Parameters
        ----------
        start_iteration: int
        final_iteration: int
        """
        self.start_iteration = start_iteration
        self.final_iteration = final_iteration

    def run(self):
        """
        Perform the adaptation
        """
        self.component_list: List[ComponentBase] = [self.simulation,
                                                    self.controller,
                                                    self.refine]

        self._check_pbs()
        self._check_if_ready()
        self._prepare_flow_directory()

        with cd('./Flow'):
            if self.start_iteration == 1:
                self.refine.translate_mesh()

            for istep in range(self.start_iteration, self.final_iteration+1):
                print(f'Begin adaptation step {istep}')
                self._check_for_stop_file(istep)
                early_stop = self._run_adapt_iteration(istep)
                self.controller.cleanup(istep)
                if early_stop:
                    break
                self.istep = istep

    def _check_pbs(self):
        """
        If a component already has a pbs handler, let them use that, else
        give them one
        """
        for component in self.component_list:
            if component.pbs is None:
                component.pbs = self.pbs

    def _run_adapt_iteration(self, istep: int) -> bool:
        """
        | Run the steps of a cycle of the adaptation. For a steady
        | adaptation, the steps are:
        |
        | 1. Run the flow simulation.
        | 2. Compute the desired complexity for the next step.
        | 3. Compute the metric field
        """

        # set up
        self._set_node_request_size(istep)
        self._copy_mapbc_file(istep)
        self.controller.update_inputs(istep)

        self.simulation.run(istep)

        # adaptation prep for next step
        self.current_complexity = self.controller.compute_complexity(istep + 1,
                                                                     self.current_complexity)
        self.refine.run(istep, self.current_complexity)

        early_stop = self.controller.check_for_early_stop_condition(istep)
        return early_stop

    def _set_node_request_size(self, istep: int):
        """
        Set how many compute nodes to request given the current complexity
        and desired grid vertices per cpu core
        """

        if istep == 1:
            complexity = self.controller.initial_complexity
        else:
            if self.current_complexity is None:  # handle restarts
                self.current_complexity = self.controller.compute_complexity(istep,
                                                                             self.current_complexity)
            complexity = self.current_complexity
        vertex_estimate = complexity * 2

        cores_request = vertex_estimate / self.vertices_per_cpu_core

        for component in self.component_list:
            request = int(np.ceil(cores_request/component.pbs.ncpus_per_node))
            component.pbs.requested_number_of_nodes = request

    def _check_if_ready(self):
        """
        Check if the necessary files are present to start the adaptation
        """
        self.expected_input_files = []
        for component in self.component_list:
            self.expected_input_files.extend(component.get_expected_file_list())

        for expected_file in self.expected_input_files:
            if not os.path.isfile(expected_file):
                raise FileNotFoundError(f'Expected input file: {expected_file} was not found')

    def _check_for_stop_file(self, istep):
        """
        Check for a stop.dat file in the root directory of the adaptation for
        early termination
        """
        stop = 1e99
        try:
            stop = np.loadtxt('../stop.dat')
        except:
            return
        if stop < istep:
            print('Adaptation found stop.dat in root directory. Stopping...')
            os.remove('../stop.dat')
            quit()

    def _prepare_flow_directory(self):
        """
        Make the Flow directory if it does not exist, then fill it with the
        expected input files from each component
        """
        run_dir = './Flow'
        mkdir(run_dir)
        with cd(run_dir):
            for filename in self.expected_input_files:
                cp(f'../{filename}', '.')

    def _copy_mapbc_file(self, istep):
        """
        Copy the original mapbc file to the current mesh name
        """
        first_mapbc_file = f'../{self._create_project_rootname(1)}.mapbc'
        new_mapbc_file = f'{self._create_project_rootname(istep)}.mapbc'
        cp(first_mapbc_file, new_mapbc_file)

    def _create_project_rootname(self, istep):
        return self.refine._create_project_rootname(istep)
