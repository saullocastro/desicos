from __future__ import absolute_import

import os

import numpy as np

from desicos.logger import warn
from desicos.conecylDB import update_imps
from desicos.abaqus.constants import *
from desicos.abaqus.apply_imperfections import (calc_translations_ABAQUS,
                                                translate_nodes_ABAQUS,
                                                translate_nodes_ABAQUS_c0)
def calc_msi_amplitude(cc, force=False):
    """Calculates the mid-surface imperfection of a ConeCyl model

    .. note:: Must be called from Abaqus.

    Parameters
    ----------
    cc : ConeCyl object
        The :class:`.ConeCyl` object already
    force : bool, optional
        Does not the check if the finite element model is already created.


    Returns
    -------
    max_amp : float
        The maximum absolute amplitude.

    """
    if not force and not cc.created_model:
        warn('The finite element for the input ConeCyl object is not created')
        return

    from abaqus import mdb

    part = mdb.models[cc.model_name].parts[cc.part_name_shell]
    coords = np.array([n.coordinates for n in part.nodes])
    xs, ys, zs = coords.T
    node_rs = (xs**2 + ys**2)**0.5
    pts = zs/cc.H
    rs, zs = cc.r_z_from_pt(pts)
    amps = (node_rs - rs) * np.cos(cc.alpharad)
    max_amp = max(np.absolute(amps))

    return max_amp

