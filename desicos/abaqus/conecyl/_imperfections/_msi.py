import os

import numpy as np

from desicos.logger import *
from desicos.conecylDB import update_imps
from desicos.abaqus.conecyl._imperfections import Imperfection
from desicos.abaqus.constants import *
from desicos.abaqus.abaqus_functions import edit_keywords
from desicos.abaqus.apply_imperfections import (calc_translations_ABAQUS,
                                                translate_nodes_ABAQUS)

class MSI(Imperfection):

    def __init__(self):
        super(MSI, self).__init__()
        self.name = 'msi'
        self.imp_ms = ''
        self.stretch_H = False
        self.r_TOL = 1.
        self.ncp = 5
        self.power_parameter = 2
        self.num_sec_z = 100
        self.scaling_factor = 1.
        self.pt = 1.
        self.index  = None
        self.use_theta_z_format = False
        # plotting options
        self.xaxis = 'amplitude'
        self.xaxis_label = 'Imperfection amplitude, mm'
        self.nodal_translations = None
        self.stress_free = True
        self.created = False

    def rebuild(self):
        self.theta = 0.
        self.theta1 = 0.
        self.theta2 = 0.
        cc = self.impconf.conecyl
        self.r, self.z = cc.r_z_from_pt(self.pt)
        self.x, self.y, self.z = self.get_xyz()
        self.node = self.impconf.load_asymmetry.node
        self.name = 'MSI_%02d_SF_%05d' % (self.index,
                        int(round(100*self.scaling_factor)))

    def calc_amplitude(self):
        if self.created:
            self.amplitude = self.impconf.conecyl.measure_me()

    def create(self, force=False, stress_free=None):
        if stress_free==None:
            stress_free = self.stress_free

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
            imperfection_file_name = imps_theta_z[self.imp_ms]['msi']
        else:
            imperfection_file_name = imps[self.imp_ms]['msi']

        H_measured = H_measured[self.imp_ms]
        R_measured = R_measured[self.imp_ms]
        cc = self.impconf.conecyl
        if stress_free:
            self.nodal_translations = translate_nodes_ABAQUS(
                              imperfection_file_name = imperfection_file_name,
                              model_name = cc.mod.name,
                              part_name = cc.part.name,
                              H_model = cc.h,
                              H_measured = H_measured,
                              R_model = cc.r,
                              R_measured = R_measured,
                              semi_angle = cc.alphadeg,
                              stretch_H = self.stretch_H,
                              r_TOL = self.r_TOL,
                              num_closest_points = self.ncp,
                              power_parameter = self.power_parameter,
                              num_sec_z = self.num_sec_z,
                              scaling_factor = self.scaling_factor,
                              nodal_translations = self.nodal_translations,
                              use_theta_z_format = self.use_theta_z_format)
        else:
            warn('Using ``use_theta_z_format=True``')
            if self.nodal_translations==None:
                self.nodal_translations = calc_translations_ABAQUS(
                              imperfection_file_name = imperfection_file_name,
                              model_name = cc.mod.name,
                              part_name = cc.part.name,
                              H_model = cc.h,
                              H_measured = H_measured,
                              R_model = cc.r,
                              R_measured = R_measured,
                              semi_angle = cc.alphadeg,
                              stretch_H = self.stretch_H,
                              scaling_factor = self.scaling_factor,
                              r_TOL = self.r_TOL,
                              num_closest_points = self.ncp,
                              power_parameter = self.power_parameter,
                              num_sec_z = self.num_sec_z,
                              use_theta_z_format = True)
            trans = self.nodal_translations
            cc = self.impconf.conecyl
            print 'DEBUG cc.index', cc.index
            filename = os.path.join(cc.output_dir,
                                    'msi_stressed_{0:02d}.inp'.format(
                                     cc.index))
            edge_nids = ([n.id for n in cc.cross_sections[0].nodes]
                         + [n.id for n in cc.cross_sections[-1].nodes])
            with open(filename,'w') as out:
                out.write('*Boundary, type=displacement\n')
                for i, n in enumerate(cc.part.nodes):
                    nid = int(n.label)
                    if nid in edge_nids:
                        continue
                    u = np.concatenate((trans[i], [0,0,0]), axis=1)
                    for dof, u_dof in enumerate(u):
                        if u_dof != 0.:
                            out.write(
                                'InstanceCylinder.{0:d},{1:d},,{2:f}\n'.
                                      format(nid, dof+1, u_dof))
            text = '\n*INCLUDE, input=msi_stressed_{0:02d}.inp'.format(
                     cc.index)
            edit_keywords(model=cc.mod, text=text, before_pattern=None)

        self.created = True
        self.calc_amplitude()
        print '%s amplitude = %f' % (self.name, self.amplitude)

        return self.nodal_translations

    def print_to_file(self, filename=None):
        if not filename:
            cc = self.impconf.conecyl.study_dir
            filename = os.path.join(cc, self.name + '.txt')
        print 'Writing output file "%s" ...' % filename
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

