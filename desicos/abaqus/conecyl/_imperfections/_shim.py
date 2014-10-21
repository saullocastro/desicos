import numpy as np

from desicos.abaqus.conecyl._imperfections import Imperfection

class Shim(Imperfection):

    def __init__(self):
        super(Shim, self).__init__()
        self.pt = 1
        self.theta = None
        self.thick = None
        self.omega = None
        # plotting options
        self.xaxis = 'thick'
        self.xaxis_label = 'Shim thickness, mm'

    def rebuild(self):
        cc = self.impconf.conecyl
        pt = self.pt
        r, z = cc.r_z_from_pt(pt)
        self.z = z
        self.x, self.y, self.z = self.get_xyz()
        self.theta1 = self.theta
        self.theta2 = self.theta + self.omega
        self.r, z = cc.r_z_from_pt(self.pt)
        self.zlow = 0
        self.rlow, z = cc.r_z_from_pt(self.zlow / cc.h)
        self.zup = z
        self.rup, z  = cc.r_z_from_pt(self.zup  / cc.h)
        #
        self.theta  = self.theta % 360.
        self.theta1 = self.theta1 % 360.
        self.theta2 = self.theta2 % 360.
        #
        self.name = 'shim_theta_{0:03d}_thick_{1:03d}_omega_{2:03d}'.format(
                    int(self.theta), int(self.thick*100), int(self.omega))

    def calc_amplitude(self):
        self.amplitude = self.thick
