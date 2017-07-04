from __future__ import absolute_import

import numpy as np

from desicos.abaqus.apply_imperfections import change_thickness_ABAQUS
from desicos.conecylDB import update_imps


class TI(object):
    """Thickness Imperfection

    Assumes that a percentage variation of the laminate thickness can be
    represented by the same percentage veriation of each ply, i.e., each
    ply thickness is varied in order to reflect a given measured thickness
    imperfection field.

    """
    def __init__(self):
        super(TI, self).__init__()
        self.name = 'ti'
        self.imp_thick = ''
        self.number_of_sets = None
        self.stretch_H = False
        self.ncp = 5
        self.power_parameter = 2
        self.num_sec_z = 50
        self.scaling_factor = 1.
        self.thetadeg = 0.
        self.thetadegs = []
        self.pts = []
        self.index  = None
        self.use_theta_z_format = False
        # plotting options
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Scaling factor'
        self.elems_t = None
        self.t_set = None
        self.created = False

    def rebuild(self):
        self.name = 'TI_%02d_SF_%05d' % (self.index,
                        int(round(100*self.scaling_factor)))
        self.thetadegs = [self.thetadeg]
        self.pts = []

    def __setstate__(self, attrs):
        # Old versions had a bug where self.xaxis was set to 'amplitude'
        # Fix that during loading
        if attrs['xaxis'] == 'amplitude':
            attrs['xaxis'] = 'scaling_factor'
            attrs['xaxis_label'] = 'Scaling factor'
        self.__dict__.update(attrs)

    def calc_amplitude(self):
        """Calculates the thickness imperfection amplitude

        Amplitude measured as the biggest difference between each layup
        thickness and the nominal thickness of the Cone/Cylinder,
        considering only the layups that are not suppressed.

        .. note:: Must be called from Abaqus.

        Returns
        -------
        max_amp : float
            Maximum absolute imperfection amplitude.

        """
        if self.created:
            from abaqus import mdb

            cc = self.impconf.conecyl
            part = mdb.models[cc.model_name].parts[cc.part_name_shell]
            max_amp = 0.
            cc_total_t = sum(cc.plyts)
            for layup in part.compositeLayups.values():
                if not layup.suppressed:
                    layup_t = sum(p.thickness for p in layup.plies.values())
                    max_amp = max(max_amp, abs(layup_t-cc_total_t))

            return max_amp

    def create(self, force=False):
        """Creates the thickness imperfection

        The thickness imperfection is created assuming that each ply has
        the same contribution to the measured laminate thickness. Thus, a
        scaling factor is applied to the nominal thickness of each ply in
        order to macth the measured imperfection field.

        Parameters
        ----------
        force : bool, optional
            If ``True`` the thickness imperfection is applied even when it
            is already created.

        """
        if self.created:
            if force:
                cc = self.impconf.conecyl
                cc.created = False
                cc.rebuilt = False
                cc.create_model()
            else:
                return
        cc = self.impconf.conecyl
        imps, imps_theta_z, t_measured, R_best_fit, H_measured = update_imps()

        if self.use_theta_z_format:
            imperfection_file_name = imps_theta_z[self.imp_thick]['ti']
        else:
            imperfection_file_name = imps[self.imp_thick]['ti']

        H_measured = H_measured[self.imp_thick]
        R_best_fit = R_best_fit[self.imp_thick]
        t_measured = t_measured[self.imp_thick]
        cc = self.impconf.conecyl
        self.elems_t, self.t_set = change_thickness_ABAQUS(
                      imperfection_file_name = imperfection_file_name,
                      model_name = cc.model_name,
                      part_name = cc.part_name_shell,
                      stack = cc.stack,
                      t_model = sum(cc.plyts),
                      t_measured = t_measured,
                      H_model = cc.H,
                      H_measured = H_measured,
                      R_model = cc.rbot,
                      R_best_fit = R_best_fit,
                      number_of_sets = self.number_of_sets,
                      semi_angle = cc.alphadeg,
                      stretch_H = self.stretch_H,
                      scaling_factor = self.scaling_factor,
                      num_closest_points = self.ncp,
                      power_parameter = self.power_parameter,
                      num_sec_z = self.num_sec_z,
                      elems_t = self.elems_t,
                      t_set = self.t_set,
                      use_theta_z_format = self.use_theta_z_format)

        from desicos.abaqus.abaqus_functions import set_colors_ti
        set_colors_ti(cc)
        self.created = True
        print('%s amplitude = %f' % (self.name, self.calc_amplitude()))
        ffi = self.impconf.ffi
        if ffi is not None and ffi.created:
            # There is already a FFI, let it know about us
            ffi.update_after_tis()

        return self.elems_t, self.t_set

