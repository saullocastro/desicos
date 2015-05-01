r"""
===============================================
CPPOT-geometry (:mod:`desicos.cppot.core.geom`)
===============================================

.. currentmodule:: desicos.cppot.core.geom

Classes and functions to help with 2D geometrical operations.

"""

from collections import namedtuple
import numpy as np

# Save some lookup time for these often-used values
pi = np.pi
pi2 = 2*np.pi

def wrap_to_pi(angle):
    """Wrap an angle to within the range [-pi, pi), by adding multiples of 2*pi

    Parameters
    ----------
    angle : float
        The angle to wrap

    Returns
    -------
    new_angle : float
        Wrapped angle within the range [-pi, pi)

    """
    return (angle + pi) % pi2 - pi


def angle_in_range(angle, angle_min, angle_max):
    """Check if an angle is within the specified range (min..max)
    While taking care of all the (mod 2pi)-issues.

    Parameters
    ----------
    angle : float
        The angle to check
    min_angle : float
        The lower limit of the range
    max_angle : float
        The upper limit of the range

    Returns
    -------
    in_range : bool
        True iff the given angle is in range min_angle...max_angle

    """
    return (((angle - angle_min) % pi2) +
            ((angle_max - angle) % pi2)) < pi2


def circle_segment_area(radius, angle):
    """Calculate the area of a circle segment, which is a region bound by
    an arc (less than 180 deg) and a straight line connecting the end points
    of that arc.

    Parameters
    ----------
    radius : float
        Radius of the arc
    angle : float
        Angle (in radians) of the arc

    Returns
    -------
    area : float
        The calculated area

    Notes
    -----
    See http://en.wikipedia.org/wiki/Circular_segment

    """
    return 0.5*radius**2 * (angle - np.sin(angle))


