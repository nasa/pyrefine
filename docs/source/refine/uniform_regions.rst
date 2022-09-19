Uniform Refinement Regions
==========================
Uniform regions let you enforce size constraints in regoins of refine-generated meshes.
The regions can be boxes or cylinders where the cylinder can have different radii to generalize
it to a point, line, frustrum, cone, cylinder.
The base class defines the properties of the size constraint, and the two subclasses define the geometry.

Uniform regions are stored in the refine classes in the :attr:`~pyrefine.refine.base.RefineBase.uniform_regions` list of the refine objects.
They are added to the command line arguments when refine executes.

.. automodule:: pyrefine.refine.uniform_region


Base Class
----------

.. autoclass:: UniformRegionBase
   :members:
   :show-inheritance:

Box
---

.. autoclass:: UniformBox
   :members:
   :show-inheritance:

Cylinder
--------

.. autoclass:: UniformCylinder
   :members:
   :show-inheritance:
