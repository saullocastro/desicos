import numpy as np
from numpy import sin, cos

from desicos.abaqus.stringers import Stringer


class BladeComposite(Stringer):
    """Blade stringer using composite properties

    Parameters
    ----------
    thetadeg : float
        Circumferential position in degrees.
    wbot : float
        Flange width at the bottom edge.
    wtop : float
        Flange width at the top edge.
    stack : list
        Laminate stacking sequence.
    plyts : list
        Ply thicknesses.
    laminaprops : list
        The properties for each lamina.
    numel_flange : int, optional
        The number of elements along the width.

    """
    def __init__(self, thetadeg, wbot, wtop, stack, plyts, laminaprops,
                 numel_flange=4):
        self.thetadegs = [thetadeg]
        self.wbot = wbot
        self.wtop = wtop
        self.stack = stack
        self.plyts = plyts
        self.laminaprops = laminaprops
        self.numel_flange = numel_flange


    def create(self):
        #TODO
        # for each stringer create a method that will create its part and
        # translate at the Assembly level already. The part name should be the
        # stringer name added by an identification number
        # probably it will be easier to handle the identification number by
        # creating a StringerConfiguration class, analogously to the
        # imperfection configuration class

        from desicos.abaqus import abaqus_functions
        from regionToolset import Region
        from abaqus import mdb, session
        from abaqusConstants import (STANDALONE, THREE_D, DEFORMABLE_BODY,
                                     FIXED, QUAD, STRUCTURED, ON, XZPLANE,
                                     CARTESIAN, LAMINA, COMPUTED,
                                     SURFACE_TO_SURFACE)

        cc = self.stringer_conf.conecyl
        mod = mdb.models[cc.model_name]
        vp = session.viewports[session.currentViewportName]
        count = 1
        for part_name in mod.parts.keys():
            if 'Stringer' in part_name:
                count += 1
        self.name = 'StringerBladeComposite_{0:02d}'.format(count)

        thetarad = np.deg2rad(thetadeg)
        L = cc.L
        sina = sin(cc.alpharad)
        cosa = cos(cc.alpharad)
        rbot = cc.rbot
        rtop = cc.rtop
        wbot = self.wbot
        wtop = self.wtop

        point1 = (0, 0)
        point2 = (-wbot, 0)
        point3 = (-L*sina - wtop, L*cosa)
        point4 = (-L*sina, L*cosa)

        # creating part
        s = mod.ConstrainedSketch(name='__profile__', sheetSize=L)
        g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
        s.setPrimaryObject(option=STANDALONE)
        s.Line(point1=point1, point2=point2)
        s.Line(point1=point2, point2=point3)
        s.Line(point1=point3, point2=point4)
        s.Line(point1=point4, point2=point1)
        part = mod.Part(name=self.name, dimensionality=THREE_D,
                        type=DEFORMABLE_BODY)
        part.BaseShell(sketch=s)
        s.unsetPrimaryObject()
        vp.setValues(displayedObject=part)
        del mod.sketches['__profile__']

        # partitioning along the meridian
        for pt in cc.pts:
            plane = part.DatumPlaneByPrincipalPlane(
                            principalPlane=XZPLANE, offset=pt*cc.H)
            part.PartitionFaceByDatumPlane(datumPlane=part.datums[plane.id],
                        faces=part.faces)

        # material properties
        same_laminaprop = True
        for laminaprop in self.laminaprops:
            if laminaprop != self.laminaprops[0]:
                same_lamiaprop = False
                break
        material_type = LAMINA
        if same_laminaprop:
            mat_name = 'MatStringer_{0:02d}'.format(count)
            mat_names = [mat_name for _ in laminaprops]
            myMat = mod.Material(name=mat_name)
            myMat.Elastic(table=(laminaprop,), type=material_type)
        else:
            mat_names = []
            for i, laminaprop in enumerate(self.laminaprops):
                mat_name = 'MatStringer_{0:02d}_ply_{0:02d}'.format(count, i+1)
                mat_names.append(mat_name)
                myMat = mod.Material(name=mat_name)
                myMat.Elastic(table=(laminaprop,), type=material_type)
        csys_name = 'CsysStringer_{0:02d}'.format(count)
        csys = part.DatumCsysByThreePoints(point1=(-L*sina, L*cosa, 0),
                point2=(-wbot, 0, 0), name=csys_name, coordSysType=CARTESIAN,
                origin=(0.0, 0.0, 0.0))
        csys_datum = part.datums[csys.id]
        abaqus_functions.create_composite_layup(
                name='LayupStringer_{0:02d}'.format(count),
                stack=self.stack, plyts=self.plyts, mat_names=mat_names,
                part=part, part_csys=csys_datum,
                region=Region(faces=part.faces), axis_normal=3)

        # meshing part
        # flange
        edge = part.edges.findAt((-wbot/2., 0., 0.))
        part.seedEdgeByNumber(edges=(edge,), number=self.numel_flange,
                              constraint=FIXED)
        # meridian
        coords = []
        for f in np.linspace(0.01, 0.99, 100):
            Li = f*L
            coords.append(((-Li*sina, Li*cosa, 0.),))
        edges = part.edges.findAt(*coords)
        part.seedEdgeBySize(edges=edges, size=cc.mesh_size,
                            constraint=FIXED)
        part.setMeshControls(regions=part.faces, elemShape=QUAD,
                             technique=STRUCTURED)
        part.generateMesh()

        # assemblying part
        ra = mod.rootAssembly
        ra.Instance(name=self.name, part=part, dependent=ON)
        ra.rotate(instanceList=(self.name, ),
                  axisPoint=(0.0, 0.0, 0.0),
                  axisDirection=(1.0, 0.0, 0.0),
                  angle=90.0)
        if thetadeg > 0:
            ra.rotate(instanceList=(self.name, ),
                      axisPoint=(0.0, 0.0, 0.0),
                      axisDirection=(0.0, 0.0, 1.0),
                      angle=thetadeg)
        ra.translate(instanceList=(self.name,),
                     vector=(rbot*cos(thetarad), rbot*sin(thetarad), 0.))
        vp.setValues(displayedObject=ra)


        # tieing stringer to the shell surface
        inst_shell = ra.instances['INST_SHELL']
        side2Faces1 = inst_shell.faces
        region1 = Region(side2Faces=side2Faces1)
        inst_stringer_faces = ra.instances[self.name].faces
        region2 = Region(side2Faces=inst_stringer_faces)
        tie_name = 'TieStringer_{0:02d}'.format(count)
        mod.Tie(name=tie_name, master=region1, slave=region2,
                positionToleranceMethod=COMPUTED, adjust=OFF,
                tieRotations=ON, constraintEnforcement=SURFACE_TO_SURFACE,
                thickness=ON)

        # output request
        hist_name = 'HistoryOutStringer_{0:02d}'.format(count)
        mod.FieldOutputRequest(name=hist_name, createStepName=cc.step1Name,
                               variables=('U',))


