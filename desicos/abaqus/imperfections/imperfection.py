from __future__ import absolute_import

from desicos.abaqus.abaqus_functions import create_sketch_plane
from desicos.abaqus.utils import cyl2rec

class Imperfection(object):
    """Base class for all imperfections

    This class should be sub-classed when a new imperfection is created.

    """
    def __init__(self):
        self.name = ''
        self.thetadegs = []
        self.pts = [] #NOTE zs, rs and pts are the same
        self.zs = []
        self.rs = []
        self.cc = None
        self.impconf = None
        self.amplitude = None
        self.sketch_plane = None

    def create_sketch_plane(self):
        self.sketch_plane = create_sketch_plane(self.impconf.conecyl,
                                                      self)
    def get_xyz(self):
        r, z = self.impconf.conecyl.r_z_from_pt(self.pt)
        return cyl2rec(r, self.thetadeg, z)
