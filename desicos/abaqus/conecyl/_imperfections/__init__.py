import numpy as np

import desicos.abaqus.coords as coords
import desicos.abaqus.utils as utils
from desicos.abaqus.constants import *

class ImpConf( object ):
    '''
       Configurations of imperfections
       Each ImpConf may have one:
         - LoadAsymmetry
       and many objects:
         - PLoad
         - Dimple
         - Axisymmetric
         - Linear Buckling Mode-Shaped Imperfection (LBMI)
         - Thickness Imperfection (TI)
         - Mid-Surface Imperfection (MSI)

    '''
    def __init__( self ):
        self.load_asymmetry = None
        self.imperfections = []
        self.ploads = []
        self.dimples = []
        self.axisymmetrics = []
        self.lbmis = []
        self.msis = []
        self.tis = []
        self.rename = True
        self.name = ''
        self.conecyl = None

    def add_load_asymmetry( self, betadeg, omegadeg ):
        if self.load_asymmetry == None:
            import _load_asymmetry
            la = _load_asymmetry.LoadAsymmetry()
            la.betadeg = betadeg
            la.omegadeg = omegadeg
            la.impconf = self
            self.load_asymmetry = la
        else:
            la = self.load_asymmetry
            la.betadeg = betadeg
            la.omegadeg = omegadeg
        return la

    def add_dimple( self, theta0, pt, a, b, wb ):
        import _dimple
        #
        sb = _dimple.Dimple()
        sb.theta  = theta0
        sb.pt = pt
        sb.a = a
        sb.b = b
        sb.wb = wb
        sb.impconf = self
        #
        self.dimples.append( sb )
        return sb

    def add_axisymmetric( self, pt, b, wb ):
        import _axisymmetric
        #
        ax = _axisymmetric.Axisymmetric()
        ax.pt = pt
        ax.b = b
        ax.wb = wb
        ax.impconf = self
        #
        self.axisymmetrics.append( ax )
        return ax

    def add_pload( self, theta, pt, pltotal ):
        import _pload
        pload = _pload.PLoad( theta, pt, pltotal )
        pload.impconf = self
        self.ploads.append( pload )
        return pload

    def add_lbmi( self, mode, scaling_factor ):
        import _lbmi
        lbmi = _lbmi.LBMI()
        lbmi.mode = mode
        lbmi.scaling_factor = scaling_factor
        lbmi.impconf = self
        self.lbmis.append( lbmi )
        return lbmi

    def add_msi( self, imp_ms, scaling_factor ):
        import _msi
        msi = _msi.MSI()
        msi.impconf = self
        msi.imp_ms = imp_ms
        msi.scaling_factor = scaling_factor
        self.msis.append( msi )
        return msi

    def add_ti( self, imp_thick, scaling_factor ):
        import _ti
        ti = _ti.TI()
        ti.impconf = self
        ti.imp_thick = imp_thick
        ti.scaling_factor = scaling_factor
        self.tis.append( ti )
        return ti

    def rebuild( self ):
        #TODO compatibility solution, should improve?
        utils.check_attribute( self, 'msis', [] )
        utils.check_attribute( self, 'tis', [] )
        #TODO end of compatibility solution
        self.imperfections = []
        i = -1
        # load asymmetry
        la = self.load_asymmetry
        if la <> None:
            i += 1
            la.index = i
            la.rebuild()
            self.imperfections.append( la )
        # ploads
        for pload in self.ploads:
            i += 1
            pload.index = i
            pload.rebuild()
            self.imperfections.append( pload )
        # dimples
        for sb in self.dimples:
            i += 1
            sb.index = i
            sb.rebuild()
            self.imperfections.append( sb )
        # axisymmetrics
        for ax in self.axisymmetrics:
            i += 1
            ax.index = i
            ax.rebuild()
            self.imperfections.append( ax )
        # linear buckling mode-shaped imperfection (LBMI)
        for lbmi in self.lbmis:
            i += 1
            lbmi.index = i
            lbmi.rebuild()
            self.imperfections.append( lbmi )
        # mid-surface imperfection (MSI)
        for msi in self.msis:
            i += 1
            msi.index = i
            msi.rebuild()
            self.imperfections.append( msi )
        # thickness imperfection (TI)
        for ti in self.tis:
            i += 1
            ti.index = i
            ti.rebuild()
            self.imperfections.append( ti )
        # name
        if self.rename:
            self.name = ('PLs_%02d_dimples_%02d_axisym_%02d' +\
                        '_lbmis_%02d_MSIs_%02d_TIs_%02d') % \
                        ( len(self.ploads), len(self.dimples),
                          len(self.axisymmetrics), len(self.lbmis),
                          len(self.msis), len(self.tis) )


