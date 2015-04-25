r"""
=========================================================
Virtual Ply Model (:mod:`desicos.cppot.core.ply_model`)
=========================================================

.. currentmodule:: desicos.cppot.core.ply_model

Classes to create a virtual model of the ply pieces on an actual cone.

"""

import numpy as np

from desicos.constants import TOL
from desicos.cppot.core.geom import Point2D, Line2D, Polygon2D
from desicos.cppot.core.geom import wrap_to_pi, angle_in_range, circle_segment_area


class PlyPieceModel(object):
    """Abstract base class for all ply piece models

    This class encapsulates all functionality to create a virtual ply model
    based on the given parameters. Various methods are available to
    subsequently extract information about this virtual ply model.

    For the different ply piece shapes, subclasses should be made that define
    at least the method ``construct_single_ply_piece`` and possibly others.

    =====================  ==================================================
    Attribute              Description
    =====================  ==================================================
    ``cg``                 :class:`.ConeGeometry`, object that describes the
                           geometry of the cone.
    ``fiber_angle``        ``float``, nominal fiber angle in degrees.
    ``starting_position``  ``float``, radius in the flattened cone
                           ((s, phi)-coordinate system) where the origin line
                           (L0) of the basic ply piece intersects the
                           eta-axis.
    ``max_width``          ``float``, maximum width of a single ply piece.
    ``rel_ang_offset``     ``float`` optional, default is 0. Relative angular
                           offset (0..1) to be used when positioning the
                           pieces in this ply. Can be used to avoid
                           overlapping of seams, when multiple plies have the
                           same fiber angle.
    ``eccentricity``       ``float``, eccentricity parameter (range 0...1)
                           that controls the positioning of the ply piece
                           relative to the origin line.
                           Optional, the default value is:
                                a) if ``cc.stack[i] == 0`` -> 0.5
                                b) if ``cc.stack[i] > 0`` -> 0.0
                                c) if ``cc.stack[i] < 0`` -> 1.0
    ``base_piece``        :class:`PlyPiece`, base (prototype) ply piece,
                          with a nominal angle of 0. This ply piece is not
                          part of the layup, but used as a prototype to
                          construct all other ply pieces.
    ``ply_pieces``        ``list`` of :class:`PlyPiece`, a list containing
                          all ply pieces in the virtual cone model.
    ====================  ==================================================

    """
    def __init__(self, cg, fiber_angle, starting_position,
                 max_width, rel_ang_offset=0.0, eccentricity=None):
        self.cg = cg
        self.fiber_angle = fiber_angle
        self.starting_position = starting_position
        self.max_width = max_width
        self.rel_ang_offset = rel_ang_offset
        if eccentricity is not None:
            self.eccentricity = eccentricity
        elif abs(self.fiber_angle) < TOL:
            self.eccentricity = 0.5
        elif self.fiber_angle > 0:
            self.eccentricity = 0.0
        else:
            self.eccentricity = 1.0
        self.base_piece = None
        self.ply_pieces = []
        self._useful_polygon_cache = dict() # Cache for _useful_polygon

    def construct_single_ply_piece(self, fraction=1.0):
        """Construct a single ply piece.

        Parameters
        ----------
        fraction : float
            Optional, range (0, 1], default is 1.
            The newly constructed ply piece will normally span an angle
            ``delta_phi`` on the nominal circle (radius ``s_theta_nom``) from
            ``phi_nom_min`` to ``phi_nom_max``. When this parameter is set
            unequal to 1, ``delta_phi`` of the resulting ply piece will be the
            indicated fraction of the value it would normally have. This
            functionality is used to construct rest-pieces.

        Returns
        -------
        ply_piece : :class:`.PlyPiece`
            The newly constructed ply piece.

        Notes
        -----
        This method is just to define the interface, implementation should be
        provided by a derived class.

        """
        raise NotImplementedError()

    def rebuild(self):
        """Rebuild the model, actually constructing all ply pieces

        """
        self._useful_polygon_cache = dict()
        base_piece = self.construct_single_ply_piece()
        ply_pieces = []
        self.base_piece = base_piece
        self.ply_pieces = ply_pieces
        # Nominal angle covered per piece
        delta_phi = base_piece.phi_nom_max - base_piece.phi_nom_min
        # Total angle to cover
        phi_min = 0
        phi_max = 2 * np.pi * self.cg.sin_alpha
        rest_piece_fraction = self.num_pieces() % 1.0
        rest_piece_todo = TOL < rest_piece_fraction < (1.0 - TOL)

        offset_phi = self.rel_ang_offset*delta_phi
        # Go backwards as far as needed,
        # use the fact that the base piece has phi_nom = 0,
        # so new_piece.phi_limit_max = current_phi + base_piece.phi_limit_max
        current_phi = offset_phi
        while current_phi + base_piece.phi_limit_max > phi_min:
            ply_pieces.append(base_piece.copy_rotated(current_phi))
            current_phi -= delta_phi
        # reverse the list to maintain CCW order, not strictly necessary but nice
        ply_pieces.reverse()

        # Go forwards as far as needed
        # use the fact that the base piece has phi_nom = 0,
        # so new_piece.phi_limit_min = current_phi + base_piece.phi_limit_min
        current_phi = offset_phi + delta_phi
        while current_phi + base_piece.phi_limit_min <= phi_max:
            ply_pieces.append(base_piece.copy_rotated(current_phi))
            # Insert rest piece just after the first piece that is entirely
            # above phi = 0
            if rest_piece_todo and ply_pieces[-1].phi_limit_min > 0:
                rest_piece_todo = False
                current_phi += base_piece.phi_nom_max - rest_piece_fraction*base_piece.phi_nom_min
                rest_piece = self.construct_single_ply_piece(fraction=rest_piece_fraction)
                rest_piece = rest_piece.copy_rotated(current_phi)
                ply_pieces.append(rest_piece)
                current_phi += rest_piece_fraction*base_piece.phi_nom_max - base_piece.phi_nom_min
            else:
                current_phi += delta_phi
        assert not rest_piece_todo

    def local_orientation(self, eta, zeta):
        """Determine the local fiber orientation at a given point. If the
        given point is not inside any ply piece, NaN is returned. If there are
        multiple overlapping ply pieces, the orientation belonging to one of
        them (the first in the ply piece list) is returned.

        Parameters
        ----------
        eta : float
            Horizontal coordinate of point, in the coordinate system of the
            unfolded cone.
        zeta : float
            Vertical coordinate of point, in the coordinate system of the
            unfolded cone.

        Returns
        -------
        local_angle : float
            Local fiber angle at the given point in the given ply, in degrees.

        """
        point = Point2D(eta, zeta)
        phi = point.angle()
        for pp in self.ply_pieces:
            if pp.contains_point(point, phi):
                return self.fiber_angle + pp.angle_deviation(point)
        return np.nan

    def all_local_orientations(self, eta, zeta):
        """Determine the local fiber orientations of all plies at a point.

        Parameters
        ----------
        eta : float
            Horizontal coordinate of point, in the coordinate system of the
            unfolded cone.
        zeta : float
            Vertical coordinate of point, in the coordinate system of the
            unfolded cone.

        Returns
        -------
        local_angles : list
            Lists of floats representing the local fiber angle of each
            (possibly overlapping) ply piece at this point, in degrees.

        """

        point = Point2D(eta, zeta)
        phi = point.angle()
        return len([self.fiber_angle + pp.angle_deviation(point)
                for pp in self.ply_pieces if pp.contains_point(point, phi)])

    def local_num_pieces(self, eta, zeta):
        """Determine the local number of overlapping pieces at a given point.

        Parameters
        ----------
        eta : float
            Horizontal coordinate of point, in the coordinate system of the
            unfolded cone.
        zeta : float
            Vertical coordinate of point, in the coordinate system of the
            unfolded cone.

        Returns
        -------
        num_pieces : int
            Number of overlapping pieces at the given point in the ply

        """
        return len(self.all_local_orientations(eta, zeta))

    def _useful_polygon(self, ply_piece=None):
        # Internal function to get a polygon representing the section of a
        # ply piece that overlaps with the useful area of the cone (between s2
        # and s3). Additionally, return the points on s2 and s3 separately.
        if ply_piece is None:
            ply_piece = self.base_piece
        # Re-use cached value if possible, for performance
        if ply_piece in self._useful_polygon_cache:
            return self._useful_polygon_cache[ply_piece]

        P1, P2, P3, P4 = ply_piece.polygon.points()
        phi_nom = ply_piece.phi_nom
        L1 = Line2D.from_points(P1, P2)
        L3 = Line2D.from_points(P3, P4)
        points = []

        # Define a quick helper function that will be useful later
        def make_intersection(L, s):
            return L.intersection_circle_near(s, Point2D.from_polar(s, phi_nom))

        # Add the intersection with s2 near P1
        if P1.norm() > self.cg.s2:
            # P1 is inside the useful area, add it as well
            L4 = Line2D.from_points(P4, P1)
            points.append(make_intersection(L4, self.cg.s2))
            points.append(P1)
        else:
            # P1 is outside the useful area
            points.append(make_intersection(L1, self.cg.s2))

        # Add the intersection points with s3
        pts_on_s3 = (make_intersection(L1, self.cg.s3),
                     make_intersection(L3, self.cg.s3))
        points.extend(pts_on_s3)

        # Add the intersection with s2 near P4
        if P4.norm() > self.cg.s2:
            # P4 is inside the useful area, add it as well
            points.append(P4)
            L4 = Line2D.from_points(P4, P1)
            points.append(make_intersection(L4, self.cg.s2))
        else:
            # P4 is outside the useful area
            points.append(make_intersection(L3, self.cg.s2))

        pts_on_s2 = (points[0], points[-1])
        retval = (Polygon2D(points), pts_on_s2, pts_on_s3)
        self._useful_polygon_cache[ply_piece] = retval
        return retval

    def corner_orientations(self):
        """Get the fiber orientations at all corners of the useful area,
        which is the area between radii s2 and s3.

        Returns
        -------
        corner_orientations : list
            Fiber angles (in degrees) at the four useful corner points of
            the base ply piece. The order of values matches P1, P2, P3, P4.
        """
        _, pts_on_s2, pts_on_s3 = self._useful_polygon()
        # Change the order to match P1, P2, P3, P4
        points = pts_on_s2[:1] + pts_on_s3 + pts_on_s2[1:]
        return [self.fiber_angle + self.base_piece.angle_deviation(point) for point in points]

    def num_pieces(self):
        """Determine the total number of pieces needed to fully cover the cone.

        Returns
        -------
        num_pieces : float
            The number of needed pieces, as a float. The fractional part
            indicates the size of the 'rest piece' that is needed.

        """
        delta_phi = self.base_piece.phi_nom_max - self.base_piece.phi_nom_min
        return 2*np.pi*self.cg.sin_alpha / delta_phi

    def edge_lengths(self):
        """Get the lengths of the edges of the (base) ply piece.

        Returns
        -------
        edge_lengths : list
            List of edge lengths (L1 to L4)

        """
        points = list(self.base_piece.polygon.points())
        NUM = 4
        assert len(points) == NUM
        return [(points[i] - points[(i+1) % NUM]).norm() for i in range(NUM)]

    def ratio_continuous_fibers(self):
        """Get the ratio of continuous fibers, i.e. the fraction of the fibers
        at the bottom edge (radius s3) that reach the top edge (radius s2).

        Returns
        -------
        ratio : float
            The ratio of continuous fibers

        """
        _, pts_on_s2, pts_on_s3 = self._useful_polygon()
        th_nom = np.radians(self.fiber_angle)
        cont_length_1 = Line2D.from_point_angle(pts_on_s2[0], th_nom).distance_point(pts_on_s2[1])
        cont_length_2 = Line2D.from_point_angle(pts_on_s3[0], th_nom).distance_point(pts_on_s3[1])
        return cont_length_1 / cont_length_2

    def ply_piece_area(self):
        """Get the area of a single ply piece that is on the free cone area,
        i.e. between radii s2 and s3.

        Returns
        -------
        area : float
            The aforementioned area

        """
        poly, pts_on_s2, pts_on_s3 = self._useful_polygon()
        # Correct the area of the _useful_polygon to account for the arcs
        s2_angle = abs(pts_on_s2[0].angle() - pts_on_s2[1].angle())
        s3_angle = abs(pts_on_s3[0].angle() - pts_on_s3[1].angle())
        area_s2 = circle_segment_area(self.cg.s2, s2_angle)
        area_s3 = circle_segment_area(self.cg.s3, s3_angle)
        return poly.area() - area_s2 + area_s3

    def effective_area(self, ply_piece=None, max_angle_dev=2.0):
        """Get the effective area of a single ply piece. This is the area on
        useful section of the cone, where the deviation of the fiber angle
        is less than a given maximum.

        Parameters
        ----------
        ply_piece : :class:`PlyPiece`, optional
            Ply piece to get the effective area for. If not set, the base
            piece is used.
        max_angle_dev : float, optional
            Maximum deviation from the nominal fiber angle to consider
            the material 'effective'. In degrees.

        Returns
        -------
        out : tuple
            2-tuple, where ``out[0]`` is the effective surface area and
            ``out[1]`` is the corresponding polygon.

        Notes
        -----
        Note that the polygon has straight edges, while the calculation of
        the effective area takes into account that some edges of the effective
        area may be arc sections.

        """
        if ply_piece is None:
            ply_piece = self.base_piece
        poly, pts_on_s2, pts_on_s3 = self._useful_polygon(ply_piece)
        # Construct lines through those corner points of the polygon,
        # that are on s2/s3. They will be useful later
        line_s2 = Line2D.from_points(*pts_on_s2)
        line_s3 = Line2D.from_points(*pts_on_s3)

        # Lines to cut away the non-effective area
        cut_line_1 = Line2D.from_point_angle(Point2D(0., 0.),
            ply_piece.phi_nom - np.radians(max_angle_dev))
        cut_line_2 = Line2D.from_point_angle(Point2D(0., 0.),
            ply_piece.phi_nom + np.pi + np.radians(max_angle_dev))
        # Slice the polygon, with some corrections
        for cut_line in (cut_line_1, cut_line_2):
            outp = []
            for p in poly.slice_line(cut_line).points():
                # Polygon intersection can result in points that are not
                # exactly on circles s2/s3, while they should be. Correct that.
                if cut_line.distance_point(p) < TOL:
                    if line_s2.distance_point(p) < TOL:
                        p = cut_line.intersection_circle_near(self.cg.s2, p)
                    elif line_s3.distance_point(p) < TOL:
                        p = cut_line.intersection_circle_near(self.cg.s3, p)
                outp.append(p)
            poly = Polygon2D(outp)

        # Calculate area
        area = poly.area()
        # Correct polygon area for arc sections s2/s3, if needed
        pts_on_s2 = [p for p in poly.points() if abs(p.norm() - self.cg.s2) < TOL]
        if len(pts_on_s2) >= 2:
            angles = [p.angle() for p in pts_on_s2]
            area -= circle_segment_area(self.cg.s2, max(angles) - min(angles))
        pts_on_s3 = [p for p in poly.points() if abs(p.norm() - self.cg.s3) < TOL]
        if len(pts_on_s3) >= 2:
            angles = [p.angle() for p in pts_on_s3]
            area += circle_segment_area(self.cg.s3, max(angles) - min(angles))

        return area, poly


