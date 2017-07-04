from __future__ import absolute_import

import numpy as np

from .imperfection import Imperfection

class Dimple(Imperfection):
    """Dimple imperfection

    References
    ----------
    Wullschleger, L. and Meyer-Piening, H.-R.. Buckling of geometrically
    imperfect cylindrical shells - definition of a buckling load.
    International Journal of Non-Linear Mechanics 37 (2002) 645-657.

    """
    def __init__(self, thetadeg, pt, a, b, wb):
        super(Dimple, self).__init__()
        self.thetadeg = thetadeg
        self.pt = pt
        self.a = a
        self.b = b
        self.wb = wb
        # plotting options
        self.xaxis = 'wb'
        self.xaxis_label = 'Imperfection amplitude, mm'

    def rebuild(self):
        cc = self.impconf.conecyl
        pt = self.pt
        r, z = cc.r_z_from_pt(pt)
        self.x, self.y, self.z = self.get_xyz()
        cl = np.rad2deg(self.a/2./r)
        self.r, z = cc.r_z_from_pt(self.pt)
        cl_side = np.sin(np.deg2rad(cl))*self.r
        self.zlow = self.z - cl_side
        self.rlow, z = cc.r_z_from_pt(self.zlow/cc.H)
        self.zup = self.z + cl_side
        self.rup, z = cc.r_z_from_pt(self.zup/cc.H)

        self.thetadeg1 = self.thetadeg - cl
        self.thetadeg2 = self.thetadeg + cl

        self.thetadeg  = self.thetadeg  % 360.
        self.thetadeg1 = self.thetadeg1 % 360.
        self.thetadeg2 = self.thetadeg2 % 360.

        self.thetadegs = [self.thetadeg1, self.thetadeg, self.thetadeg2]
        self.pts = [self.zlow/cc.H, self.z/cc.H, self.zup/cc.H]

        self.name = ('dimple_pt_%03d_theta_%03d'
                     % (int(self.pt*100), int(self.thetadeg)))

    def calc_amplitude(self):
        return self.wb

    def create(self):
        """Realizes the dimple imperfection in the finite element model

        The nodes corresponding to this imperfection are translated.

        .. note:: Must be called from Abaqus.

        """
        from __main__ import mdb

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        part_shell = mod.parts['Shell']

        a  = self.a
        b  = self.b
        wb = self.wb
        dim = 1.5*max(self.a, self.b)
        xMin = self.x - dim
        xMax = self.x + dim
        yMin = self.y - dim
        yMax = self.y + dim
        zMin = self.z - dim
        zMax = self.z + dim
        box_nodes = part_shell.nodes.getByBoundingBox(xMin,yMin,zMin,
                                                      xMax,yMax,zMax)
        box_nodes = np.array(box_nodes, dtype=object)
        def calc_dr_dz(x, y, z):
            zeta = (z-self.z) + b/2.
            dist = np.sqrt((x-self.x)**2 + (y-self.y)**2)
            pt = z / cc.H
            r,z = cc.r_z_from_pt(pt)
            alpha  = 2*np.arcsin(dist / (2.*r))
            arc = alpha*r
            drR = -wb/2.*np.cos(np.pi*arc/a)*(1-np.cos(2*np.pi*zeta/b))
            dr = drR*np.cos(cc.alpharad)
            dz = drR*np.sin(cc.alpharad)
            check = (zeta < 0.) | (zeta > b)
            dr[check] = 0
            dz[check] = 0
            check = (arc < 0.) | (arc > a/2.)
            dr[check] = 0
            dz[check] = 0
            return dr, dz
        local_csys = part_shell.features['part_cyl_csys']
        local_csys = part_shell.datums[local_csys.id]
        xs, ys, zs = np.array([node.coordinates for node in box_nodes]).T
        drs, dzs = calc_dr_dz(x=xs, y=ys, z=zs)
        check = drs!=0
        box_nodes = box_nodes[check]
        drs = drs[check]
        dzs = dzs[check]
        for node, dr, dz in zip(box_nodes, drs, dzs):
            part_shell.editNode(localCsys = local_csys,
                                nodes = (node,),
                                offset1 = dr,
                                offset3 = dz)


# Reference:
# Wullschleger, L. and Meyer-Piening, H.-R.. Buckling of geometrically
# imperfect cylindrical shells - definition of a buckling load. International
# Journal of Non-Linear Mechanics 37 (2002) 645-657.
