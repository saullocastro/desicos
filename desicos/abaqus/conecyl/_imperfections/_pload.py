import numpy as np

from desicos.abaqus.conecyl._imperfections import Imperfection
from desicos.abaqus.constants import *

class PLoad( Imperfection ):

    def __init__( self, theta, pt, pltotal = 1. ):
        super( PLoad, self ).__init__(theta, pt)
        self.name   = 'PL'
        self.clearance = 0.
        self.index  = None
        if abs(pltotal) < 0.1 * TOL:
            pltotal = 0.1 * TOL
        self.pltotal  = pltotal # resultant pload
        self.plradial = None    # component radial direction
        self.plx  = None        # component x      direction
        self.ply  = None        # component y      direction
        self.plz  = None        # component z      direction
        self.poly_cir = None
        self.poly_mer = None
        self.xfit_cir = None
        self.xfit_mer = None
        # plotting options
        self.xaxis = 'pltotal'
        self.xaxis_label = 'Perturbation Load, N'

    def rebuild( self ):
        cc = self.impconf.conecyl
        alpharad = cc.alpharad
        betarad  = cc.betarad
        if abs(self.pltotal) < 0.1 * TOL:
            self.pltotal = 0.1 * TOL
        self.plradial =  self.pltotal * np.cos( alpharad + betarad )
        self.plz = -self.pltotal * np.sin( alpharad + betarad )
        self.plx = -self.plradial * np.cos( np.deg2rad( self.theta ) )
        self.ply = -self.plradial * np.sin( np.deg2rad( self.theta ) )
        self.x, self.y, self.z = self.get_xyz()
        cl = self.clearance
        self.theta1 = self.theta - cl
        self.theta2 = self.theta + cl
        self.r, z = cc.r_z_from_pt( self.pt )
        cl_side = np.sin( np.deg2rad( cl ) ) * self.r
        self.zlow    = self.z - cl_side
        self.rlow, z = cc.r_z_from_pt( self.zlow / cc.h )
        self.zup     = self.z + cl_side
        self.rup, z  = cc.r_z_from_pt( self.zup  / cc.h )
        #
        self.theta  = self.theta  % 360.
        self.theta1 = self.theta1 % 360.
        self.theta2 = self.theta2 % 360.
        #
        self.name = 'PL_pt_%03d_theta_%03d' \
                    % ( int(self.pt*100), int(self.theta) )

    def calc_amplitude( self ):
        cc = self.impconf.conecyl
        if cc.step2Name in self.node.dr.keys():
            if cc.axial_include:
                self.amplitude = ( self.node.dr[cc.step2Name][0]**2 +\
                                   self.node.dz[cc.step2Name][0]**2 )**0.5
            else:
                self.amplitude = ( self.node.dr[cc.step2Name][-1]**2 +\
                                   self.node.dz[cc.step2Name][-1]**2 )**0.5
        else:
            pass