class Imperfection( object ):

    def __init__(self, theta=0., pt=0.5):
        self.name = ''
        self.r    = None
        self.rlow = None
        self.rup  = None
        self.theta  = theta
        self.theta1 = None
        self.theta2 = None
        self.pt = pt        # ratio along cone/cylinder height
        self.z    = None
        self.zlow = None
        self.zup  = None
        self.x = None
        self.y = None
        self.cc = None
        self.impconf = None
        self.vertice = None
        self.sketch_plane = None
        self.sketches  = []
        self.faces  = []
        self.clearance = 20.
        self.meridian = None
        self.cross_section = None
        self.ehr_cir   = None
        self.ehr_mer   = None
        self.amplitude = None
        self.node      = None

    def get_xyz( self ):
        r, z = self.impconf.conecyl.r_z_from_pt( self.pt )
        return coords.cyl2rec( r, self.theta, z )

    def create_sketch_plane( self ):
        self.sketch_plane = \
            utils.create_sketch_plane( self.impconf.conecyl, self )

    def get_cs_mer( self ):
        for meridian in self.impconf.conecyl.meridians:
            if abs(self.theta - meridian.theta) < TOLangle:
                meridian.ploads.append( self )
                self.meridian = meridian
                break
        for cross_section in self.impconf.conecyl.cross_sections:
            if abs(self.z - cross_section.z) < TOL:
                cross_section.ploads.append( self )
                self.cross_section = cross_section
                break
        if self.meridian == None:
            print 'WARNING - pload - meridian not found'
            raise
        if self.cross_section == None:
            print 'WARNING - pload - cross section not found'
            raise

    def get_node( self, force=False ):
        if self.node == None:
            node = list( set( self.meridian.nodes ) &\
                         set( self.cross_section.nodes ) )[0]
            self.node = node
            self.node.pload = self
        return self.node

    def calc_ehr_and_displ( self, step_name='',\
                            cir_criterion = 'zero_radial_displ',
                            cir_threshold = 0.0125,
                            mer_threshold = 0.0125,
                            only_cir = True ):
        if self.pltotal < TOL:
            self.ehr_cir = 0.
            self.ehr_mer = 0.
            return
        if step_name == '':
            step_name = self.impconf.conecyl.step1Name
        self.get_node()
        cc = None
        if self.impconf <> None:
            if self.impconf.conecyl <> None:
                cc = self.impconf.conecyl
        if cc == None:
            print 'WARNING - concecyl not found for pload'
        #
        # circumferential equivalent cutout radius
        #
        nodes = self.cross_section.nodes
        nodeids = [ node.id for node in nodes ]
        plnindex  = nodeids.index( self.node.id )
        plndispl  = self.node.dr[ step_name ][ -1 ]
        if cir_criterion == 'zero_radial_displ':
            # finding point
            x = []
            y = []
            for node in nodes:
                x.append( node.theta - self.theta )
                y.append( node.dr[ step_name ][ -1 ] )
            thr = cir_threshold
            for i in range( len(y)-2, -1, -1 ):
                yi = abs( y[i] )
                if yi > thr:
                    xi  = abs( x[i]   )
                    xi1 = abs( x[i+1] )
                    yi1 = abs( y[i+1] )
                    # linear interpolation
                    radius_theta = (thr-yi)*(xi1-xi)/(yi1-yi) + xi
                    #TODO very interesting that the wrong formula for
                    #     radius_theta (without abs()) was resulting in
                    #     constant diameter after some perturbation load level
                    break
        if cir_criterion == 'first_cross':
            # reading points to polyfit
            xj = []
            yj = []
            order = 6
            xj.append( nodes[plnindex].theta - self.theta )
            yj.append( nodes[plnindex].dr[ step_name ][ -1 ] )
            for j in range( plnindex + 1, len(nodeids) ):
                node_1 = nodes[ j-1 ]
                node   = nodes[ j   ]
                dri_1  = node_1.dr[ step_name ][ -1 ]
                dri    = node.dr[ step_name ][ -1 ]
                xj.append( node.theta - self.theta )
                yj.append( dri )
                if dri_1 > dri and (j-plnindex) > order:
                    break
            # creating polynom
            if len(xj)-1 < order:
                order = len(xj) - 1
            poly = np.poly1d( np.polyfit( xj, yj, order ) )
            # curve to find theta for radial_displ = 0
            init  = int(10*min(xj))
            final = int(10*max(xj))
            xfit = np.array( [j*0.1 for j in range( init, final, 1 )] )
            roots = []
            for root in np.roots( poly ):
                if np.imag( root ) == 0:
                    root = np.real( root )
                    if  min(xj) < root\
                    and max(xj) > root:
                        roots.append( root )
            if not roots:
                for root in np.roots( poly.deriv() ):
                    if np.imag( root ) == 0:
                        root = np.real( root )
                        if  min(xj) < root\
                        and max(xj) > root:
                            roots.append( root )
            roots.sort()
            radius_theta = roots[0]
            if roots[0] < cc.plyts[0]:
                radius_theta = roots[1]
            #
            # storing values
            self.xj_cir = xj
            self.yj_cir = yj
            self.poly_cir = poly
            self.xfit_cir = xfit
        r_local, tmpz  = cc.r_z_from_pt( self.pt )
        try:
            rad = np.deg2rad(radius_theta - self.theta)
        except:
            print 'ERROR - Diameter could not be calculated'
            return False
        self.ehr_cir  = float( rad * r_local)
        #
        # meridional equivalent cutout radius
        #
        if only_cir:
            self.ehr_mer = 0.
            return
        nodes = self.meridian.nodes
        nodeids = [ node.id for node in nodes ]
        plnindex = nodeids.index( self.node.id )
        plndispl = self.node.dr[ step_name ][ -1 ]
        xj = []
        yj = []
        # reading points to polyfit
        order = 6
        xj.append( nodes[plnindex].z - self.z )
        yj.append( nodes[plnindex].dr[ step_name ][ -1 ] )
        for j in range( plnindex + 1, len(nodeids) ):
            node_1 = nodes[ j-1 ]
            node   = nodes[ j   ]
            dri_1  = node_1.dr[ step_name ][ -1 ]
            dri    = node.dr[ step_name ][ -1 ]
            xj.append( node.z - self.z )
            yj.append( dri )
            if dri_1 > dri and (j-plnindex) > order:
                break
        # creating polynom
        if len(xj)-1 < order:
            order = len(xj) - 1
        poly = np.poly1d( np.polyfit( xj, yj, order ) )
        # curve to find theta for radial_displ = 0.1
        init  = int(10*min(xj))
        final = int(10*max(xj))
        xfit = np.array( [j*0.1 for j in range( init, final, 1 )] )
        polyxxx = poly.deriv().deriv().deriv()
        #
        roots = []
        for root in np.roots(polyxxx):
            if np.imag( root ) == 0:
                root = np.real( root )
                if  min(xj) < root\
                and max(xj) > root:
                    roots.append( root )

        # storing values
        self.xj_mer = xj
        self.yj_mer = yj
        self.ehr_mer = float(min( roots ))
        self.poly_mer = poly
        self.xfit_mer = xfit
        self.displ    = plndispl