class TrapezPlyPieceModel(PlyPieceModel):
    """Sub-class of ``PlyPieceModel``, for shape A (trapezium)

    """
    def construct_single_ply_piece(self, fraction=1.0):
        """Construct a ply piece for shape A (trapezium)"""
        th_nom = np.radians(self.fiber_angle)
        # Step 1: Define origin line L0
        origin_point = Point2D(self.starting_position, 0.0)
        L0 = Line2D.from_point_angle(origin_point, th_nom)
        # Step 2: Define line L2, perpendicular to L0, tangent to circle s4
        tangent_point = Point2D.from_polar(self.cg.s4, th_nom)
        L2 = Line2D.from_point_angle(tangent_point, th_nom + np.pi/2)
        P0 = L0.intersection_line(L2)

        # Step 3: Position P2 and P3 based on max_width and eccentricity
        P2_dist = self.max_width * self.eccentricity
        P3_dist = self.max_width * (1 - self.eccentricity)
        P2 = P0 + Point2D.from_polar(P2_dist, L2.angle())
        P3 = P0 + Point2D.from_polar(P3_dist, L2.angle() + np.pi)

        # Step 4: Calculate the spanned angle (both deltas should be >= 0)
        T2 = L0.intersection_circle_near(P2.norm(), P0)
        T3 = L0.intersection_circle_near(P3.norm(), P0)
        delta_phi_1 = fraction*(P2.angle() - T2.angle())
        delta_phi_2 = fraction*(T3.angle() - P3.angle())

        # Step 5: Calculate the side lines L1 and L3
        L1 = L0.rotate(delta_phi_1)
        L3 = L0.rotate(-delta_phi_2)
        near_pt = Point2D(self.cg.s1, 0)
        P1a = L1.intersection_circle_near(self.cg.s1, near_pt)
        P4a = L3.intersection_circle_near(self.cg.s1, near_pt)
        # Redefine P2 and P3 if needed (for rest pieces)
        if fraction != 1.0:
            P2 = L2.intersection_line(L1)
            P3 = L2.intersection_line(L3)

        # Step 6: Construct L4, parallel to L2, through either P1a or P4a,
        # whichever is furthest from L2
        if L2.distance_point(P1a) > L2.distance_point(P4a):
            L4_through_point = P1a
        else:
            L4_through_point = P4a
        L4 = Line2D.from_point_angle(L4_through_point, L2.angle())
        # now redefine P1 and P4 as the intersection points:
        P1b = L4.intersection_line(L1)
        P4b = L4.intersection_line(L3)

        ip_L1_L3 = L1.intersection_line(L3)
        if L2.distance_point(ip_L1_L3) < L2.distance_point(P4b):
            # Line segments L1 and L3 intersect within the polygon, so we have
            # a 'hourglass' shape. Move P1 and P4 to the intersection point,
            # effectively forming a triangle. We could just drop P4, if not
            # for some other code expeccting 4-point polygons.
            P1, P4 = ip_L1_L3, ip_L1_L3
        else:
            P1, P4 = P1b, P4b

        # Step 7: Return the final ply piece
        return PlyPiece(Polygon2D((P1, P2, P3, P4)), 0.0, -delta_phi_2, delta_phi_1)