class Point2D(namedtuple('Point2D', 'x y')):
    """Class representing a point on a two-dimensional plane
    It is based on ``namedtuple``, which allows both named attribute access
    (point.x) and iteration / indexing. Point2D instances are immutable after
    construction. Addition / subtraction operators are overloaded, as wel as
    pre-multiplying by a scalar.

    =========  ==========================================================
    Attribute  Description
    =========  ==========================================================
    ``x``      ``float``, Cartesian x-coordinate
    ``y``      ``float``, Cartesian y-coordinate
    =========  ==========================================================

    """

    __slots__ = () # As recommended by python docs, saves memory

    def __setstate__(self, dict):
        # Unpickling is done during creation
        assert self.x == dict['x']
        assert self.y == dict['y']

    def angle(self):
        """ Calculate the angle of this point in polar coordinates

        Returns
        -------
        angle : float
            The counterclockwise angle (in radians) from the positive x-axis

        """
        return np.arctan2(self.y, self.x)

    def norm(self):
        """Calculate distance of this point with respect to the origin.

        """
        return (self.x**2 + self.y**2)**0.5

    def distance(self, other):
        """Calculate Euclidean distance between two points.

        """
        assert isinstance(other, Point2D)
        return (self - other).norm()

    def rotate(self, angle):
        """Created a new point, rotated with respect to the origin.
        The original point remains untouched.

        Parameters
        ----------
        angle : float
            Angle (in radians) with which the point is to be rotated

        Returns
        -------
        new_point : :class:`Point2D`
            The newly constructed rotated point

        """
        return self.__class__.from_polar(self.norm(), self.angle() + angle)

    def __add__(self, other):
        """Addition operator, creates a new point at (x1+x2, y1+y2)

        """
        if not isinstance(other, Point2D):
            raise NotImplementedError()
        return self.__class__(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        """Subtraction operator, creates a new point at (x1-x2, y1-y2)

        """
        if not isinstance(other, Point2D):
            raise NotImplementedError()
        return self.__class__(self.x - other.x, self.y - other.y)

    def __rmul__(self, other):
        """Pre-multiplication by a scalar

        """
        if not isinstance(other, (int, float)):
            raise NotImplementedError()
        return self.__class__(self.x * other, self.y * other)

    @classmethod
    def from_polar(cls, norm, angle):
        """Class method, creates a point from polar coordinates

        Parameters
        ----------
        norm : float
            Distance from the origin
        angle : float
            The counterclockwise angle (in radians) from the positive x-axis

        Returns
        -------
        point : :class:`Point2D`
            The newly constructed point
        """
        return cls(norm * np.cos(angle), norm * np.sin(angle))


class Line2D(namedtuple('Line2D', 'a b c')):
    """Class representing a line on a two-dimensional plane
    It is based on ``namedtuple``, which allows both named attribute access
    (line.a) and iteration / indexing. Line2D instances are immutable after
    construction.

    The line is defined based on two equations:
    a*x + b*y = c
    a**2 + b**2 = 1
    The latter normalization constraint is enforced in ``__new__``

    =========  ==========================================================
    Attribute  Description
    =========  ==========================================================
    ``a``      ``float``, Line parameter in equation (a*x + b*y = c)
    ``b``      ``float``, Line parameter in equation (a*x + b*y = c)
    ``c``      ``float``, Line parameter in equation (a*x + b*y = c)
    =========  ==========================================================

    """
    __slots__ = () # As recommended by python docs, saves memory

    def __new__(cls, a, b, c):
        # Tuples are immutable after construction, so initialization
        # should be done in __new__ instead of __init__
        norm = (a**2 + b**2)**0.5
        return super(Line2D, cls).__new__(cls, a/norm, b/norm, c/norm)

    def direction(self):
        """Obtain a point representing a unit direction vector parallel to the
        line.

        Returns
        -------
        direction : :class:`Point2D`
            The requested unit direction vector
        """
        return Point2D(self.b, -self.a)

    def angle(self):
        """ Calculate the angle of this line with respect to the x-axis

        Returns
        -------
        angle : float
            The counterclockwise angle (in radians) from the positive x-axis

        """
        return self.direction().angle()

    def rotate(self, angle):
        """Created a new line, rotated with respect to the origin.
        The original line remains untouched.

        Parameters
        ----------
        angle : float
            Angle (in radians) with which the line is to be rotated

        Returns
        -------
        new_line : :class:`Line2D`
            The newly constructed rotated line

        """
        a, b, c = self
        a_new = a*np.cos(angle) - b*np.sin(angle)
        b_new = b*np.cos(angle) + a*np.sin(angle)
        return self.__class__(a_new, b_new, c)

    def distance_point(self, point):
        """Get the shortest Euclidean distance between this line and a point

        Parameters
        ----------
        point : :class:`Point2D`
            Point to find the distance to

        Returns
        -------
        distance : float
            The shortest distance from this line to the given point.

        """
        assert isinstance(point, Point2D)
        return np.abs(self.a*point.x + self.b*point.y - self.c)

    def point_on_right(self, point):
        """Check on which side of this line a point lies

        Parameters
        ----------
        point : :class:`Point2D`
            Point to check

        Returns
        -------
        on_right_side : bool
            ``True`` if the point is on the right side of this line (looking
            into the direction of ``self.direction()``), ``False`` otherwise.

        """
        return (self.a*point.x + self.b*point.y - self.c) > 0

    def intersection_line(self, other):
        """Get the intersection point of this line and another line

        Parameters
        ----------
        other : :class:`Line2D`
            Other line to find intersection point with

        Returns
        -------
        intersection_point : :class:`Point2D`
            The found intersection point

        Notes
        -----
        If no intersection point could be found, a ValueError is raised.
        This can happen when the lines are parallel.

        See also:
        http://en.wikipedia.org/wiki/Intersection_(Euclidean_geometry)#Two_lines

        """
        assert isinstance(other, Line2D)
        a1, b1, c1 = self
        a2, b2, c2 = other
        denominator = a1*b2 - a2*b1
        if denominator == 0:
            raise ValueError('Unable to find intersection of lines: Lines are identical or parallel')
        x = (c1*b2 - c2*b1) / denominator
        y = (a1*c2 - a2*c1) / denominator
        return Point2D(x, y)

    def all_intersections_circle(self, radius):
        """Get all intersection points of a line with a circle
        The center of the circle is presumed to be at the origin

        Parameters
        ----------
        radius : float
            Radius of circle

        Returns
        -------
        intersection_points : list of :class:`Point2D`
            List containing either 0, 1 or 2 intersection points

        Notes
        -----
        See also:
        http://en.wikipedia.org/wiki/Intersection_(Euclidean_geometry)#A_line_and_a_circle

        """
        a, b, c = self
        # The fact that a**2 + b**2 = 1 simplifies things a bit
        D = radius**2 - c**2

        # Line does not cut circle
        if D < 0:
            return []

        # Line cuts circle at exactly one point
        elif D == 0:
            x1 = a*c
            y1 = b*c
            return [Point2D(x1, y1)]

        # Line cuts circle at two points
        else: # D > 0
            sqrtD = np.sqrt(D)
            x1 = a*c + b*sqrtD
            y1 = b*c - a*sqrtD
            x2 = a*c - b*sqrtD
            y2 = b*c + a*sqrtD
            return [Point2D(x1, y1), Point2D(x2, y2)]

    def intersection_circle_near(self, radius, near_point):
        """Get the intersection of a line with a circle
        If there is more than one intersection point, it returns the
        intersection closest to near_point. If there is no intersection,
        a ValueError is raised.

        Parameters
        ----------
        radius : float
            Radius of circle
        nearby_point : :class:`Point2D`
            The intersection nearest to this point will be returned

        Returns
        -------
        intersection_point : :class:`Point2D`
            The found intersection point
        """
        assert isinstance(near_point, Point2D)
        ips = self.all_intersections_circle(radius)
        if len(ips) == 0:
            raise ValueError('Error finding intersection of line and circle: there is none')
        elif len(ips) == 1:
            return ips[0]
        elif len(ips) == 2:
            ip1, ip2 = ips
            d1 = (near_point.x - ip1.x)**2 + (near_point.y - ip1.y)**2
            d2 = (near_point.x - ip2.x)**2 + (near_point.y - ip2.y)**2
            return ip1 if d1 < d2 else ip2
        else:
            assert False # Should not be reached

    @classmethod
    def from_point_angle(cls, point, angle):
        """Class method, constructs a line based on a point and an angle

        Parameters
        ----------
        point : :class:`Point2D`
            Point that the line should go through
        angle : float
            The counterclockwise angle (in radians) between the line and the positive x-axis

        Returns
        -------
        line : :class:`Line2D`
            The constructed line

        """
        assert isinstance(point, Point2D)
        dir = Point2D.from_polar(1, angle)
        a = -dir.y
        b = dir.x
        c = a*point.x + b*point.y
        return cls(a, b, c)

    @classmethod
    def from_points(cls, point1, point2):
        """Class method, constructs a line based on two points

        Parameters
        ----------
        point1 : :class:`Point2D`
            First point that the line should go through
        point2 : :class:`Point2D`
            Second point that the line should go through

        Returns
        -------
        line : :class:`Line2D`
            The constructed line

        Notes
        -----
        If no line can be constructed, a ValueError is raised.
        This happens when the points are identical.

        See also:
        http://math.stackexchange.com/questions/422602/convert-two-points-to-line-eq-ax-by-c-0

        """
        assert isinstance(point1, Point2D)
        assert isinstance(point2, Point2D)
        if point1 == point2:
            raise ValueError('Unable to construct line between points: they are identical')
        dir = point2 - point1
        return cls.from_point_angle(point1, dir.angle())


class Polygon2D(tuple):
    """Class representing a polygon on a two-dimensional plane.
    It is assumed that polygons do not self-intersect

    Pass an iterable of ``Point2D``-objects to the constructor.
    Polygon2D instances are immutable after construction.

    Notes
    -----
    Even though this object if (currently) a tuple of its points, it is
    recommended to not rely on this. This to allow possible future changes to
    the underlying implementation.

    """
    __slots__ = () # As recommended by python docs, saves memory

    def points(self):
        """Get an iterator over all corner points in this polygon"""
        return iter(self)

    def area(self):
        """Calculate the area enclosed by this polygon.

        See also:
        http://en.wikipedia.org/wiki/Shoelace_formula

        """
        return 0.5*abs(sum(self[i-1].y*p.x - self[i-1].x*p.y for i, p in enumerate(self)))

    def contains_point(self, point):
        """Determine if a point is inside or outside the polygon

        Parameters
        ----------
        point : :class:`Point2D`
            Point to test

        Returns
        -------
        inside_polygon : bool
            ``True`` if the point is inside the polygon, ``False`` otherwise

        Notes
        -----
        The 'Ray casting' algorithm is used, since the 'interior angle'
        algorithm was found to be very slow.

        This method has not been verified to work correctly for special cases,
        such as the point being (almost) exactly on a vertex or line.

        """
        crossings = 0
        # We use a coordinate system with 'point' at the origin, so shift polygon
        shifted_polygon = [p - point for p in self]
        # Iterate over all connected pairs of points
        for i in range(len(shifted_polygon)):
            x1, y1 = shifted_polygon[i-1]
            x2, y2 = shifted_polygon[i]
            # The ray that we use is along the positive x-axis. Now check if the
            # line from (x1, y1) to (x2, y2) intersects the positive x-axis

            # First, check if the points are on different sides of the x-axis
            # Else, there is no intersection at all
            if (y1 > 0 and y2 <= 0) or (y1 < 0 and y2 >= 0):
                # Second, check that they intersect the x-axis at x >= 0
                if x1 + y1*(x2 - x1)/(y1 - y2) >= 0:
                    crossings += 1
        # Odd number of crossings -> point is inside
        return (crossings % 2) == 1

    def get_closed_line(self, num_points=1):
        """Get a closed line that can be used to plot this polygon.

        Parameters
        ----------
        num_points : int
            The number of points to use per edge. Default value is 1.

        Returns
        -------
        out : tuple
            out[0] contains a numpy array of x-coordinates, out[1] an array
            of y-coordinates. The first point in the polygon is repeated, such
            that plot(x, y) results in a closed polygon.

        """
        x = []
        y = []
        for i in range(len(self) - 1, -1, -1):
            x.append(np.linspace(self[i].x, self[i-1].x, (num_points+1) if i == 0 else num_points, endpoint=(i == 0)))
            y.append(np.linspace(self[i].y, self[i-1].y, (num_points+1) if i == 0 else num_points, endpoint=(i == 0)))
        return np.hstack(x), np.hstack(y)

    def slice_line(self, line):
        """Slice this polygon, returning only the section on the right side
        of the given line.

        Parameters
        ----------
        line : :class:`Line2D`
            Line to be used for slicing.

        Returns
        -------
        new_poly : :class:`Polygon2D`
            The (newly created) sliced polygon.

        """
        out = []
        for i, p in enumerate(self):
            if line.point_on_right(p) != line.point_on_right(self[i-1]):
                edge = Line2D.from_points(p, self[i-1])
                out.append(line.intersection_line(edge))
            if line.point_on_right(p):
                out.append(p)
        return self.__class__(out)

    def rotate(self, rotate_angle):
        """Create a new polygon, idential to this one but rotated around the
        origin by a certain angle.

        Parameters
        ----------
        rotate_angle : float
            Rotation angle to use, in radians

        Returns
        -------
        new_poly : :class:`Polygon2D`
            The (newly created) rotated polygon.

        """
        c = np.cos(rotate_angle)
        s = np.sin(rotate_angle)
        return self.__class__(Point2D(c*p[0] - s*p[1], s*p[0] + c*p[1]) for p in self)


class ConeGeometry(object):
    r"""ConeGeometry object

    Carries all the information about the geometry of a cone, plus some
    read-only accessors to calculate often-needed cone properties. These are
    all calculated on-the-fly, so no rebuild()-ing is necessary.

    ================  ==================================================
    Attribute         Description
    ================  ==================================================
    ``H``             ``float``, height of the free area of the cone.
    ``rbot``          ``float``, bottom radius of the cone
    ``alpharad``      ``float``, semi-vertex angle of the cone, in
                      radians. Must be between 0 and pi/2.
    ``extra_height``  ``float``, extra (support) height. A section with
                      this height is added along both the top and bottom
                      edge of the free cone. This represents the extra
                      material that is present during manufacturing.
    ================  ==================================================

    """
    def __init__(self, H, rbot, alpharad, extra_height):
        self.H = H
        self.rbot = rbot
        if not (0 < alpharad < np.pi/2):
            raise ValueError('Not a cone; required is 0 < alpha < 90 (degrees)')
        self.alpharad = alpharad
        self.extra_height = extra_height

    @classmethod
    def from_conecyl(cls, cc, extra_height):
        """Construct a ConeGeometry object based on an existing ConeCyl

        Parameters
        ----------
        cc : :class:`.ConeCyl`
            Existing cone to use. Must be a cone, i.e. alpha > 0.
        extra_height : float
            Extra support height for this model.

        Returns
        -------
        cg : :class:`.ConeGeometry`
            The constructed ConeGeometry object

        """
        return cls(cc.H, cc.rbot, cc.alpharad, extra_height)

    @property
    def sin_alpha(self):
        """Read-only property: Sine of the semi-vertex angle."""
        return np.sin(self.alpharad)

    @property
    def cos_alpha(self):
        """Read-only property: Cosine of the semi-vertex angle."""
        return np.cos(self.alpharad)

    @property
    def tan_alpha(self):
        """Read-only property: Tangent of the semi-vertex angle."""
        return np.tan(self.alpharad)

    @property
    def rtop(self):
        """Read-only property: Top radius of the cone."""
        return self.rbot - self.H * self.tan_alpha

    @property
    def L(self):
        """Read-only property: Meridional length."""
        return self.H / self.cos_alpha

    @property
    def s1(self):
        """Read-only property: Radius of top (support) edge in unfolded coordinates."""
        return self.rbot / self.sin_alpha - \
            (self.H + self.extra_height) / self.cos_alpha

    @property
    def s2(self):
        """Read-only property: Radius of top edge of the free cone in unfolded coordinates."""
        return self.rbot / self.sin_alpha - self.H / self.cos_alpha

    @property
    def s3(self):
        """Read-only property: Radius of bottom edge of the free cone in unfolded coordinates."""
        return self.rbot / self.sin_alpha

    @property
    def s4(self):
        """Read-only property: Radius of bottom (support) edge in unfolded coordinates."""
        return self.rbot / self.sin_alpha + self.extra_height / self.cos_alpha

    @property
    def cone_area(self):
        """Read-only property: Surface area of the free cone (supports excluded)."""
        return np.pi * (self.s3**2 - self.s2**2) * self.sin_alpha
