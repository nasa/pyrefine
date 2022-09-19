#!/usr/bin/env python

# --uniform box {​​​​​​​​ceil,floor}​​​​​​​​ h0 decay_distance xmin ymin zmin xmax ymax zmax

# --uniform cyl {​​​​​​​​ceil,floor}​​​​​​​​ h0 decay_distance x1 y1 z1 x2 y2 z2 r1 r2
# has two radii and can be a point, line, cone, fustrum, or cylinder

class UniformRegionBase:
    def __init__(self):
        self.allowed_limits = ['ceil', 'floor']
        self._shape = 'undefined'
        self.limit = 'ceil'

        #: float: reference element length
        self.h0 = 0.1

        #: float: reference distance for quadratic decay of sizing constraint enforcement.
        #: Distance measured from shape surface (positive distance designates interior enforcement).
        self.decay_distance = 0.1

    @property
    def limit(self):
        """
        Type of sizing constraint enforced in region (ceil or floor).

        :type: str
        """
        return self._limit

    @limit.setter
    def limit(self, type):
        if type in self.allowed_limits:
            self._limit = type
        else:
            raise ValueError('Tried to set invalid limit type.  Only ceil of floor are allowed.')

    def get_commandline_arguments(self) -> str:
        """
        Returns the refine commandline arguments to activate a uniform refinement region.
        """
        raise NotImplementedError()


class UniformBox(UniformRegionBase):
    def __init__(self, xmin=0.0, ymin=0.0, zmin=0.0,
                 xmax=1.0, ymax=1.0, zmax=1.0):
        super().__init__()
        self._shape = 'box'
        self.set_box_bounds(xmin, ymin, zmin, xmax, ymax, zmax)

    def set_box_bounds(self, xmin, ymin, zmin, xmax, ymax, zmax):
        """
        Define Cartesian box extents by coordinates of two diagonally opposed points.
        """
        self.xmin = xmin
        self.ymin = ymin
        self.zmin = zmin

        self.xmax = xmax
        self.ymax = ymax
        self.zmax = zmax

    def get_commandline_arguments(self) -> str:
        return ' --uniform %s %s %f %f %f %f %f %f %f %f' % (
            self._shape, self.limit, self.h0, self.decay_distance,
            self.xmin, self.ymin, self.zmin, self.xmax, self.ymax, self.zmax)


class UniformCylinder(UniformRegionBase):

    def __init__(self, base_x=0.0, base_y=0.0, base_z=0.0, base_radius=1.0,
                 top_x=0.0, top_y=0.0, top_z=1.0, top_radius=1.0):
        """
        A cylinder, in general, has two radii and can degenerate to a point,
        line, cone, fustrum, or cylinder.  A cylinder is defined by the coordinates
        of two points and the radius at those point.  The radii of the cylinder are
        perpendicular to the axis connecting the two points.

        Parameters
        ----------
        base_x: float
            x coordinate of cylinder base center
        base_y: float
            y coordinate of cylinder base center
        base_z: float
            z coordinate of cylinder base center
        base_radius: float
            radius of cylinder base
        top_x: float
            x coordinate of cylinder top center
        top_y: float
            y coordinate of cylinder top center
        top_z: float
            z coordinate of cylinder top center
        top_radius: float
            radius of cylinder top
        """
        super().__init__()
        self._shape = 'cyl'
        self.set_base(base_x, base_y, base_z, base_radius)
        self.set_top(top_x, top_y, top_z, top_radius)

    def set_base(self, x, y, z, radius):
        """
        Set the center and radius of the bottom circle

        Parameters
        ----------
        x: float
            x coordinate
        y: float
            y coordinate
        z: float
            z coordinate
        radius: float
            radius of face
        """
        self.x1 = x
        self.y1 = y
        self.z1 = z
        self.r1 = radius

    def set_top(self, x, y, z, radius):
        """
        Set the center and radius of the top circle

        Parameters
        ----------
        x: float
            x coordinate
        y: float
            y coordinate
        z: float
            z coordinate
        radius: float
            radius of face
        """
        self.x2 = x
        self.y2 = y
        self.z2 = z
        self.r2 = radius

    def get_commandline_arguments(self) -> str:
        return ' --uniform %s %s %f %f %f %f %f %f %f %f %f %f' % (
            self._shape, self.limit, self.h0, self.decay_distance,
            self.x1, self.y1, self.z1, self.x2, self.y2, self.z2, self.r1, self.r2)
