import numpy as np

import utils

from constants import *

class Cutout(object):

    def __init__( self ):
        self.name      = ''
        self.index     = None
        self.d         = None
        self.theta     = None
        self.pt        = None
        self.theta1    = None
        self.theta2    = None
        self.meridian1 = None
        self.meridian  = None
        self.meridian2 = None
        self.cross_section_low = None
        self.cross_section     = None
        self.cross_section_up  = None
        self.clearance = 3.
        self.x         = None
        self.y         = None
        self.zlow      = None
        self.z         = None
        self.zup       = None
        self.rlow      = None
        self.r         = None
        self.rup       = None
        self.numel     = 64     #use multiples of 8
        #self.layers    = 3
        self.conecyl   = None
        self.diag1_plane = None
        self.diag2_plane = None
        self.diag1_edges = []
        self.diag2_edges = []
        self.inner_edges = []
        self.middle_edges = []
        self.outer_edges = []
        self.sketch_plane = None
        self.sketches = []
        self.faces = []
        # plotting options
        self.xaxis = 'd'
        self.xaxis_label = 'Cutout diameter, mm'

    def rebuild( self ):
        cc = self.conecyl
        cl = self.clearance
        self.r, self.z = cc.r_z_from_pt( self.pt )
        x, y, z        = utils.cyl2rec( self.r, self.theta, self.z )
        self.x         = x
        self.y         = y
        alpha          = np.arcsin( self.d*cl/ (2 * self.r) )
        self.theta1    = self.theta - np.rad2deg( alpha )
        self.theta2    = self.theta + np.rad2deg( alpha )
        self.zlow      = self.z - self.d*cl / 2.
        self.rlow, z   = cc.r_z_from_pt( self.zlow / cc.h )
        self.zup       = self.z + self.d*cl / 2.
        self.rup, z    = cc.r_z_from_pt( self.zup  / cc.h )
        #
        self.theta  = self.theta  % 360.
        self.theta1 = self.theta1 % 360.
        self.theta2 = self.theta2 % 360.
        #
        self.name      = 'cutout_%d' % self.index

    def get_cs_mer( self ):
        if self.conecyl is None:
            print 'ERROR - cutout.py - find_meridians - conecyl not defined!'
            raise
        for meridian in self.conecyl.meridians:
            if abs( meridian.theta - self.theta1 ) < TOL:
                self.meridian1 = meridian
            if abs( meridian.theta - self.theta  ) < TOL:
                self.meridian  = meridian
            if abs( meridian.theta - self.theta2 ) < TOL:
                self.meridian2 = meridian
        if self.meridian1 is None\
        or self.meridian  is None\
        or self.meridian2 is None:
            print 'ERROR - cutout.py - find_meridians - meridian not found!'

        for cross_section in self.conecyl.cross_sections:
            if abs( cross_section.z - self.zlow ) < TOL:
                self.cross_section_low = cross_section
            if abs( cross_section.z - self.z  ) < TOL:
                self.cross_section  = cross_section
            if abs( cross_section.z - self.zup ) < TOL:
                self.cross_section_up  = cross_section
        if self.cross_section_low is None\
        or self.cross_section     is None\
        or self.cross_section_up  is None:
            print 'ERROR - cutout.py - find_cross_sections - cross_section not found!'

    def find_faces( self ):
        pass

    def find_edges( self ):
        pass

    def create_sketch_plane( self ):
        import utils
        self.sketch_plane = \
            utils.create_sketch_plane( self.conecyl, self )

    def create( self ):
        return