class Trapez2PlyPieceModel(PlyPieceModel):
    """Sub-class of ``PlyPieceModel``, for shape B (trapezium with one overlap)

    """
    def construct_single_ply_piece(self, fraction=1.0):
        """Construct a ply piece for shape A (trapezium)"""
        th_nom = np.radians(self.fiber_angle)
        # Step 1: Define origin line L0
        origin_point = Point2D(self.starting_position, 0.0)
        L0 = Line2D.from_point_angle(origin_point, th_nom )
        # Step 2: Define line L2, perpendicular to L0, tangent to circle s4
        tangent_point = Point2D.from_polar(self.cg.s4, th_nom)
        L2 = Line2D.from_point_angle(tangent_point, th_nom + np.pi/2)
        P0 = L0.intersection_line(L2)

        # Step 3: Position P2 and P3 based on max_width and eccentricity
        P2_dist = self.max_width * self.eccentricity
        P3_dist = self.max_width * (1 - self.eccentricity)
        P2 = P0 + Point2D.from_polar(P2_dist, L2.angle())
        P3 = P0 + Point2D.from_polar(P3_dist, L2.angle() + np.pi)

        # Step 4: Calculate a rough estimate of the spanned angle
        delta_phi_1 = (P2.angle() - P0.angle())
        delta_phi_2 = (P0.angle() - P3.angle())
        ip_L0_s2 = L0.intersection_circle_near(self.cg.s2, origin_point)
        ip_L0_s4 = L0.intersection_circle_near(self.cg.s4, origin_point)

        ratio = 0.0
        REQ_RATIO = 2.0
        # Step 5: Iterate until the ratio of spanned angles on s4 and s2 is (nearly) correct
        while abs(ratio - REQ_RATIO) > TOL:
            delta_phi_on_s2 = REQ_RATIO * (delta_phi_1 + delta_phi_2)
            ip_L1_s2 = ip_L0_s2.rotate(REQ_RATIO * delta_phi_1)
            ip_L3_s2 = ip_L0_s2.rotate(-REQ_RATIO * delta_phi_2)
            L1 = Line2D.from_points(ip_L1_s2, P2)
            L3 = Line2D.from_points(ip_L3_s2, P3)
            ip_L1_s4 = L1.intersection_circle_near(self.cg.s4, P0)
            ip_L3_s4 = L3.intersection_circle_near(self.cg.s4, P0)
            delta_phi_1 = ip_L1_s4.angle() - ip_L0_s4.angle()
            delta_phi_2 = ip_L0_s4.angle() - ip_L3_s4.angle()
            delta_phi_on_s4 = delta_phi_1 + delta_phi_2
            ratio = delta_phi_on_s2 / delta_phi_on_s4

        # Redefine P2 and P3 if needed (for rest pieces)
        if fraction != 1.0:
            ip_L1_s2 = ip_L1_s2.rotate((fraction - 1.0) * delta_phi_1)
            ip_L3_s2 = ip_L3_s2.rotate((1.0 - fraction) * delta_phi_2)
            # Apply an additional rotation to avoid having more than one overlap
            ip_L3_s2 = ip_L3_s2.rotate(delta_phi_1 + delta_phi_2)
            ip_L1_s4 = ip_L1_s4.rotate((fraction - 1.0) * delta_phi_1)
            ip_L3_s4 = ip_L3_s4.rotate((1.0 - fraction) * delta_phi_2)
            L1 = Line2D.from_points(ip_L1_s2, ip_L1_s4)
            L3 = Line2D.from_points(ip_L3_s2, ip_L3_s4)
            delta_phi_1 *= fraction
            delta_phi_2 *= fraction

        # Step 6: redefine P1 to P4 as the intersection points
        L4 = Line2D.from_point_angle(Point2D(0.0, 0.0), L2.angle())
        P1 = L1.intersection_line(L4)
        P2 = L2.intersection_line(L1)
        P3 = L3.intersection_line(L2)
        P4 = L4.intersection_line(L3)

        # Step 7: Return the final ply piece
        return PlyPiece(Polygon2D((P1, P2, P3, P4)), 0.0, -delta_phi_2, delta_phi_1)


class RectPlyPieceModel(PlyPieceModel):
    """Sub-class of ``PlyPieceModel``, for shape C (rectangle)

    """
    def construct_single_ply_piece(self, fraction=1.0):
        """Construct a ply piece for shape C (rectangle)"""
        th_nom = np.radians(self.fiber_angle)
        # Define origin line L0
        origin_point = Point2D(self.starting_position, 0.0)
        L0 = Line2D.from_point_angle(origin_point, th_nom)
        # Define line L4
        L4 = Line2D.from_point_angle(Point2D(0.0, 0.0), th_nom + np.pi/2)
        ip_L0_L4 = L0.intersection_line(L4)

        # Construct P1 and P4
        P1_dist = self.max_width * self.eccentricity
        P4_dist = self.max_width * (1 - self.eccentricity)
        P1 = ip_L0_L4 + Point2D.from_polar(P1_dist, L4.angle())
        P4 = ip_L0_L4 + Point2D.from_polar(P4_dist, L4.angle() + np.pi)

        # Construct side lines L1, L3, parallel to L0
        L1 = Line2D.from_point_angle(P1, L0.angle())
        L3 = Line2D.from_point_angle(P4, L0.angle())
        # Intersection points L0, L1, L3 with circle
        P0 = L0.intersection_circle_near(self.cg.s4, origin_point)
        P2 = L1.intersection_circle_near(self.cg.s4, P0)
        P3 = L3.intersection_circle_near(self.cg.s4, P0)

        # Handle creation of rest pieces, with fraction < 1.0
        delta_phi_1 = (P2.angle() - P0.angle())
        delta_phi_2 = (P0.angle() - P3.angle())
        if fraction != 1.0:
            P2 = P2.rotate((fraction - 1.0) * delta_phi_1)
            P3 = P3.rotate((1.0 - fraction) * delta_phi_2)
            L1 = Line2D.from_point_angle(P2, L1.angle())
            L3 = Line2D.from_point_angle(P3, L3.angle())
            P1 = L4.intersection_line(L1)
            P4 = L4.intersection_line(L3)
            delta_phi_1 *= fraction
            delta_phi_2 *= fraction

        # Construct L2 through P2 or P3, whichever is furthest from L4
        # Adjust the other point
        if L4.distance_point(P2) > L4.distance_point(P3):
            L2 = Line2D.from_point_angle(P2, L4.angle())
            P3 = L2.intersection_line(L3)
        else:
            L2 = Line2D.from_point_angle(P3, L4.angle())
            P2 = L2.intersection_line(L1)

        # Return the final ply piece
        return PlyPiece(Polygon2D((P1, P2, P3, P4)), 0.0, -delta_phi_2, delta_phi_1)


