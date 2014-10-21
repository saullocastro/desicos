import numpy as np

from desicos.abaqus.conecyl._imperfections import Imperfection

class Dimple(Imperfection):

    def __init__(self):
        super(Dimple, self).__init__()
        self.a = None
        self.b = None
        self.wb = None
        # plotting options
        self.xaxis = 'wb'
        self.xaxis_label = 'Imperfection amplitude, mm'

    def rebuild(self):
        cc = self.impconf.conecyl
        pt = self.pt
        r, z = cc.r_z_from_pt(pt)
        self.z = z
        self.x, self.y, self.z = self.get_xyz()
        cl = np.rad2deg(self.a / 2. / r)
        self.theta1 = self.theta - cl
        self.theta2 = self.theta + cl
        self.r, z = cc.r_z_from_pt(self.pt)
        cl_side = np.sin(np.deg2rad(cl)) * self.r
        self.zlow    = self.z - cl_side
        self.rlow, z = cc.r_z_from_pt(self.zlow / cc.h)
        self.zup     = self.z + cl_side
        self.rup, z  = cc.r_z_from_pt(self.zup  / cc.h)
        #
        self.theta  = self.theta  % 360.
        self.theta1 = self.theta1 % 360.
        self.theta2 = self.theta2 % 360.
        #
        self.name = 'dimple_pt_%03d_theta_%03d' \
                    % (int(self.pt*100), int(self.theta))

    def calc_amplitude(self):
        self.amplitude = self.wb

    def create(self):
        a  = self.a
        b  = self.b
        wb = self.wb
        cc = self.impconf.conecyl
        dim = 1.5 * max(self.a, self.b)
        xMin = self.x - dim
        xMax = self.x + dim
        yMin = self.y - dim
        yMax = self.y + dim
        zMin = self.z - dim
        zMax = self.z + dim
        box_nodes = cc.part.nodes.getByBoundingBox(\
                         xMin,yMin,zMin,xMax,yMax,zMax)
        box_nodes = list(box_nodes)

        def calc_dr_dz(x, y, z):
            zeta = (z-self.z) + b/2.
            if zeta < 0. or zeta > b:
                return 0. , 0.
            dist = np.sqrt((x-self.x)**2 + (y-self.y)**2)
            pt = z / cc.h
            r,z = cc.r_z_from_pt(pt)
            alpha  = 2 * np.arcsin(dist / (2. * r))
            arc = alpha * r
            if arc < 0. or arc > a/2.:
                return 0. , 0.
            drR = -wb/2. * np.cos(np.pi * arc/a) * (1-np.cos(2*np.pi*zeta/b))
            dr = drR * np.cos(cc.alpharad)
            dz = drR * np.sin(cc.alpharad)
            return dr, dz
        local_csys = cc.part.datums[ cc.local_csys.id ]
        for node in box_nodes:
            x,     y, z = node.coordinates
            dr, dz = calc_dr_dz(x=x, y=y, z=z)
            if dr <> 0.:
                cc.part.editNode(localCsys = local_csys,
                                  nodes     = (node,)   ,
                                  offset1   = dr,
                                  offset3   = dz)


# Reference:
# Wullschleger, L. and Meyer-Piening, H.-R.. Buckling of geometrically
# imperfect cylindrical shells - definition of a buckling load. International
# Journal of Non-Linear Mechanics 37 (2002) 645-657.
