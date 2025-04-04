from pbs4py import PBS

from .base import ControllerBase


class NodeRatioController(ControllerBase):
    def __init__(self, project_name: str, pbs: PBS = None):
        """
        Multiplies the complexity whenever the ratio of the nodes in the mesh to the previous one drops below :attr:`~node_ratio`
        by a fixed factor, :attr:`~complexity_multiplier`. The default behavior is to double
        the complexity whenever the ratio of nodes in the mesh is below 1.25.

        Parameters
        ----------
        project_name:
            The root name of the project (without any mesh numbers)
        pbs:
            PBS queue helper
        """
        super().__init__(project_name, pbs)

        #: int: The contoller will multiple the complexity by the multiplier factor is the
        #: ratio of the number of nodes of this mesh to the previous one drops below this ratio
        self.node_ratio = 1.25

        #: float: the multiplier applied to the complexity when the complexity needs to be updated.
        #:  The default value is 2.0.
        self.complexity_multiplier = 2.0

    def compute_complexity(self, istep: int, current_complexity: float) -> float:
        """
        Parameters
        ----------
        istep:
            Adaptation step number
        current_complexity:
            The current complexity in the driver. If doing a restart, the current
            complexity will be `None`

        Returns
        -------
        complexity:
        """

        if istep == 1:
            return self.initial_complexity

        current_number_of_nodes = self._get_vertex_count(istep - 1)
        if istep == 2 or current_complexity is None:
            complexity = self.initial_complexity
        else:
            node_ratio = current_number_of_nodes / self.previous_number_of_nodes
            print("Node ratio = ", node_ratio)
            if node_ratio < self.node_ratio:
                complexity = current_complexity * self.complexity_multiplier
            else:
                complexity = current_complexity

        self.previous_number_of_nodes = current_number_of_nodes
        print("Complexity:", complexity)
        return complexity
