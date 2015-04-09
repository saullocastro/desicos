import numpy as np
from numpy import sin, cos

from desicos.abaqus.utils import cyl2rec


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

    """
    def __init__(self, thetadeg, pt, d, drill_offset_deg=0.):
        self.thetadeg = thetadeg
        self.pt = pt
        self.d = d
        self.index = None
        self.drill_offset_deg = drill_offset_deg
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

        clearance = 0.75*self.d
        self.offsetdeg = np.rad2deg((self.d/2. + clearance)/r)
        self.thetadeg1 = self.thetadeg - self.offsetdeg
        self.thetadeg2 = self.thetadeg + self.offsetdeg
        self.ptlow = (z-self.d)/H
        self.ptup = (z+self.d)/H

        self.name = 'cutout'
        self.thetadegs = [self.thetadeg1, self.thetadeg, self.thetadeg2]
        self.pts = [self.ptlow, self.pt, self.ptup]


    def create(self):
        from abaqus import mdb
        from abaqusConstants import (SIDE1, SUPERIMPOSE, COPLANAR_EDGES,
                MIDDLE, XZPLANE, SWEEP)

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
        dy = d*sin(thetarad)
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
                z),), searchTolerance=1.).values()]
            if not faceList:
                break
            #TODO try / except blocks needed due to an Abaqus bug
            try:
                p.RemoveFaces(faceList=faceList, deleteCells=False)
            except:
                pass

        p.setMeshControls(regions=p.faces, technique=SWEEP)
        p.generateMesh()

if __name__ == '__main__':
    from desicos.abaqus.conecyl import ConeCyl

    cc = ConeCyl()
    cc.from_DB('desicos_2014_c17')
    cc.impconf.ploads = []
    cc.impconf.add_cutout(0, 0.5, 100, 45)
    cc.create_model()


