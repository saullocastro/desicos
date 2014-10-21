import numpy as np
from abaqusConstants import *

from desicos.abaqus.constants import *

def _nearPt(x1, y1, x2, y2, t):
    x = x1 + t*(x2-x1)
    y = y1 + t*(y2-y1)
    return x,y

def _create_partition_from_sketch(cc, entity, s, cut=False):
    part = cc.part
    part_local_csys_datum = part.datums[cc.local_csys.id]
    new_face = part.faces.findAt(((entity.x, entity.y, entity.z),))[0]
    if cut:
        part.CutExtrude(sketchPlane = entity.sketch_plane.datum,
                        sketchUpEdge = part_local_csys_datum.axis3,
                        sketchPlaneSide = SIDE2,
                        sketchOrientation = RIGHT,
                        sketch = s,
                        depth = 0.5*cc.r)
    else:
        part.PartitionFaceBySketchDistance(
                sketchPlane = entity.sketch_plane.datum,
                sketchUpEdge = part_local_csys_datum.axis3,
                faces = new_face,
                sketchPlaneSide = SIDE2,
                sketch = s,
                distance = 0.5*cc.r)
    s.unsetPrimaryObject()

def _create_sketch(cc, entity):
    part = cc.part
    part_local_csys_datum = part.datums[ cc.local_csys.id ]
    t = part.MakeSketchTransform(sketchPlane = entity.sketch_plane.datum,
                                 sketchUpEdge = part_local_csys_datum.axis3,
                                 sketchPlaneSide = SIDE2,
                                 sketchOrientation = RIGHT,
                                 origin = (entity.x, entity.y, entity.z))
    name = '__%s_%s_%d' % (entity.name, 'sketch_', len(entity.sketches))
    s = cc.mod.ConstrainedSketch(name = name,
                                 sheetSize = cc.h,
                                 gridSpacing = cc.h/100.,
                                 transform = t)
    s.setPrimaryObject(option=SUPERIMPOSE)
    part.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    return s

def _create_circle_partition(cc, entity,
                             cut = False,
                             fact = 0.6,
                             radius = None):
    s = _create_sketch(cc, entity)
    if radius == None:
        cl = entity.theta2 - entity.theta
        cl *= fact
        side_low = np.sin(np.deg2rad(cl))*entity.rlow
        side_up = np.sin(np.deg2rad(cl))*entity.rup
        half_height = fact*(entity.zup - entity.zlow)/2.
        hh = half_height
    else:
        hh = radius
    s.CircleByCenterPerimeter(center=(0.0, 0.0),
                              point1=(0., hh))
    entity.sketches.append(s)
    _create_partition_from_sketch(cc, entity, s, cut)

def _create_rect_partition(cc, entity,
                               radius = None,
                               cut = False,
                               x_edges = False,
                               fact = 1.):
    s = _create_sketch(cc, entity)
    cl = entity.theta2 - entity.theta
    cl *= fact
    side_low = np.sin(np.deg2rad(cl))*entity.rlow
    side_up = np.sin(np.deg2rad(cl))*entity.rup
    half_height = fact*(entity.zup - entity.zlow)/2.
    hh = half_height
    l1 = s.Line(point1=(-side_up, hh), point2=(side_up, hh))
    l2 = s.Line(point1=(side_up, hh), point2=(side_low, -hh))
    l3 = s.Line(point1=(side_low, -hh), point2=(-side_low, -hh))
    l4 = s.Line(point1=(-side_low, -hh), point2=(-side_up, hh))
    if entity.__class__.__name__.find('PLoad') > -1:
        l5 = s.Line(point1=(-side_low, 0.), point2=(side_up, 0.))
    if x_edges:
        l6 = s.Line(point1=(-side_low, -hh), point2=(side_up, hh))
        l7 = s.Line(point1=(-side_up, hh), point2=(side_low, -hh))
    if radius <> None:
        radius_dist = 0.2
        rd = radius_dist
        if radius == 'auto':
            radius = 2*hh*rd
        x1, y1 = _nearPt(-side_up, hh, side_up, hh, (1-rd))
        x2, y2 = _nearPt(side_up, hh, side_low, -hh, rd)
        s.FilletByRadius(radius = radius,
                         curve1 = l1,
                         nearPoint1 = (x1, y1),
                         curve2 = l2,
                         nearPoint2 = (x2, y2))
        x1, y1 = _nearPt(side_up, hh, side_low, -hh, (1-rd))
        x2, y2 = _nearPt(side_low, -hh, -side_low, -hh, rd)
        s.FilletByRadius(radius = radius,
                         curve1 = l2,
                         nearPoint1 = (x1, y1),
                         curve2 = l3,
                         nearPoint2 = (x2, y2))
        x1, y1 = _nearPt(side_low, -hh, -side_low, -hh, (1-rd))
        x2, y2 = _nearPt(-side_low, -hh, -side_up, hh, rd)
        s.FilletByRadius(radius = radius,
                         curve1 = l3,
                         nearPoint1 = (x1, y1),
                         curve2 = l4,
                         nearPoint2 = (x2, y2))
        x1, y1 = _nearPt(-side_low, -hh, -side_up, hh, (1-rd))
        x2, y2 = _nearPt(-side_up, hh, side_up, hh, rd)
        s.FilletByRadius(radius = radius,
                         curve1 = l4,
                         nearPoint1 = (x1, y1),
                         curve2 = l1,
                         nearPoint2 = (x2, y2))
    geomList = tuple(s.geometry.values())
    s.removeGapsAndOverlaps(geomList = geomList, tolerance = TOL)
    entity.sketches.append(s)
    _create_partition_from_sketch(cc, entity, s, cut)

def _create_sketch_planes(cc):
    for imp in cc.impconf.imperfections:
        imp.create_sketch_plane()
    for cutout in cc.cutouts:
        cutout.create_sketch_plane()

def _create_partitions(cc):
    # identifying te first face for all objects:
    for imp in cc.impconf.imperfections:
        imp.faces = []
        imp.sketches = []
    for imp in cc.impconf.imperfections:
        imp.faces.append(cc.part.faces[0])
    for cutout in cc.cutouts:
        cutout.faces = []
        cutout.sketches = []
    for cutout in cc.cutouts:
        cutout.faces.append(cc.part.faces[0])
    if len(cc.cutouts) > 0:
        # partitioning 1
        #for pload in cc.impconf.ploads:
        #   _create_rect_partition(cc, pload)
        #TODO solution to avoid weird partitions
        if cc.alpharad == 0.:
            for cutout in cc.cutouts:
                _create_rect_partition(cc,
                                       cutout,
                                       x_edges=True)
        ## partitioning 2
        #for cutout in cc.cutouts:
        #    _create_rect_partition(cc,
        #                           entity = cutout,
        #                           radius = 'auto',
        #                           cut = False,
        #                           fact = 0.8)
        ## partitioning 3
        #for cutout in cc.cutouts:
        #    _create_circle_partition(cc,
        #                             entity=cutout,
        #                             cut=False,
        #                             fact = 0.7)
        # partitioning 4
        for cutout in cc.cutouts:
            _create_circle_partition(cc,
                                     cutout,
                                     cut = True,
                                     radius = cutout.d/2.)
    else:
        pass
