import numpy as np

from desicos.abaqus.conecyl._imperfections import Imperfection

class Axisymmetric( Imperfection ):

    def __init__( self ):
        super( Axisymmetric, self ).__init__()
        self.b = None
        self.wb = None
        # plotting options
        self.xaxis = 'wb'
        self.xaxis_label = 'Imperfection amplitude, mm'

    def rebuild( self ):
        cc = self.impconf.conecyl
        pt = self.pt
        r, z = cc.r_z_from_pt( pt )
        self.x = r
        self.y = 0.
        self.z = z
        #
        self.theta  = 0.
        self.theta1 = 0.
        self.theta2 = 0.
        #
        self.name = 'axisym_pt_%03d' % int(self.pt*100)

    def calc_amplitude( self ):
        self.amplitude = self.wb

    def create( self ):
        b  = self.b
        wb = self.wb
        cc = self.impconf.conecyl
        dim = 1.5 * self.b
        zMin = self.z - dim
        zMax = self.z + dim
        box_nodes = cc.part.nodes.getByBoundingBox( \
                         -1e6,-1e6,zMin,1e6,1e6,zMax )
        box_nodes = list(box_nodes)

        def calc_dr_dz( x, y, z ):
            zeta = (z-self.z) + b/2.
            if zeta < 0. or zeta > b:
                return 0. , 0.
            pt = z / cc.h
            r,z = cc.r_z_from_pt( pt )
            drR = -wb/2.*(1-np.cos(2*np.pi*zeta/b))
            dr = drR * np.cos( cc.alpharad )
            dz = drR * np.sin( cc.alpharad )
            return dr, dz
        local_csys = cc.part.datums[ cc.local_csys.id ]
        for node in box_nodes:
            x,     y, z = node.coordinates
            dr, dz = calc_dr_dz( x=x, y=y, z=z )
            if dr <> 0.:
                cc.part.editNode( localCsys = local_csys,
                                  nodes     = (node,)   ,
                                  offset1   = dr,
                                  offset3   = dz )


# Reference:
# modified from: Wullschleger, L. and Meyer-Piening, H.-R.. Buckling of
# geometrically imperfect cylindrical shells - definition of a buckling load.
# International Journal of Non-Linear Mechanics 37 (2002) 645-657.
