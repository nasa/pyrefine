Refine Multiscale Metric
========================
The multiscale metric looks reduce interpolation error in the solution.
For unsteady problems, the fixed point version can account for the change in
the solution over the time period of interest and form an averaged metric.

.. automodule:: pyrefine.refine.multiscale

Multiscale
----------

.. autoclass:: RefineMultiscale
   :members:
   :show-inheritance:

Fixed Point Multiscale
----------------------

.. autoclass:: RefineMultiscaleFixedPoint
   :members:
   :show-inheritance:
