Two Phase Time Domain FUN3D Simulation
======================================


.. automodule:: pyrefine.simulation.fun3d_two_phase_unsteady

Finite Volume
-------------
This two phase unsteady analysis can be used in cases like DDES where you want
to save volume outputs for metric computation at a fixed interval, but you want to have a
phase before saving the files to propagate the transients downstream.

The same fun3d.nml in the root directory is used for both phases.
The attributes for class set the number of the steps for each phase and the volume save frequency
into the fun3d.nml before running nodet_mpi.

.. autoclass:: SimulationFun3dTwoPhase
   :members:
   :show-inheritance:

Stabilized Finite Element
-------------------------
This two phase analysis runs differently than the FV version becase the first phase is a steady analysis.

.. autoclass:: SimulationSFETwoPhase
   :members:
   :show-inheritance:
