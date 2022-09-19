Adaptation Driver
==================
The adaptatation driver orchestrates the adaptation components to perform the adaptation.

.. toctree::
   :maxdepth: 1

   adaptation_driver.rst

Adaptation Components
=====================
The components are responsible for performing the actions required to run a refine adaptation.

Component Base Classes
----------------------
The component base classes define how the driver and user interact with all versions of the particular component.
Class inhertiance is used to create particular versions that perform the task in different manners or use different
underlying codes.

.. toctree::
   :maxdepth: 1

   refine/base.rst
   controller/base.rst
   simulation/base.rst

Refine
------
The refine object performs the metric computation, the generation of new meshes, and interpolation of the solution onto the new mesh.
The methods to access this functionality are defined in :class:`~pyrefine.refine.base.RefineBase`.

.. toctree::
   :maxdepth: 1

   refine/multiscale.rst
   refine/goal_oriented.rst
   refine/uniform_regions.rst

.. _controller:

Controller
----------
The controller object updates any input files at the start of an adaptation cycle, schedules the complexity for the mesh adaptation step, and cleans up files at the end of cycle.
The methods to access this functionality are defined in :class:`~pyrefine.controller.base.ControllerBase`.

.. toctree::
   :maxdepth: 1

   controller/basic.rst
   controller/smooth_transition.rst
   controller/monitoring.rst
   controller/aoa_sweep.rst

FUN3D Simulations
-----------------
The simulation object performs the analysis required for the adaptation step.
The methods to access this functionality are defined in :class:`~pyrefine.simulation.base.SimulationBase`.

.. toctree::
   :maxdepth: 1

   fun3d_simulations/general.rst
   fun3d_simulations/adjoint.rst
   fun3d_simulations/time_domain.rst
   fun3d_simulations/flutter.rst

Post Processing
===============

Pyrefine comes with a small set of post-processing options.

.. toctree::
   :maxdepth: 1

   post_processing.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
