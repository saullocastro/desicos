import os
import __main__

import numpy as np

import desicos.abaqus.utils as utils
from desicos.abaqus.conecyl._imperfections import Imperfection
from desicos.abaqus.constants import *
from desicos.abaqus.apply_imperfections import change_thickness_ABAQUS
from desicos.conecylDB import update_imps

class TI(Imperfection):

    def __init__(self):
        super(TI, self).__init__()
        self.name = 'ti'
        self.imp_thick = ''
        self.number_of_sets = None
        self.stretch_H = False
        self.ncp = 5
        self.power_parameter = 2
        self.num_sec_z = 20
        self.scaling_factor = 1.
        self.pt = 1.
        self.index  = None
        self.use_theta_z_format = False
        # plotting options
        self.xaxis = 'amplitude'
        self.xaxis_label = 'Imperfection amplitude, mm'
        self.elems_t = None
        self.t_set = None
        self.created = False

    def rebuild(self):
        self.theta = 0.
        self.theta1 = 0.
        self.theta2 = 0.
        cc = self.impconf.conecyl
        self.r, self.z = cc.r_z_from_pt(self.pt)
        self.x, self.y, self.z = self.get_xyz()
        self.node = self.impconf.load_asymmetry.node
        self.name = 'TI_%02d_SF_%05d' % (self.index,
                        int(round(100*self.scaling_factor)))

    def calc_amplitude(self):
        '''
        Amplitude measured as the biggest difference, among all layups that are
        not suppressed, between their thickness and the nominal thickness of the
        Cone / Cylinder
        '''
        if self.created:
            cc = self.impconf.conecyl
            max_amp = 0.
            cc_total_t = sum(cc.plyts)
            for layup in cc.part.compositeLayups.values():
                if not layup.suppressed:
                    layup_t = sum([p.thickness for p in layup.plies.values()])
                    max_amp = max(max_amp, abs(layup_t-cc_total_t))
            self.amplitude = max_amp

    def create(self, force=False):
        if self.created:
            if force:
                cc = self.impconf.conecyl
                cc.created = False
                cc.rebuilt = False
                cc.create_model()
            else:
                return

        imps, imps_theta_z, t_measured, R_measured, H_measured = update_imps()

        if self.use_theta_z_format:
            imperfection_file_name = imps_theta_z[self.imp_thick]['ti']
        else:
            imperfection_file_name = imps[self.imp_thick]['ti']

        H_measured = H_measured[self.imp_thick]
        R_measured = R_measured[self.imp_thick]
        t_measured = t_measured[self.imp_thick]
        cc = self.impconf.conecyl
        self.elems_t, self.t_set = change_thickness_ABAQUS(
                      imperfection_file_name = imperfection_file_name,
                      model_name = cc.mod.name,
                      part_name = cc.part.name,
                      stack = cc.stack,
                      t_model = sum(cc.plyts),
                      t_measured = t_measured,
                      H_model = cc.h,
                      H_measured = H_measured,
                      R_model = cc.r,
                      R_measured = R_measured,
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

        utils.set_colors_ti(cc)
        self.created = True
        self.calc_amplitude()
        print '%s amplitude = %f' % (self.name, self.amplitude)

        return self.elems_t, self.t_set