class MSI(object):
    r"""Mid-Surface Imperfection

    The imperfections are applied using both an inverse-weighted
    interpolation algorithm, detailed in :func:`.inv_weighted`, or a
    continuous fitting function, detailed in :func:`.calc_c0`.

    The following attributes of the :class:`.MSI` object control the
    inverse-weighted algorithm:

    ===================  =====================================================
    Attribute            Description
    ===================  =====================================================
    ``ncp``              ``int``, number of closest points
    ``power_parameter``  ``float``, power parameter
    ``r_TOL``            ``float``, percentage tolerance to ignore noisy
                         data, for example, when ``r_TOL=1.`` the points
                         with a radius `r > 1.1 R_{bot}`
    ===================  =====================================================

    Additional attributes are used to apply the imperfection into the
    finite element model when the inverse-weighted algorithm is selected.

    ======================  ==================================================
    Attribute               Description
    ======================  ==================================================
    ``imp_ms``              ``str``, an entry in the imperfection database,
                            if an entry with this string key is found, it
                            will overwrite the parameters: ``path,
                            R_best_fit, H_measured``
    ``path``                ``str``, full path to the imperfection file
    ``use_theta_z_format``  ``bool``, if the imperfection file is in the
                            `\theta, Z, imp` or in the `X, Y, Z` format
    ``R_measured``          ``float``, best fit radius obtained with
                            functions :func:`.best_fit_cylinder` or
                            :func:`.best_fit_cone`
    ``H_measured``          ``float``, height of the specimen for which the
                            imperfection file corresponds to
    ``scaling_factor``      ``float``, a scaling factor that is applied to
                            the imperfection amplitude
    ``sample_size``         Avoids a memory overflow during runtime for
                            large imperfection files
    ``rotatedeg``           ``float``, rotation angle in degrees telling
                            how much the imperfection pattern should be
                            rotated about the `X_3` (or `Z`) axis.
    ======================  ==================================================

    The following attributes of the :class:`.MSI` object control the
    continuous function-based algorithm:

    ===================  =====================================================
    Attribute            Description
    ===================  =====================================================
    ``c0``               ``np.ndarray``, coefficients giving the amplitude of
                         each term in the approximation function given by
                         ``funcnum``. If specified overwrites even ``imp_ms``

                         .. note:: The coefficients ``c0`` must be calculated
                                   already considering ``rotatedeg`` using
                                   function :func:`.calc_c0`

    ``m0``               ``int``, number of terms along the meridional
                         coordinate
    ``n0``               ``int``, number of terms alog the circumferential
                         coordinate
    ``funcnum``          ``int``, the base function used for the
                         approximation, as detailed in :func:`.calc_c0`
    ``scaling_factor``   ``float``, a scaling factor that is applied to
                         the imperfection amplitude
    ===================  =====================================================

    Additional parameters that govern how the imperfection pattern will look
    like in the finite element model:

    ===================  =====================================================
    Attribute            Description
    ===================  =====================================================
    ``ignore_bot_h``     Used to ignore nodes from the bottom resin ring. The
                         default value ``True`` will automatically obtain the
                         resin ring dimensions. Set to ``False`` or ``None``
                         if an imperfection pattern "extruded" to both edges
                         is the desired behavior
    ``ignore_top_h``     Similar to ``ignore_bot_h``, but for the top edge.
    ``stretch_H``        If the measured imperfection does not cover the whole
                         height it will be stretched. If
                         ``stretch_H is True``, ``ignore_bot_h`` and
                         ``ignore_top_h`` are automatically set to ``False``
    ===================  =====================================================

    """
    def __init__(self):
        super(MSI, self).__init__()
        self.name = 'msi'
        self.index  = None
        self.imp_ms = ''
        self.stretch_H = False
        self.r_TOL = 1.
        self.ncp = 5
        self.rotatedeg = 0.
        self.power_parameter = 2
        self.scaling_factor = 1.
        self.use_theta_z_format = True
        self.path = None
        self.c0 = None
        self.m0 = None
        self.n0 = None
        self.funcnum = None
        self.H_measured = None
        self.R_best_fit = None
        self.ignore_bot_h = True
        self.ignore_top_h = True
        self.sample_size = 2000000
        #TODO: include z_offset_bottom to calculate ignore_bot_h and
        #      ignore_top_h
        # plotting options
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Scaling factor'
        self.nodal_translations = None
        self.created = False
        self.thetadegs = []
        self.pts = []

    def __setstate__(self, attrs):
        # Old versions had a bug where self.xaxis was set to 'amplitude'
        # Fix that during loading
        if attrs['xaxis'] == 'amplitude':
            attrs['xaxis'] = 'scaling_factor'
            attrs['xaxis_label'] = 'Scaling factor'
        self.__dict__.update(attrs)

    def rebuild(self):
        cc = self.impconf.conecyl
        self.name = 'MSI_{0:02d}_SF_{1:05d}'.format(self.index,
                    int(round(100*self.scaling_factor)))
        self.thetadegs = []
        self.pts = []

        imps, imps_theta_z, t_measured, R_best_fit, H_measured = update_imps()
        if self.use_theta_z_format:
            if self.imp_ms in imps_theta_z.keys():
                self.path = imps_theta_z[self.imp_ms]['msi']
        else:
            if self.imp_ms in imps.keys():
                self.path = imps[self.imp_ms]['msi']
        if self.imp_ms in H_measured.keys():
            self.H_measured = H_measured[self.imp_ms]
        if self.imp_ms in R_best_fit.keys():
            self.R_best_fit = R_best_fit[self.imp_ms]
        if self.stretch_H:
            self.ignore_bot_h = False
            self.ignore_top_h = False
        if self.ignore_bot_h is True:
            if cc.resin_add_BIR or cc.resin_add_BOR:
                self.ignore_bot_h = cc.resin_bot_h
            else:
                self.ignore_bot_h = False
        if self.ignore_top_h is True:
            if cc.resin_add_TIR or cc.resin_add_TOR:
                self.ignore_top_h = cc.resin_top_h
            else:
                self.ignore_top_h = False

    def calc_amplitude(self):
        """Calculates the geometric imperfection of the finite element model

        .. note:: Must be called from Abaqus.

        Returns
        -------
        max_amp : float
            The maximum absolute amplitude.

        """
        if self.created:
            return calc_msi_amplitude(self.impconf.conecyl, force=True)
        else:
            warn('Mid-surface imperfection not created')

    def create(self, force=False):
        """Applies the mid-surface imperfection in the finite element model

        .. note:: Must be called from Abaqus.

        Parameters
        ----------
        force : bool, optional
            Creates the imperfection even when it is already created

        """
        from abaqus import mdb

        if self.created:
            if force:
                self.created = False
                self.create()
            else:
                return
        cc = self.impconf.conecyl
        if self.c0 is None:
            self.nodal_translations = translate_nodes_ABAQUS(
                              imperfection_file_name = self.path,
                              model_name = cc.model_name,
                              part_name = cc.part_name_shell,
                              H_model = cc.H,
                              H_measured = self.H_measured,
                              R_model = cc.rbot,
                              R_best_fit = self.R_best_fit,
                              semi_angle = cc.alphadeg,
                              stretch_H = self.stretch_H,
                              rotatedeg = self.rotatedeg,
                              scaling_factor = self.scaling_factor,
                              r_TOL = self.r_TOL,
                              num_closest_points = self.ncp,
                              power_parameter = self.power_parameter,
                              nodal_translations = self.nodal_translations,
                              use_theta_z_format = self.use_theta_z_format,
                              ignore_bot_h = self.ignore_bot_h,
                              ignore_top_h = self.ignore_top_h,
                              sample_size = self.sample_size)
        else:
            if self.rotatedeg:
                warn('"rotatedeg != 0", be sure you included this effect ' +
                     'when calculating "c0"')
            self.nodal_translations = translate_nodes_ABAQUS_c0(
                              m0 = self.m0,
                              n0 = self.n0,
                              c0 = self.c0,
                              funcnum = self.funcnum,
                              model_name = cc.model_name,
                              part_name = cc.part_name_shell,
                              H_model = cc.H,
                              semi_angle = cc.alphadeg,
                              scaling_factor = self.scaling_factor,
                              fem_meridian_bot2top = True,
                              ignore_bot_h = self.ignore_bot_h,
                              ignore_top_h = self.ignore_top_h)
        self.created = True
        print('%s amplitude = %f' % (self.name, self.calc_amplitude()))

        return self.nodal_translations


    def print_to_file(self, filename=None):
        if not filename:
            cc = self.impconf.conecyl.study_dir
            filename = os.path.join(cc, self.name + '.txt')
        print('Writing output file "%s" ...' % filename)
        keys = self.nodal_translations.keys()
        keys.sort()
        outfile = open(filename, 'w')
        for k in keys:
            original_coords = nodes_dict[k]
            translations = self.nodal_translations[k]
            new_coords = original_coords + translations * scaling_factor
            outfile.write('%d %f %f %f\n' % (k, new_coords[0],
                                                new_coords[1],
                                                new_coords[2]))
        outfile.close()

