from desicos.abaqus.conecyl._imperfections import Imperfection

class LoadAsymmetry( Imperfection ):

    def __init__( self ):
        super( LoadAsymmetry, self ).__init__()
        self.name   = 'la'
        self.clearance = 0.
        self.index  = None
        self.betadeg = 0.
        self.omegadeg = 0.
        self.pt = 1.
        # plotting options
        self.xaxis = 'betadeg'
        self.xaxis_label = 'Load Asymmetry, degrees'

    def rebuild( self ):
        cc = self.impconf.conecyl
        self.betadeg = cc.betadeg
        self.omegadeg = cc.omegadeg
        self.theta  = self.omegadeg
        self.theta1 = self.omegadeg + 180.
        self.theta2 = self.omegadeg + 180.
        self.r, self.z  = cc.r_z_from_pt( self.pt )
        self.x, self.y, self.z = self.get_xyz()
        #
        self.name = 'la_betadeg_%07d' % int(round(1.e5*self.betadeg))
        self.name = 'la'

    def calc_amplitude( self ):
        self.amplitude = self.betadeg

