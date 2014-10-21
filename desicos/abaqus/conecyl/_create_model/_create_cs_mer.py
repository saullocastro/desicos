import numpy as np

import desicos.abaqus.geom as geom
import desicos.abaqus.coords as coords
import desicos.abaqus.utils as utils
from desicos.abaqus.constants import *

def _create_cs_mer( cc ):
    part = cc.part
    R = cc.r
    # MERIDIONAL CUTS
    thetas1 = []
    for entity in cc.impconf.imperfections + cc.cutouts:
        utils.add2list( thetas1, entity.theta  )
        utils.add2list( thetas1, entity.theta1 )
        utils.add2list( thetas1, entity.theta2 )
    utils.add2list( thetas1, 0. )
    utils.add2list( thetas1, 180. )
    cc.thetas = thetas1
    cc.thetas.sort()
    # the planes will cut both sides, so the thetas higher than 180.
    # must be cut at the opposite side
    thetas2 = []
    for theta in thetas1:
        if theta > 180.:
            utils.add2list( thetas2, theta - 360. )
        else:
            utils.add2list( thetas2, theta )
    thetas2.sort()
    # creating points and instantiating cutting plane objects
    pt = part.DatumPointByCoordinate( coords = (0.0, 0.0,   0.0   ) )
    po = part.datums[ pt.id ]
    pt = part.DatumPointByCoordinate( coords = (0.0, 0.0, 1.1*cc.h) )
    pz = part.datums[ pt.id ]
    cc.cutplanes = []
    for theta in thetas2:
        x  = 1.1*R * np.cos( np.deg2rad( theta ) )
        y  = 1.1*R * np.sin( np.deg2rad( theta ) )
        pt = part.DatumPointByCoordinate( coords = (x, y, 0.0) )
        pp = part.datums[ pt.id ]
        cutplane = geom.Plane()
        cutplane.p1   = po
        cutplane.p2   = pz
        cutplane.p3   = pp
        cutplane.theta = theta
        cutplane.part = part
        cc.cutplanes.append( cutplane )
        cutplane.create()
    # cutting faces
    pos_y_cuts = set([])
    neg_y_cuts = set([])
    for cutplane in cc.cutplanes:
        # skiping cross_section planes
        if cutplane.theta == None:
            continue
        # cutplane for theta = 0.
        if abs( cutplane.theta ) < TOL:
            cutplane_zero = cutplane
            continue
        if abs( cutplane.theta - 180. ) < TOL:
            continue
        for entity in cc.impconf.imperfections + cc.cutouts:
            #
            theta  = entity.theta
            theta1 = entity.theta1
            theta2 = entity.theta2
            if theta > 180.:
                theta -= 360.
            if theta1 > 180.:
                theta1 -= 360.
            if theta2 > 180.:
                theta2 -= 360.
            #
            if  abs(cutplane.theta - theta ) < TOL:
                y = entity.y
                if y > 0.:
                    pos_y_cuts.add( cutplane )
                else:
                    neg_y_cuts.add( cutplane )
            if  abs(cutplane.theta - theta1) < TOL:
                x,y,z = coords.cyl2rec( R, theta1, entity.z )
                if y > 0.:
                    pos_y_cuts.add( cutplane )
                else:
                    neg_y_cuts.add( cutplane )
            if  abs(cutplane.theta - theta2) < TOL:
                x,y,z = coords.cyl2rec( R, theta2, entity.z )
                if y > 0.:
                    pos_y_cuts.add( cutplane )
                else:
                    neg_y_cuts.add( cutplane )
    # dividing cylinder meridionally by two
    part.PartitionFaceByDatumPlane(
             datumPlane = cutplane_zero.datum,
             faces      = part.faces     )
    # cutting the positive faces
    for cutplane in pos_y_cuts:
        faces = part.faces.getByBoundingBox( -1.e6,-1.e-8,-1.e6,1.e6,1.e6,1.e6 )
        part.PartitionFaceByDatumPlane(
                 datumPlane = cutplane.datum,
                 faces      = faces     )
    # cutting the negative faces
    for cutplane in neg_y_cuts:
        faces = part.faces.getByBoundingBox( -1.e6,-1.e6,-1.e6,1.e6,1.e-8,1.e6 )
        part.PartitionFaceByDatumPlane(
                 datumPlane = cutplane.datum,
                 faces      = faces     )
    # CROSS SECTION CUTS
    cross_zs = []
    utils.add2list( cross_zs, 0. )
    bc = cc.boundary_clearance
    if bc == 0. or bc == None:
        pass
    else:
        utils.add2list( cross_zs,    bc  * cc.h )
        utils.add2list( cross_zs,(1.-bc) * cc.h )
    utils.add2list( cross_zs, cc.h )
    for imp in cc.impconf.imperfections:
        utils.add2list( cross_zs,  imp.z )
    for cutout in cc.cutouts:
        utils.add2list( cross_zs, cutout.zlow )
        utils.add2list( cross_zs, cutout.z )
        utils.add2list( cross_zs, cutout.zup )
    cc.cross_zs = cross_zs
    cc.cross_zs.sort()
    z_imps    = [imp.z for imp in cc.impconf.imperfections]
    z_cutouts = [cut.zlow for cut in cc.cutouts] + \
                [cut.z    for cut in cc.cutouts] + \
                [cut.zup  for cut in cc.cutouts]
    for z in cross_zs:
        if z == 0. or z == cc.h:
            continue
        pt = part.DatumPointByCoordinate( coords = (0.0  ,   0.0, z) )
        po = part.datums[ pt.id ]
        pt = part.DatumPointByCoordinate( coords = (1.1*R,   0.0, z) )
        px = part.datums[ pt.id ]
        pt = part.DatumPointByCoordinate( coords = (0.0  , 1.1*R, z) )
        py = part.datums[ pt.id ]
        cutplane      = geom.Plane()
        cutplane.p1   = po
        cutplane.p2   = px
        cutplane.p3   = py
        cutplane.part = part
        cc.cutplanes.append( cutplane )
        cutplane.create()
        if bc <> None and bc <> 0.:
            if abs(z - bc*cc.h) < TOL or abs(z - (1.-bc)*cc.h) < TOL:
                part.PartitionFaceByDatumPlane(
                         datumPlane = cutplane.datum,
                         faces      = part.faces     )
        #if  len(cc.cutouts) == 0 \
        if z in z_imps \
        or z in z_cutouts:
            part.PartitionFaceByDatumPlane(
                     datumPlane = cutplane.datum,
                     faces      = part.faces     )

    # END OF CUTTING
    # CROSS SECTION AND MERIDIANS
    cc.meridians = []
    for i in range( len(cc.thetas) ):
        theta = cc.thetas[ i ]
        meridian = geom.Meridian()
        meridian.index = i
        meridian.theta = theta
        cc.meridians.append( meridian )
    cc.cross_sections = []
    for i in range( len( cc.cross_zs) ):
        pt = cc.cross_zs[ i ] / cc.h
        r, z   = cc.r_z_from_pt( pt )
        cross_section = geom.CrossSection()
        cross_section.index = i
        cross_section.z     = z
        cc.cross_sections.append( cross_section )
    # finding for imperfections
    for imp in cc.impconf.imperfections:
        imp.get_cs_mer()
    # finding for cutouts
    for cutout in cc.cutouts:
        cutout.get_cs_mer()
    # MAPPING EDGES
    import _read_and_map
    _read_and_map._map_edges( cc, objname = 'part' )

