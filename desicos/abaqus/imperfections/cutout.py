import numpy as np
from numpy import sin, cos

from desicos.abaqus.utils import cyl2rec
from desicos.logger import warn


class Cutout(object):
    r"""Cutout

    Parameters
    ----------
    thetadeg : float
        Circumferential position of the dimple.
    pt : float
        Normalized meridional position.
    d : float
        Diameter of the drilling machine.
    drill_offset_deg : float
        Angular offset when the drilling is not normal to the shell
        surface. A positive offset means a positive rotation about the
        `\theta` axis, along the meridional plane.
    clearance_factor : float
        Fraction of the diameter to apply as clearance around the cutout.
        This clearance is partitoned and meshed separately from the rest of
        the cone / cylinder.

    """
    def __init__(self, thetadeg, pt, d, drill_offset_deg=0.,
                 clearance_factor=0.75):
        self.thetadeg = thetadeg
        self.pt = pt
        self.d = d
        self.index = None
        self.drill_offset_deg = drill_offset_deg
        self.clearance_factor = clearance_factor
        self.impconf = None
        self.name = ''
        self.thetadeg1 = None
        self.thetadeg2 = None
        self.offsetdeg = None
        # plotting options
        self.xaxis = 'd'
        self.xaxis_label = 'Cutout diameter, mm'
        self.x = None
        self.y = None
        self.z = None


    def rebuild(self):
        cc = self.impconf.conecyl
        H = cc.H
        r, z = cc.r_z_from_pt(self.pt)

        self.x, self.y, self.z = cyl2rec(r, self.thetadeg, z)

        clearance = self.clearance_factor*self.d
        self.offsetdeg = np.rad2deg((clearance + self.d/2.)/r)
        self.thetadeg1 = self.thetadeg - self.offsetdeg
        self.thetadeg2 = self.thetadeg + self.offsetdeg
        zoffs = clearance + self.d/2. / cos(np.deg2rad(self.drill_offset_deg))
        zoffs *= cos(cc.alpharad)
        self.ptlow = (z - zoffs)/H
        self.ptup = (z + zoffs)/H

        self.name = 'cutout'
        self.thetadegs = [self.thetadeg1, self.thetadeg, self.thetadeg2]
        self.pts = [self.ptlow, self.pt, self.ptup]


    def create(self):
        from abaqus import mdb
        from abaqusConstants import (SIDE1, SUPERIMPOSE, COPLANAR_EDGES,
                MIDDLE, XZPLANE, SWEEP, FIXED)
        from regionToolset import Region

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        p = mod.parts[cc.part_name_shell]
        ra = mod.rootAssembly
        datums = p.datums
        d = self.d
        r, z = cc.r_z_from_pt(self.pt)
        x, y, z = self.x, self.y, self.z
        alpharad = cc.alpharad
        drill_offset_rad = np.deg2rad(self.drill_offset_deg)
        thetarad = np.deg2rad(self.thetadeg)
        thetadeg = self.thetadeg
        thetadeg1 = self.thetadeg1
        thetadeg2 = self.thetadeg2

        # line defining the z axis
        _p1 = p.DatumPointByCoordinate(coords=(0, 0, 0))
        _p2 = p.DatumPointByCoordinate(coords=(0, 0, 1))
        zaxis = p.DatumAxisByTwoPoint(point1=datums[_p1.id],
                                      point2=datums[_p2.id])

        # line defining the cutting axis
        p1coord = np.array((x, y, z))
        dx = d*cos(alpharad - drill_offset_rad)*cos(thetarad)
        dy = d*cos(alpharad - drill_offset_rad)*sin(thetarad)
        dz = d*sin(alpharad - drill_offset_rad)
        p2coord = np.array((x+dx, y+dy, z+dz))
        p1 = p.DatumPointByCoordinate(coords=p1coord)
        p2 = p.DatumPointByCoordinate(coords=p2coord)
        drillaxis = p.DatumAxisByTwoPoint(point1=datums[p1.id],
                                          point2=datums[p2.id])

        #TODO get vertices where to pass the cutting plane
        plow = p1coord.copy()
        pup = p1coord.copy()
        rlow, zlow = cc.r_z_from_pt(self.ptlow)
        plow[2] = zlow
        rup, zup = cc.r_z_from_pt(self.ptup)
        pup[2] = zup

        diag1pt = p.DatumPointByCoordinate(
                    coords=cyl2rec(rup, thetadeg2, zup))
        diag2pt = p.DatumPointByCoordinate(
                    coords=cyl2rec(rup, thetadeg1, zup))
        diag3pt = p.DatumPointByCoordinate(
                    coords=cyl2rec(rlow, thetadeg1, zlow))
        diag4pt = p.DatumPointByCoordinate(
                    coords=cyl2rec(rlow, thetadeg2, zlow))
        diag1 = p.DatumPlaneByThreePoints(point1=datums[p1.id],
                                          point2=datums[p2.id],
                                          point3=datums[diag1pt.id])
        diag2 = p.DatumPlaneByThreePoints(point1=datums[p1.id],
                                          point2=datums[p2.id],
                                          point3=datums[diag2pt.id])
        diag3 = p.DatumPlaneByThreePoints(point1=datums[p1.id],
                                          point2=datums[p2.id],
                                          point3=datums[diag3pt.id])
        diag4 = p.DatumPlaneByThreePoints(point1=datums[p1.id],
                                          point2=datums[p2.id],
                                          point3=datums[diag4pt.id])

        c1 = cyl2rec(0.5*(rup + r), thetadeg + 0.5*self.offsetdeg,
                     0.5*(z + zup))
        c2 = cyl2rec(0.5*(rup + r), thetadeg - 0.5*self.offsetdeg,
                     0.5*(z + zup))
        c3 = cyl2rec(0.5*(rlow + r), thetadeg - 0.5*self.offsetdeg,
                     0.5*(z + zlow))
        c4 = cyl2rec(0.5*(rlow + r), thetadeg + 0.5*self.offsetdeg,
                     0.5*(z + zlow))

        #TODO try / except blocks needed due to an Abaqus bug
        try:
            face1 = p.faces.findAt(c1)
            p.PartitionFaceByDatumPlane(datumPlane=datums[diag1.id],
                    faces=face1)
        except:
            pass

        try:
            face2 = p.faces.findAt(c2)
            p.PartitionFaceByDatumPlane(datumPlane=datums[diag2.id],
                    faces=face2)
        except:
            pass

        try:
            face3 = p.faces.findAt(c3)
            p.PartitionFaceByDatumPlane(datumPlane=datums[diag3.id],
                    faces=face3)
        except:
            pass

        try:
            face4 = p.faces.findAt(c4)
            p.PartitionFaceByDatumPlane(datumPlane=datums[diag4.id],
                    faces=face4)
        except:
            pass

        sketchplane = p.DatumPlaneByPointNormal(point=datums[p2.id],
                                                normal=datums[drillaxis.id])

        sketchstrans = p.MakeSketchTransform(
                            sketchPlane=datums[sketchplane.id],
                            sketchUpEdge=datums[zaxis.id],
                            sketchPlaneSide=SIDE1,
                            origin=p2coord)

        sketch = mod.ConstrainedSketch(name='__profile__',
            sheetSize=10.*d, gridSpacing=d/10., transform=sketchstrans)
        sketch.setPrimaryObject(option=SUPERIMPOSE)
        p.projectReferencesOntoSketch(sketch=sketch, filter=COPLANAR_EDGES)
        sketch.CircleByCenterPerimeter(center=(0.0, 0),
                                       point1=(0.0, d/2.))

        #TODO try / except blocks needed due to an Abaqus bug
        try:
            p.PartitionFaceBySketchDistance(sketchPlane=datums[sketchplane.id],
                    sketchUpEdge=datums[zaxis.id], faces=p.faces,
                    sketchPlaneSide=SIDE1, sketch=sketch, distance=1.5*d)
        except:
            pass

        sketch.unsetPrimaryObject()
        del mod.sketches['__profile__']

        while True:
            faceList = [f[0] for f in p.faces.getClosest(coordinates=((x, y,
                z),), searchTolerance=(d/2. - 0.5)).values()]
            if not faceList:
                break
            #TODO try / except blocks needed due to an Abaqus bug
            try:
                p.RemoveFaces(faceList=faceList, deleteCells=False)
            except:
                pass

        # Seed edges around cutout area
        numel_per_edge = int(np.ceil(self.offsetdeg / 360.0 * cc.numel_r))
        edge_coords = [
            (rup, 0.5*(thetadeg1 + thetadeg), zup),
            (rup, 0.5*(thetadeg2 + thetadeg), zup),
            (rlow, 0.5*(thetadeg1 + thetadeg), zlow),
            (rlow, 0.5*(thetadeg2 + thetadeg), zlow),
            (0.5*(rlow + r), thetadeg1, 0.5*(zlow + z)),
            (0.5*(rup + r), thetadeg1, 0.5*(zup + z)),
            (0.5*(rlow + r), thetadeg2, 0.5*(zlow + z)),
            (0.5*(rup + r), thetadeg2, 0.5*(zup + z)),
        ]
        edge_coords = [cyl2rec(*c) for c in edge_coords]
        edgeList = [e[0] for e in p.edges.getClosest(coordinates=edge_coords,
            searchTolerance=1.).values()]
        p.seedEdgeByNumber(edges=edgeList, number=numel_per_edge, constraint=FIXED)

        try:
            p.setMeshControls(regions=p.faces, technique=SWEEP)
        except:
            warn("Unable to set mesh control to 'SWEEP', please check the mesh around your cutout(s)")
        p.generateMesh()
        for pload in cc.impconf.ploads:
            if (pload.pt == self.pt and pload.thetadeg == self.thetadeg and
                    pload.name in mod.loads.keys()):
                warn("Cutout is in the same location as perturbation load, moving PL to cutout edge")
                inst_shell = ra.instances['INST_SHELL']
                coords = cyl2rec(r, thetadeg + np.rad2deg(self.d/2./r), z)
                new_vertex = inst_shell.vertices.getClosest(
                    coordinates=[coords], searchTolerance=1.).values()[0][0]
                # Unfortunately you cannot simply pass a vertex or list of vertices
                # It has to be some internal abaqus sequence type... work around that:
                index = inst_shell.vertices.index(new_vertex)
                region = Region(vertices=inst_shell.vertices[index:index+1])
                mod.loads[pload.name].setValues(region=region)

if __name__ == '__main__':
    from desicos.abaqus.conecyl import ConeCyl

    cc = ConeCyl()
    cc.from_DB('desicos_2014_c17')
    cc.impconf.ploads = []
    cc.impconf.add_cutout(0, 0.5, 100, 45)
    cc.create_model()


