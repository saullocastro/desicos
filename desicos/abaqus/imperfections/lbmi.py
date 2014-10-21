import numpy as np

from imperfection import Imperfection

class LBMI(Imperfection):
    """Linear Buckling Mode-shaped Imperfection (LBMI)

    """
    def __init__(self, mode, scaling_factor):
        super(LBMI, self).__init__()
        self.name = 'lbmi'
        self.mode = mode
        self.scaling_factor = scaling_factor
        self.pt = 1.
        self.theta = 0.
        # plotting options
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Imperfection amplitude, mm'

    def rebuild(self):
        cc = self.impconf.conecyl
        self.name = 'lbmi_mode_%02d' % self.mode
        self.thetadegs = []
        self.pts = []

    def calc_amplitude(self):
        return self.scaling_factor

    def create(self):
        pass

