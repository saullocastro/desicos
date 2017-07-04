from __future__ import absolute_import

import numpy as np

from .imperfection import Imperfection

class Axisymmetric(Imperfection):
    """Axisymmetric Imperfection

    The imperfection definition is a special case of the dimple imperfection
    proposed by Wullschleger and Meyer-Piening (2002) (see :class:`.Dimple`).

    """
    def __init__(self, pt, b, wb):
        super(Axisymmetric, self).__init__()
        self.pt = pt
        self.b = b
        self.wb = wb
        # plotting options
        self.xaxis = 'wb'
        self.xaxis_label = 'Imperfection amplitude, mm'

    def rebuild(self):
        cc = self.impconf.conecyl
        pt = self.pt
        r, z = cc.r_z_from_pt(pt)
        self.x = r
        self.y = 0.
        self.z = z
        self.name = 'axisym_pt_%03d' % int(pt*100)
        self.thetadegs = []
        self.pts = [pt]

    def calc_amplitude(self):
        return self.wb

    def create(self):
        """Realizes the axisymmetric imperfection in the finite element model

        The nodes corresponding to this imperfection are translated.

        .. note:: Must be called from Abaqus.

        """
        from __main__ import mdb

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        part_shell = mod.parts['Shell']

        b  = self.b
        wb = self.wb
        cc = self.impconf.conecyl
        dim = 1.5*self.b
        zMin = self.z - dim
        zMax = self.z + dim
        box_nodes = part_shell.nodes.getByBoundingBox(-1e6,-1e6,zMin,
                                                    1e6,1e6,zMax)
        box_nodes = np.array(box_nodes, dtype=object)

        def calc_dr_dz(x, y, z):
            zeta = (z-self.z) + b/2.
            pt = z / cc.H
            r, z = cc.r_z_from_pt(pt)
            drR = -wb/2.*(1-np.cos(2*np.pi*zeta/b))
            dr = drR*np.cos(cc.alpharad)
            dz = drR*np.sin(cc.alpharad)
            check = (zeta < 0.) | (zeta > b)
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

