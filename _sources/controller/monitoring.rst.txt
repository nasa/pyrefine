Quantity Monitoring Controllers
===============================
These controllers double the complexity once one or more monitored quantities has converged on the current complexity level.

FUN3D Force Monitoring Controller
---------------------------------

.. automodule:: pyrefine.controller.monitor_forces

.. autoclass:: ControllerMonitorForcesFUN3D
   :members:
   :show-inheritance:

FUN3D SFE Force Monitoring Controller
-------------------------------------
.. automodule:: pyrefine.controller.monitor_forces
   :noindex:

.. autoclass:: ControllerMonitorForcesSFE
   :members:
   :show-inheritance:

Monitoring Base Class
---------------------
The Monitor Quantity controller is the base class for controllers that schedule
the complexity based on convergence of some quantities.

.. automodule:: pyrefine.controller.monitor_quantity

.. autoclass:: ControllerMonitorQuantity
   :members:
   :show-inheritance:
