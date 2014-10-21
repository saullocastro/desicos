import numpy as np

from desicos.abaqus.conecyl._imperfections import Imperfection

class LBMI( Imperfection ):

    def __init__( self ):
        super( LBMI, self ).__init__()
        self.name = 'lbmi'
        self.mode = None
        self.scaling_factor = None
        self.pt = 1.
        self.theta = 0.
        self.theta1 = 180.
        self.theta2 = 180.
        # plotting options
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Imperfection amplitude, mm'

    def rebuild( self ):
        cc = self.impconf.conecyl
        pt = self.pt
        self.r, self.z  = cc.r_z_from_pt( self.pt )
        self.x, self.y, self.z = self.get_xyz()
        self.name = 'lbmi_mode_%02d' % self.mode

    def calc_amplitude( self ):
        self.amplitude = self.scaling_factor

