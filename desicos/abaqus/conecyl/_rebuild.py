import json

import numpy as np

from desicos.conecylDB import fetch
import desicos.abaqus.utils as utils

def rebuild (self, force=False, save_rebuild=True):
    #TODO compatibility solution, should improve?
    utils.check_attribute(self, 'rsm', False)
    utils.check_attribute(self, 'direct_ABD_input', False)
    utils.check_attribute(self, 'laminaprops', [])
    utils.check_attribute(self, 'plyts', [])
    utils.check_attribute(self, 'laminapropKeys', [])
    utils.check_attribute(self, 'laminapropKey', 'material')
    utils.check_attribute(self, 'request_force_output', False)
    #TODO end of compatibility solution

    for node in self.nodes.values():
        node.rebuild()
    ##############################################
    if self.rebuilt and not force:
        return True
    #
    if self.request_force_output:
        self.output_requests += ['SF']

    # consistency checks
    #TODO
    if self.rsm:
        self.direct_ABD_input = True
        self.separate_load_steps = False
        self.axial_include = False
        self.elem_type = 'STRI3'

    if save_rebuild:
        if len(self.impconf.ploads) == 0:
            print 'WARNING - separate_load_steps changed to False'
            self.separate_load_steps = False
        if not self.separate_load_steps:
            self.num_of_steps = 1
        if self.separate_load_steps:
            if self.axial_include == False:
                self.num_of_steps = 1
            else:
                self.num_of_steps = 2

    # angle in radians
    if self.alphadeg <> None:
        self.alpharad = np.deg2rad(self.alphadeg)
    if self.betadeg  <> None:
        self.betarad = np.deg2rad(self.betadeg)
    if self.omegadeg <> None:
        self.omegarad = np.deg2rad(self.omegadeg)

    # r2
    self.r2 = self.r
    if self.r <> None and self.h <> None and self.alpharad <> None:
        self.r2 = self.r - np.tan(self.alpharad) * self.h

    # numel
    r = self.r
    r2 = self.r2

    # MESH
    if self.mesh_size_driven_by_cutouts:
        if len(self.cutouts) > 0:
            min_elsize = 1.e+6
            for cutout in self.cutouts:
                cl = cutout.clearance
                alpha = np.arcsin(cl/2. * cutout.d / self.r)
                elsize = alpha * self.r / (cutout.numel / 8)
                if min_elsize > elsize:
                    min_elsize = elsize
            tmp = 2 * np.pi * self.r
            self.numel_r = int(tmp / min_elsize)
            if tmp % min_elsize > 0:
                self.numel_r += 1

    #bot part of the meridian
    #the following rule considers a rav (average) in which it assumes r2
    #    if r2 --> 0, and assumes r if r2 --> r
    rav = ((r - r2)*r2/r + r2)
    perav = 2 * np.pi * rav
    for i in range(2):
        numel_r = self.numel_r
        if numel_r:
            self.elsize_r = 2*np.pi*self.r/numel_r # mm
        if self.numel_h:
            self.elsize_h = self.h/np.cos(self.alpharad)/self.numel_h
        else:
            if self.numel_hr_ratio:
                self.elsize_h = self.elsize_r/self.numel_hr_ratio
            else:
                self.elsize_h = perav/numel_r
        if i==0: #NOTE to improve the mesh for cutouts
            numel_h = self.h/np.cos(self.alpharad)/self.elsize_h
            numel_h = round(numel_h)
    self.elsize_r2 = self.r2/self.r* self.elsize_r

    # imperfections
    if self.impconf.load_asymmetry == None:
        self.impconf.add_load_asymmetry(self.betadeg, self.omegadeg)
    self.impconf.rebuild()

    # cutouts
    for cutout in self.cutouts:
        cutout.rebuild()

    if not isinstance(self.allowables, list):
        self.allowables = [self.allowables for i in self.stack]

    # laminapropKeys
    if not self.laminapropKeys:
        self.laminapropKeys = [self.laminapropKey for i in self.stack]

    # laminaprops
    if not self.laminaprops:
        laminaprops = fetch('laminaprops')
        if self.laminaprop:
            self.laminaprops = [self.laminaprop for i in self.stack]
        else:
            self.laminaprops = [laminaprops[k] for k in self.laminapropKeys]

    # ply thicknesses
    if not self.plyts:
        self.plyts = [self.plyt for i in self.stack]
    else:
        if isinstance(self.plyts, list):
            if len(self.plyts) <> len(self.stack):
                self.plyts = [plyts[0] for i in self.stack]
        else:
            self.plyts = [plyts for i in self.stack]

    # calculating ABD matrix
    if self.direct_ABD_input:
        self.calc_ABD_matrix()

    # jobname
    if self.rename:
        if not self.study:
            tmp = [self.name] + [self.impconf.name]
            self.jobname = '_'.join(tmp)
        else:
            self.jobname = self.study.name + '_model_%02d' % (self.index+1)

    if save_rebuild:
        self.rebuilt = True

    return True
