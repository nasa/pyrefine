General FUN3D Simulations
=========================

These simple FUN3D simulation classes run one call to FUN3D's ``nodet_mpi`` and
can be used to drive steady or unsteady adaptations.

Distance Calculators
--------------------
The distance object calculates the distance field for a given volume mesh for fun3d simulations.
This is necessary because FUN3D's internal distance calculator has some issues with adapted meshes.
Each fun3d simulations simulation object has an instance of a distance calculator which can be changed, but
the default distance calculator is refine's to reduced the number of dependencies.
The methods to access this functionality are defined in :class:`~pyrefine.simulation.distance_base.DistanceBase`.

.. toctree::
   :maxdepth: 1

   distance/base.rst
   distance/tinf.rst
   distance/refine.rst


Finite Volume Simulation
------------------------

.. automodule:: pyrefine.simulation.fun3d

.. autoclass:: SimulationFun3dFV
   :members:
   :show-inheritance:
   :inherited-members:


Stabilized Finite Element Simulation
------------------------------------

.. autoclass:: SimulationFun3dSFE
   :members:
   :show-inheritance:
   :inherited-members:
