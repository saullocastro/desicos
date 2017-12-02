from __future__ import absolute_import

import numpy as np

from desicos.constants import TOL
from desicos.abaqus.utils import vec_calc_elem_cg
from desicos.cppot.core.geom import ConeGeometry
from desicos.cppot.core.ply_model import TrapezPlyPieceModel
# The PlyPiece class was located here in some development versions of the
# PPI imperfection and CPPOT tool. Import it here (though it is not needed
# per se) to maintain save/load compatibility with then-created studies
from .imperfection import Imperfection


class PPI(Imperfection):
    r"""Ply Piece Imperfection

    Laminating a cone with a finite number of ply pieces causes deviations
    between the nominal fiber angle (e.g. 30 degrees) and the actual angle,
    which varies with the location on the cone. This imperfection can be used
    to include that effect in the simulation.

    =====================  ====================================================
    Attributes             Description
    =====================  ====================================================
    ``info``               ``list`` with info about the layup of this cone.
                           Length of the list should be at least equal to the
                           number of plies. Each entry is a ``dict``,
                           containing:

                            - ``starting_position``: ``float``, Radius in the
                              flattened cone ((s, phi)-coordinate system)
                              where the origin line (L0) of the basic ply
                              piece intersects the horizontal axis
                            - ``max_width``: ``float``, maximum width of a
                              single ply piece.
                            - ``rel_ang_offset``: ``float``, optional, default
                              is 0. Relative angular offset (0..1) to be used
                              when positioning the pieces in this ply. Used to
                              avoid overlapping of seams, when multiple plies
                              have the same orientation.
                            - ``eccentricity``: ``float``, eccentricity param
                              (range 0...1) that controls the positioning of
                              the ply piece relative to the origin line.
                              Optional, the default value is dependent on the
                              nominal fiber angle:
                                a) 0.5 if ``cc.stack[i] == 0``
                                b) 0.0 if ``cc.stack[i] > 0``
                                c) 1.0 if ``cc.stack[i] < 0``

    ``extra_height``       ``float``, extra height above and below the cone
                           height (`cc.H`) to consider in the ply placement
                           model.
    =====================  ====================================================

    Notes
    -----
    This imperfection only works for cones, not for cylinders.

    """
    def __init__(self, info, extra_height=0):
        super(PPI, self).__init__()
        self.info = info
        self.extra_height = extra_height
        self.models = []
        self.cone_geometry = None
        self.name = 'PPI'
        self.index = None
        self.max_deviation = 0
        self.xaxis = 'max_deviation'
        self.xaxis_label = 'Max angle deviation [deg]'

    def calc_amplitude(self):
        return self.max_deviation

    def __setstate__(self, attrs):
        # In some old (development) versions of the PPI, entries in 'info'
        # had different names. Fix that during loading, to keep compatibility
        ATTR_MAP = {'s_theta_nom': 'starting_position', 'max_w': 'max_width'}
        for info in attrs['info']:
            for old, new in ATTR_MAP.iteritems():
                if old in info and new not in info:
                    info[new] = info[old]
                    del info[old]
        self.__dict__.update(attrs)

    def rebuild(self):
        cc = self.impconf.conecyl
        self.cone_geometry = ConeGeometry.from_conecyl(cc, self.extra_height)
        if not cc.alphadeg > 0:
            raise ValueError('PlyPieceImperfection may only be used for cones, i.e. when alpha > 0')
        if len(cc.stack) > len(self.info):
            raise ValueError('Not enough info rows supplied for PlyPieceImperfection.')
        self.models = []
        self.max_deviation = 0

        for i, ply_info in enumerate(self.info):
            if 'starting_position' not in ply_info:
                raise ValueError("PlyPieceImperfection: Missing parameter " +
                    "'starting_position' for ply {0:02d}".format(i+1))
            if 'max_width' not in ply_info:
                raise ValueError("PlyPieceImperfection: Missing parameter " +
                    "'max_width' for ply {0:02d}".format(i+1))
            model = TrapezPlyPieceModel(self.cone_geometry, cc.stack[i], **ply_info)
            self.models.append(model)
            model.rebuild()
            angle_dev = max(abs(x - cc.stack[i]) for x in model.corner_orientations())
            self.max_deviation = max(self.max_deviation, angle_dev)

    def _create_orientation_fields(self, mod, elements):
        """Create, for each ply, a discrete field containing the local
        orientation at each element.

        Parameters
        ----------
        mod : Model
            Abaqus model to which the fields should be added
        elements :  MeshElementArray
            Set of elements that should be represented in the discrete field

        Returns
        -------
        fields : list
            List of DiscreteFields, one for each ply.

        .. note:: Must be called from Abaqus.
        """
        from abaqusConstants import SCALAR
        cc = self.impconf.conecyl
        fields = []
        coords = vec_calc_elem_cg(elements)
        el_ids = map(int, coords[:,3])
        for i, angle in enumerate(cc.stack):
            field_name = 'ply_%02d_field' % (i+1)
            values = self.fiber_orientation(i, coords)
            if np.nan in values:
                raise ValueError('Invalid PPI parameters: not all points are covered by ply pieces')
            field = mod.DiscreteField(
                        name=field_name,
                        defaultValues=(angle, ),
                        fieldType=SCALAR,
                        data=[('', 1, el_ids, values)])
            fields.append(field)
        return fields

    def create(self):
        """Actually create the imperfection

        This modifies all composite layups to replace their existing (constant)
        ply orientations with values that are defined by a discrete field.

        .. note:: Must be called from Abaqus.

        """
        from abaqus import mdb
        from abaqusConstants import ANGLE_0, ROTATION_FIELD
        from desicos.abaqus.abaqus_functions import modify_composite_layup

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        part = mod.parts[cc.part_name_shell]
        fields = self._create_orientation_fields(mod, part.elements)

        def modify_orientation(index, kwargs):
            kwargs['orientationType'] = ANGLE_0
            kwargs['additionalRotationType'] = ROTATION_FIELD
            kwargs['additionalRotationField'] = fields[index].name
            kwargs.pop('orientation', None)
            kwargs.pop('orientationValue', None)
            kwargs.pop('angle', None)
            return kwargs

        for layup_name, layup in part.compositeLayups.items():
            if not layup.suppressed:
                modify_composite_layup(part, layup_name, modify_orientation)

    def fiber_orientation(self, ply_index, coords):
        """Determine the local fiber orientation at a set of coordinates,
        given in the global Cartesian (x, y, z) coordinate system. If points
        are not covered by any ply piece, NaN is returned for those

        Parameters
        ----------
        ply_index : int
            Index of the ply of interest
        coords : numpy.array
            Two-dimensional array containing one row per point and the x-, y-
            and z-coordinates of each point as columns.

        Returns
        -------
        thetas : numpy.array
            Local fiber angle at each given point in the ply, in degrees.

        """
        eta, zeta = self.gcs_to_unfolded(coords[:,0], coords[:,1], coords[:,2])
        return [self.models[ply_index].local_orientation(e, z) for e, z in zip(eta, zeta)]

    def gcs_to_unfolded(self, x, y, z):
        """Convert global xyz coordinates to the unfolded (eta, zeta)-csys.

        Parameters
        ----------
        x : float or numpy array
            X-coordinates in global Cartesian coordinate system
        y : float or numpy array
            Y-coordinates in global Cartesian coordinate system
        z : float or numpy array
            Z-coordinates in global Cartesian coordinate system

        Returns
        -------
        out : tuple
            A 2-tuple, where out[0] contains the eta-coordinate(s) and out[1]
            the zeta-coordinate(s) corresponding to the given point(s).

        Notes
        -----
        Input coordinates should be on the surface of the cone.

        """
        cg = self.cone_geometry
        r = np.sqrt(x**2 + y**2)
        theta = np.arctan2(y, x)
        # Calculate the distance from the projection of the centroid on the
        # cone (in the r,z-plane), to the bottom edge of the cone
        bot_dist = (cg.rbot - r) * cg.sin_alpha + z * cg.cos_alpha
        s = cg.rbot / cg.sin_alpha - bot_dist
        phi = theta % (2*np.pi) * cg.sin_alpha
        eta = s * np.cos(phi)
        zeta = s * np.sin(phi)
        return eta, zeta

    def unfolded_to_gcs(self, eta, zeta, approx_phi=0.0, cylindrical=False):
        """Convert unfolded (eta, zeta)-coordinates to the global coordinate system.

        Parameters
        ----------
        eta : float or numpy array
            Horizontal coordinates in the unfolded coordinate system.
        zeta : float or numpy array
            Vertical coordinates in the unfolded coordinate system.
        approx_phi : float, optional
            As an intermediate step, the (eta, zeta)-coordinates are converted
            to polar (s, phi)-coordinates. This transformation is multivalued,
            as (s, phi + 2pi) and such is also a valid result. Resolve this
            ambiguity by choosing the value of phi closest to approx_phi,
            so within the (approx_phi - pi, approx_phi + pi) range.
        cylindrical : bool, optional
            Whether to return output values in a Cartesian (if ``False``) or
            cylindrical (if ``True``) coordinate system. Default is ``False``.

        Returns
        -------
        out : tuple
            A 3-tuple, containing (depending on the parameter ``cylindrical``)
            either (x, y, z) or (r, theta, z)-coordinates.

        """
        cg = self.cone_geometry
        s = np.sqrt(eta**2 + zeta**2)
        phi = np.arctan2(zeta, eta)
        n_circ = np.round((approx_phi - phi) / (2*np.pi))
        phi += n_circ * (2*np.pi)
        r = s * cg.sin_alpha
        theta = phi / cg.sin_alpha
        z = (cg.s3 - s) * cg.cos_alpha
        if cylindrical:
            return r, theta, z
        else:
            return r*np.cos(theta), r*np.sin(theta), z

    def get_ply_lines(self, ply_index, center_theta_zero=True):
        """Obtain a series of lines that can be used to draw all ply pieces.

        Parameters
        ----------
        ply_index : int
            Index of ply to construct lines for.
        center_theta_zero : bool
            Plot the ply pieces in the -pi...pi range, instead of 0..2pi

        Returns
        -------
        lines : list
            List of lines. Each line is a 2-tuple (thetas, zs), containing
            a list of circumferential coordinates and a list of vertical
            coordinates of the points along the line.

        """
        lines = []
        for pp in self.models[ply_index].ply_pieces:
            # Skip duplicate ply pieces for plotting
            if not (-TOL <= pp.phi_nom < 2*np.pi*self.cone_geometry.sin_alpha - TOL):
                continue
            r, theta, z = self.unfolded_to_gcs(
                *pp.polygon.get_closed_line(100), approx_phi=pp.phi_nom, cylindrical=True)
            if center_theta_zero and pp.phi_nom > np.pi*self.cone_geometry.sin_alpha:
                theta -= 2*np.pi
            lines.append((theta, z))
        return lines