class PlyPiece(object):
    r"""PlyPiece object

    Carries all the information about a single piece of ply in the layup of a
    cone, with a defined size and orientation.

    =====================  ==================================================
    Attributes             Description
    =====================  ==================================================
    ``polygon``            ``Polygon2D``, containing the geometry of the
                           ply piece.
    ``phi_nom``            ``float``, angle at which the origin line (L0) of
                           the ply piece intersects the circle with radius
                           ``starting_position``
    ``phi_nom_min``        ``float``, smallest angle phi that is contained
                           within this ply piece at radius ``starting_position``
    ``phi_nom_max``        ``float``, largest angle phi that is contained
                           within this ply piece at radius ``starting_position``
    ``phi_limit_min``      ``float``, minimum value of phi for any of the
                           points in ``polygon``. Optional, will be calculated
                           if not supplied to the constructor.
    ``phi_limit_max``      ``float``, minimum value of phi for any of the
                           points in ``polygon``. Optional, will be calculated
                           if not supplied to the constructor.
    =====================  ==================================================

    Notes
    -----
    On the nominal circle (radius ``starting_position``), this ply piece occupies
    the range ``phi_nom_min``...``phi_nom_max``.

    For all points in this ply piece, the inequality
    ``phi_limit_min <= phi <= phi_limit_max`` should hold.

    """
    def __init__(self, polygon, phi_nom, phi_nom_min, phi_nom_max, phi_limit_min=None, phi_limit_max=None):
        self.polygon = polygon
        self.phi_nom = phi_nom
        self.phi_nom_min = phi_nom_min
        self.phi_nom_max = phi_nom_max

        # If phi_limit_min/max are not set explicitly, assign them based on the
        # minimal resp. maximal angle of the points in the polygon
        if phi_limit_min is None:
            self.phi_limit_min = min(p.angle() for p in self.polygon.points())
        else:
            self.phi_limit_min = phi_limit_min
        if phi_limit_max is None:
            self.phi_limit_max = max(p.angle() for p in self.polygon.points())
        else:
            self.phi_limit_max = phi_limit_max


    def copy_rotated(self, rotate_angle):
        """Create a copy of this ply piece, which is rotated by a certain angle.

        Parameters
        ----------
        rotate_angle : float
            Angle of new ply piece with respect to this one, in radians

        Returns
        -------
        new_piece : :class:`.PlyPiece`
            Rotated ply piece

        """
        return PlyPiece(self.polygon.rotate(rotate_angle),
                        self.phi_nom + rotate_angle,
                        self.phi_nom_min + rotate_angle,
                        self.phi_nom_max + rotate_angle,
                        self.phi_limit_min + rotate_angle,
                        self.phi_limit_max + rotate_angle)


    def angle_deviation(self, point):
        """Get the deviation between the local and nominal fiber angle at a certain point

        Parameters
        ----------
        point : Point2D
            Cartesian coordinates of the point. These are in the coordinate
            system of the unfolded cone, so (eta, zeta) (as floats).

        Returns
        -------
        angle_diff : float
            Local minus nominal fiber angle at this point, in degrees

        """
        return np.degrees(wrap_to_pi(self.phi_nom - point.angle()))


    def contains_point(self, point, phi=None):
        """Check if a point is contained in this ply piece

        Parameters
        ----------
        point : Point2D
            The point to check. This is in the coordinate
            system of the unfolded cone, so (eta, zeta).
        phi : float
            Angle corresponding to ``point``. Parameter is optional, but
            passing it from the caller can help performance.

        Returns
        -------
        cointains_point : bool
            True if the point is in this ply piece, false otherwise. For
            points exactly on the edge of the ply piece, resuls are undefined.

        """
        if phi is not None and not angle_in_range(phi, self.phi_limit_min, self.phi_limit_max):
            return False
        return self.polygon.contains_point(point)