class BladeIsotropic(BladeComposite):
    """Blade stringer using isotropic properties

    Parameters
    ----------
    thetadeg : float
        Circumferential position in degrees.
    wbot : float
        Flange width at the bottom edge.
    wtop : float
        Flange width at the top edge.
    h : float
        Stringer thickness
    E : float
        Young Modulus
    nu : float
        Poisson's ratio
    numel_flange : int, optional
        The number of elements along the width.

    """
    def __init__(self, thetadeg, wbot, wtop, h, E, nu, numel_flange=4):
        self.thetadegs = [thetadeg]
        self.wbot = wbot
        self.wtop = wtop
        self.stack = [0]
        self.plyts = [h]
        G = E/(2*(nu+1))
        self.laminaprops = [(E, E, nu, G, G, G)]
        self.numel_flange = numel_flange


if __name__ == '__main__':
    from desicos.abaqus.stringers.stringerconf import StringerConf
    laminaprops = [(142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3) for
            i in range(10)]
    plyts = [0.125 for i in range(10)]
    stack = [0, 0, 90, +45, -45, -45, +45, 90, 0, 0]
    for thetadeg in [0, 30, 60, 90]:
        b = BladeComposite(thetadeg, 10, 30, stack, plyts, laminaprops)
        b = BladeIsotropic(thetadeg, 10, 30, 1., 2100., 0.33, 4)
        b.stringer_conf = StringerConf()
        b.stringer_conf.conecyl = stds['desicos_study'].ccs[1]
        b.create()
