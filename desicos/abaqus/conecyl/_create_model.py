import numpy as np

from abaqus import mdb, session
from abaqusConstants import *
from regionToolset import Region
import mesh

from desicos.logger import warn
from desicos.abaqus import abaqus_functions
from desicos.abaqus.constants import NUM_LB_MODES

def _create_mesh(cc):
    cc.rebuild()
    fr = cc.fr
    model_name = cc.model_name
    rbot = cc.rbot
    rtop = cc.rtop
    rmesh = cc.rmesh
    H = cc.H
    alphadeg = cc.alphadeg
    cosa = np.cos(cc.alpharad)
    resin_E = cc.resin_E
    resin_nu = cc.resin_nu
    tshell = sum(cc.plyts)
    resin_bot_h = float(cc.resin_bot_h)
    resin_top_h = float(cc.resin_top_h)
    resin_bir_w1 = float(cc.resin_bir_w1)
    resin_bir_w2 = float(cc.resin_bir_w2)
    resin_bor_w1 = float(cc.resin_bor_w1)
    resin_bor_w2 = float(cc.resin_bor_w2)
    resin_tir_w1 = float(cc.resin_tir_w1)
    resin_tir_w2 = float(cc.resin_tir_w2)
    resin_tor_w1 = float(cc.resin_tor_w1)
    resin_tor_w2 = float(cc.resin_tor_w2)

    # Analysis parameters
    elem_type_str = cc.elem_type
    mesh_size = cc.mesh_size
    resin_numel = cc.resin_numel

    # Getting Imperfection Partitions
    thetadegs, pts = cc.calc_partitions()

    part_name_shell = cc.part_name_shell
    inst_name_shell = ('inst_' + part_name_shell).upper()
    output_name = model_name + '.odb'

    elem_dict = {'S8R5':S8R5, 'S4R':S4R, 'S4R5':S4R5}
    elem_type = elem_dict[elem_type_str]

    mod = mdb.Model(name=model_name)
    if 'Model-1' in mdb.models.keys():
        del mdb.models['Model-1']
    part_shell = mod.Part(name='Shell', dimensionality=THREE_D,
                        type=DEFORMABLE_BODY )
    #CREATING THE SKETCH which will be used to create the shell geometry
    s1 = mod.ConstrainedSketch(name='SketchCylinder',
                               sheetSize=max([2.1*rbot, 1.1*H]))
    #sketch profile to be extruded
    s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(rbot, 0.0) )
    part_shell.BaseShellExtrude(depth=H, draftAngle=-alphadeg, sketch=s1)

    part_csys = part_shell.DatumCsysByThreePoints(name='part_cyl_csys',
                                                coordSysType=CYLINDRICAL,
                                                origin=(0.0, 0.0, 0.0),
                                                point1=(1.0, 0.0, 0.0),
                                                point2=(0.0, 1.0, 0.0))
    part_csys = part_shell.datums[part_csys.id]

    # Creating the shell material.
    mat_names = []
    for i, laminaprop in enumerate(cc.laminaprops):
        if len(laminaprop) <= 4:
            material_type = ISOTROPIC
            laminaprop = (laminaprop[0], laminaprop[2])
        else:
            material_type = LAMINA
        mat_name = cc.laminapropKeys[i]
        mat_names.append(mat_name)
        if not mat_name in mod.materials.keys():
            myMat = mod.Material(name=mat_name)
            myMat.Elastic(table=(laminaprop,), type=material_type)
            if i < len(cc.allowables) and material_type <> ISOTROPIC:
                ALLOWABLES=tuple([abs(j) for j in cc.allowables[i]])
                myMat.HashinDamageInitiation(table=(ALLOWABLES,))
    abaqus_functions.create_composite_layup(name='CompositePlate',
            stack=cc.stack, plyts=cc.plyts, mat_names=mat_names,
            part=part_shell, part_csys=part_csys,
            region=Region(faces=part_shell.faces))

    # Creating the resin material.
    if cc.resin_ring_bottom or cc.resin_ring_top:
        mod.Material(name='Resin')
        mod.materials['Resin'].Elastic(table=((resin_E, resin_nu),))
        mod.HomogeneousSolidSection(name='Rings', material='Resin')

    def create_ring_part(part_name, x1, x2, x3, x4, y1, y2, y3, y4):
        p1 = (x1, y1)
        p2 = (x2, y2)
        p3 = (x3, y3)
        p4 = (x4, y4)
        s1 = mod.ConstrainedSketch(name='__profile__', sheetSize=2*rbot)
        g, v, d, c = s1.geometry, s1.vertices, s1.dimensions, s1.constraints
        s1.setPrimaryObject(option=STANDALONE)
        s1.ConstructionLine(point1=(0.0, -1000.0), point2=(0.0, 1000.0))
        #s1.FixedConstraint(entity=g[2])
        s1.Line(point1=p1, point2=p2)
        s1.Line(point1=p2, point2=p3)
        s1.Line(point1=p3, point2=p4)
        s1.Line(point1=p4, point2=p1)
        p = mod.Part(name=part_name, dimensionality=THREE_D,
            type=DEFORMABLE_BODY)
        p.BaseSolidRevolve(sketch=s1, angle=360.0, flipRevolveDirection=OFF)
        s1.unsetPrimaryObject()
        del mod.sketches['__profile__']
        #p.setValues(geometryRefinement=EXTRA_FINE)
        return p

    if cc.resin_ring_bottom:
        # Create the Part 'Bottom_IR'
        y1 = 0
        y2 = 0
        y3 = resin_bot_h
        y4 = resin_bot_h
        x1 = fr(y1) - cosa*tshell/2.
        x2 = fr(y2) - cosa*tshell/2. - resin_bir_w1
        x3 = fr(y3) - cosa*tshell/2. - resin_bir_w2
        x4 = fr(y4) - cosa*tshell/2.
        part_bir = create_ring_part('Bottom_IR', x1, x2, x3, x4,
                                    y1, y2, y3, y4)
        # Create the part 'Bottom_OR'
        y1 = 0
        y2 = 0
        y3 = resin_bot_h
        y4 = resin_bot_h
        x1 = fr(y1) + cosa*tshell/2. + resin_bor_w1
        x2 = fr(y2) + cosa*tshell/2.
        x3 = fr(y3) + cosa*tshell/2.
        x4 = fr(y4) + cosa*tshell/2. + resin_bor_w2
        part_bor = create_ring_part('Bottom_OR', x1, x2, x3, x4,
                                    y1, y2, y3, y4)

    if cc.resin_ring_top:
        # Create the part 'Top_IR'
        y1 = H-resin_top_h
        y2 = H-resin_top_h
        y3 = H
        y4 = H
        x1 = fr(y1) - cosa*tshell/2.
        x2 = fr(y2) - cosa*tshell/2. - resin_tir_w1
        x3 = fr(y3) - cosa*tshell/2. - resin_tir_w2
        x4 = fr(y4) - cosa*tshell/2.
        part_tir = create_ring_part('Top_IR', x1, x2, x3, x4, y1, y2, y3, y4)
        # Create the part 'Top_OR'
        y1 = H-resin_top_h
        y2 = H-resin_top_h
        y3 = H
        y4 = H
        x1 = fr(y1) + cosa*tshell/2. + resin_tor_w1
        x2 = fr(y2) + cosa*tshell/2.
        x3 = fr(y3) + cosa*tshell/2.
        x4 = fr(y4) + cosa*tshell/2. + resin_tor_w2
        part_tor = create_ring_part('Top_OR', x1, x2, x3, x4, y1, y2, y3, y4)

    xzplane = part_shell.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE,
                                                    offset=0)
    xzplane = part_shell.datums[xzplane.id]
    for thetadeg in thetadegs:
        thetarad = np.deg2rad(thetadeg)
        # cutting the shell around the circumference using planes
        plane = part_shell.DatumPlaneByRotation(plane=xzplane,
                                                axis=part_csys.axis3,
                                                angle=thetadeg)
        xbot = rbot*np.cos(thetarad)
        ybot = rbot*np.sin(thetarad)
        xtop = rtop*np.cos(thetarad)
        ytop = rtop*np.sin(thetarad)
        coords_bot = (xbot, ybot, 0)
        coords_middle = ((xbot+xtop)*0.5, (ybot+ytop)*0.5, H/2.)
        faces = part_shell.faces.findAt(coords_middle)
        try:
            part_shell.PartitionFaceByDatumPlane(
                        datumPlane=part_shell.datums[plane.id],
                        faces=faces)
        except:
            pass

        if cc.resin_ring_bottom:
            # cutting Bottom_IR
            y1 = 0.
            y2 = 0.
            y3 = resin_bot_h
            y4 = resin_bot_h
            x1 = (fr(y1) - cosa*tshell/2.)*np.cos(thetarad)
            x2 = (fr(y2) - cosa*tshell/2. - resin_bir_w1)*np.cos(thetarad)
            x3 = (fr(y3) - cosa*tshell/2. - resin_bir_w2)*np.cos(thetarad)
            x4 = (fr(y4) - cosa*tshell/2.)*np.cos(thetarad)
            z1 = -(fr(y1) - cosa*tshell/2.)*np.sin(thetarad)
            z2 = -(fr(y2) - cosa*tshell/2. - resin_bir_w1)*np.sin(thetarad)
            z3 = -(fr(y3) - cosa*tshell/2. - resin_bir_w2)*np.sin(thetarad)
            z4 = -(fr(y4) - cosa*tshell/2.)*np.sin(thetarad)
            coords_1 = (x1, y1, z1)
            coords_2 = (x2, y2, z2)
            coords_3 = (x3, y3, z3)
            coords_4 = (x4, y4, z4)
            pt_1 = part_bir.DatumPointByCoordinate(coords=coords_1)
            pt_2 = part_bir.DatumPointByCoordinate(coords=coords_2)
            pt_3 = part_bir.DatumPointByCoordinate(coords=coords_3)
            pt_4 = part_bir.DatumPointByCoordinate(coords=coords_4)
            datum_1 = part_bir.datums[pt_1.id]
            datum_2 = part_bir.datums[pt_2.id]
            datum_3 = part_bir.datums[pt_3.id]
            datum_4 = part_bir.datums[pt_4.id]
            mean_coords = np.mean((coords_1, coords_2, coords_3, coords_4),
                                  axis=0)
            cell = part_bir.cells.findAt(mean_coords)
            try:
                part_bir.PartitionCellByPlaneThreePoints(cells=(cell,),
                        point1=datum_1, point2=datum_2, point3=datum_3)
            except:
                pass
            # cutting Bottom_OR
            y1 = 0.
            y2 = 0.
            y3 = resin_bot_h
            y4 = resin_bot_h
            x1 = (fr(y1) + cosa*tshell/2. + resin_bor_w1)*np.cos(thetarad)
            x2 = (fr(y2) + cosa*tshell/2.)*np.cos(thetarad)
            x3 = (fr(y3) + cosa*tshell/2.)*np.cos(thetarad)
            x4 = (fr(y4) + cosa*tshell/2. + resin_bor_w2)*np.cos(thetarad)
            z1 = -(fr(y1) + cosa*tshell/2. + resin_bor_w1)*np.sin(thetarad)
            z2 = -(fr(y2) + cosa*tshell/2.)*np.sin(thetarad)
            z3 = -(fr(y3) + cosa*tshell/2.)*np.sin(thetarad)
            z4 = -(fr(y4) + cosa*tshell/2. + resin_bor_w2)*np.sin(thetarad)
            coords_1 = (x1, y1, z1)
            coords_2 = (x2, y2, z2)
            coords_3 = (x3, y3, z3)
            coords_4 = (x4, y4, z4)
            pt_1 = part_bor.DatumPointByCoordinate(coords=coords_1)
            pt_2 = part_bor.DatumPointByCoordinate(coords=coords_2)
            pt_3 = part_bor.DatumPointByCoordinate(coords=coords_3)
            pt_4 = part_bor.DatumPointByCoordinate(coords=coords_4)
            datum_1 = part_bor.datums[pt_1.id]
            datum_2 = part_bor.datums[pt_2.id]
            datum_3 = part_bor.datums[pt_3.id]
            datum_4 = part_bor.datums[pt_4.id]
            mean_coords = np.mean((coords_1, coords_2, coords_3, coords_4),
                                  axis=0)
            cell = part_bor.cells.findAt(mean_coords)
            try:
                part_bor.PartitionCellByPlaneThreePoints(cells=(cell,),
                        point1=datum_1, point2=datum_2, point3=datum_3)
            except:
                pass
        if cc.resin_ring_top:
            # cutting the Top_IR
            y1 = H-resin_top_h
            y2 = H-resin_top_h
            y3 = H
            y4 = H
            x1 = (fr(y1) - cosa*tshell/2.)*np.cos(thetarad)
            x2 = (fr(y2) - cosa*tshell/2. - resin_tir_w1)*np.cos(thetarad)
            x3 = (fr(y3) - cosa*tshell/2. - resin_tir_w2)*np.cos(thetarad)
            x4 = (fr(y4) - cosa*tshell/2.)*np.cos(thetarad)
            z1 = -(fr(y1) - cosa*tshell/2.)*np.sin(thetarad)
            z2 = -(fr(y2) - cosa*tshell/2. - resin_tir_w1)*np.sin(thetarad)
            z3 = -(fr(y3) - cosa*tshell/2. - resin_tir_w2)*np.sin(thetarad)
            z4 = -(fr(y4) - cosa*tshell/2.)*np.sin(thetarad)
            coords_1 = (x1, y1, z1)
            coords_2 = (x2, y2, z2)
            coords_3 = (x3, y3, z3)
            coords_4 = (x4, y4, z4)
            pt_1 = part_tir.DatumPointByCoordinate(coords=coords_1)
            pt_2 = part_tir.DatumPointByCoordinate(coords=coords_2)
            pt_3 = part_tir.DatumPointByCoordinate(coords=coords_3)
            pt_4 = part_tir.DatumPointByCoordinate(coords=coords_4)
            datum_1 = part_tir.datums[pt_1.id]
            datum_2 = part_tir.datums[pt_2.id]
            datum_3 = part_tir.datums[pt_3.id]
            datum_4 = part_tir.datums[pt_4.id]
            mean_coords = np.mean((coords_1, coords_2, coords_3, coords_4),
                                  axis=0)
            cell = part_tir.cells.findAt(mean_coords)
            try:
                part_tir.PartitionCellByPlaneThreePoints(cells=(cell,),
                        point1=datum_1, point2=datum_2, point3=datum_3)
            except:
                pass
            # cutting the Top_OR
            y1 = H-resin_top_h
            y2 = H-resin_top_h
            y3 = H
            y4 = H
            x1 = (fr(y1) + cosa*tshell/2. + resin_tor_w1)*np.cos(thetarad)
            x2 = (fr(y2) + cosa*tshell/2.)*np.cos(thetarad)
            x3 = (fr(y3) + cosa*tshell/2.)*np.cos(thetarad)
            x4 = (fr(y4) + cosa*tshell/2. + resin_tor_w2)*np.cos(thetarad)
            z1 = -(fr(y1) + cosa*tshell/2. + resin_tor_w1)*np.sin(thetarad)
            z2 = -(fr(y2) + cosa*tshell/2.)*np.sin(thetarad)
            z3 = -(fr(y3) + cosa*tshell/2.)*np.sin(thetarad)
            z4 = -(fr(y4) + cosa*tshell/2. + resin_tor_w2)*np.sin(thetarad)
            coords_1 = (x1, y1, z1)
            coords_2 = (x2, y2, z2)
            coords_3 = (x3, y3, z3)
            coords_4 = (x4, y4, z4)
            pt_1 = part_tor.DatumPointByCoordinate(coords=coords_1)
            pt_2 = part_tor.DatumPointByCoordinate(coords=coords_2)
            pt_3 = part_tor.DatumPointByCoordinate(coords=coords_3)
            pt_4 = part_tor.DatumPointByCoordinate(coords=coords_4)
            datum_1 = part_tor.datums[pt_1.id]
            datum_2 = part_tor.datums[pt_2.id]
            datum_3 = part_tor.datums[pt_3.id]
            datum_4 = part_tor.datums[pt_4.id]
            mean_coords = np.mean((coords_1, coords_2, coords_3, coords_4),
                                  axis=0)
            cell = part_tor.cells.findAt(mean_coords)
            try:
                part_tor.PartitionCellByPlaneThreePoints(cells=(cell,),
                        point1=datum_1, point2=datum_2, point3=datum_3)
            except:
                pass

    # cutting the shell along the meridian

    # Partition the top and bottom to have a finer mesh in this area to match
    # the mesh of the rings
    if cc.resin_ring_bottom:
        plane_bot = part_shell.DatumPlaneByPrincipalPlane(
                        principalPlane=XYPLANE, offset=resin_bot_h)
        part_shell.PartitionFaceByDatumPlane(
                        datumPlane=part_shell.datums[plane_bot.id],
                        faces=part_shell.faces)
    if cc.resin_ring_top:
        plane_top = part_shell.DatumPlaneByPrincipalPlane(
                            principalPlane=XYPLANE,
                            offset=H-resin_top_h)
        part_shell.PartitionFaceByDatumPlane(
                            datumPlane=part_shell.datums[plane_top.id],
                            faces=part_shell.faces)
    for pt in pts:
        plane = part_shell.DatumPlaneByPrincipalPlane(
                        principalPlane=XYPLANE, offset=pt*H)
        part_shell.PartitionFaceByDatumPlane(
                    datumPlane=part_shell.datums[plane.id],
                    faces=part_shell.faces)

    if cc.resin_ring_bottom:
        # Assign the material properties to Bottom_IR
        region = Region(cells=part_bir.cells)
        part_bir.SectionAssignment(region=region, sectionName='Rings',
                offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                thicknessAssignment=FROM_SECTION)
        # Assign the material properties to Bottom_OR
        region = Region(cells=part_bor.cells)
        part_bor.SectionAssignment(region=region, sectionName='Rings',
                offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                thicknessAssignment=FROM_SECTION)
    if cc.resin_ring_top:
        # Assign the material properties to Top_IR
        region = Region(cells=part_tir.cells)
        part_tir.SectionAssignment(region=region, sectionName='Rings',
                offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                thicknessAssignment=FROM_SECTION)
        # Assign the material properties to Top_OR
        region = Region(cells=part_tor.cells)
        part_tor.SectionAssignment(region=region, sectionName='Rings',
                offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
                thicknessAssignment=FROM_SECTION)

    for thetadeg in thetadegs:
        thetarad = np.deg2rad(thetadeg)
        if cc.resin_ring_bottom:
            # Seed partitioned top and bottom part_shell
            z = resin_bot_h/2.
            x = fr(z)*np.cos(thetarad)
            y = fr(z)*np.sin(thetarad)
            edge = part_shell.edges.findAt((x, y, z))
            part_shell.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                        constraint=FIXED)
        if cc.resin_ring_top:
            z = H - resin_bot_h/2.
            x = fr(z)*np.cos(thetarad)
            y = fr(z)*np.sin(thetarad)
            edge = part_shell.edges.findAt((x, y, z))
            part_shell.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                        constraint=FIXED)
        if cc.resin_ring_bottom:
            # Seed Bottom_IR
            y = 0.
            x = (fr(y) - cosa*tshell/2. - resin_bir_w1/2.)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2. - resin_bir_w1/2.)*np.sin(thetarad)
            edge = part_bir.edges.findAt((x, y, z))
            part_bir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = resin_bot_h
            x = (fr(y) - cosa*tshell/2. - resin_bir_w2/2.)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2. - resin_bir_w2/2.)*np.sin(thetarad)
            edge = part_bir.edges.findAt((x, y, z))
            part_bir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = resin_bot_h/2.
            x = (fr(y) - cosa*tshell/2.)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2.)*np.sin(thetarad)
            edge = part_bir.edges.findAt((x, y, z))
            part_bir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = resin_bot_h/2.
            resin_bir_wm = (resin_bir_w1 + resin_bir_w2)/2
            x = (fr(y) - cosa*tshell/2. - resin_bir_wm)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2. - resin_bir_wm)*np.sin(thetarad)
            edge = part_bir.edges.findAt((x, y, z))
            part_bir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            # Seed Bottom_OR
            y = 0.
            x = (fr(y) + cosa*tshell/2. + resin_bor_w1/2.)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2. + resin_bor_w1/2.)*np.sin(thetarad)
            edge = part_bor.edges.findAt((x, y, z))
            part_bor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = resin_bot_h
            x = (fr(y) + cosa*tshell/2. + resin_bor_w2/2.)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2. + resin_bor_w2/2.)*np.sin(thetarad)
            edge = part_bor.edges.findAt((x, y, z))
            part_bor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = resin_bot_h/2.
            x = (fr(y) + cosa*tshell/2.)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2.)*np.sin(thetarad)
            edge = part_bor.edges.findAt((x, y, z))
            part_bor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = resin_bot_h/2.
            resin_bor_wm = (resin_bor_w1 + resin_bor_w2)/2
            x = (fr(y) + cosa*tshell/2. + resin_bor_wm)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2. + resin_bor_wm)*np.sin(thetarad)
            edge = part_bor.edges.findAt((x, y, z))
            part_bor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
        if cc.resin_ring_top:
            # Seed Top_IR
            y = H-resin_top_h
            x = (fr(y) - cosa*tshell/2. - resin_tir_w1/2.)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2. - resin_tir_w1/2.)*np.sin(thetarad)
            edge = part_tir.edges.findAt((x, y, z))
            part_tir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = H
            x = (fr(y) - cosa*tshell/2. - resin_tir_w2/2.)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2. - resin_tir_w2/2.)*np.sin(thetarad)
            edge = part_tir.edges.findAt((x, y, z))
            part_tir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = H-resin_top_h/2.
            x = (fr(y) - cosa*tshell/2.)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2.)*np.sin(thetarad)
            edge = part_tir.edges.findAt((x, y, z))
            part_tir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = H-resin_top_h/2.
            resin_tir_wm = (resin_tir_w1 + resin_tir_w2)/2
            x = (fr(y) - cosa*tshell/2. - resin_tir_wm)*np.cos(thetarad)
            z = -(fr(y) - cosa*tshell/2. - resin_tir_wm)*np.sin(thetarad)
            edge = part_tir.edges.findAt((x, y, z))
            part_tir.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            # Seed Top_OR
            y = H-resin_top_h
            x = (fr(y) + cosa*tshell/2. + resin_tor_w1/2.)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2. + resin_tor_w1/2.)*np.sin(thetarad)
            edge = part_tor.edges.findAt((x, y, z))
            part_tor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = H
            x = (fr(y) + cosa*tshell/2. + resin_tor_w2/2.)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2. + resin_tor_w2/2.)*np.sin(thetarad)
            edge = part_tor.edges.findAt((x, y, z))
            part_tor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = H-resin_top_h/2.
            x = (fr(y) + cosa*tshell/2.)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2.)*np.sin(thetarad)
            edge = part_tor.edges.findAt((x, y, z))
            part_tor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)
            y = H-resin_top_h/2.
            resin_tor_wm = (resin_tor_w1 + resin_tor_w2)/2
            x = (fr(y) + cosa*tshell/2. + resin_tor_wm)*np.cos(thetarad)
            z = -(fr(y) + cosa*tshell/2. + resin_tor_wm)*np.sin(thetarad)
            edge = part_tor.edges.findAt((x, y, z))
            part_tor.seedEdgeByNumber(edges=(edge,), number=resin_numel,
                                      constraint=FIXED)

    # Seed Shell Cross Section Edges
    for z in [0, resin_bot_h, H-resin_top_h, H]:
        size = mesh_size*fr(z)/rmesh
        edges = part_shell.edges.getByBoundingBox(-2*rbot, -2*rbot, z-0.1,
                                                   2*rbot, 2*rbot, z+0.1)
        part_shell.seedEdgeBySize(edges=edges, size=size, constraint=FIXED)

    tmp = np.linspace(0.1, 359, 360)
    tmp = tmp[~np.in1d(tmp, thetadegs)]
    thetarads_search = np.deg2rad(tmp)
    if cc.resin_ring_bottom:
        # Seed Bottom_IR edges inner face
        coords = []
        y = 0.
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2. - resin_bir_w1)*np.cos(thetarad)
            z = -(r - cosa*tshell/2. - resin_bir_w1)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2. - resin_bir_w1)/rmesh
        edges = part_bir.edges.findAt(*tuple(coords), printWarning=False)
        part_bir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = resin_bot_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2. - resin_bir_w2)*np.cos(thetarad)
            z = -(r - cosa*tshell/2. - resin_bir_w2)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2. - resin_bir_w2)/rmesh
        edges = part_bir.edges.findAt(*tuple(coords), printWarning=False)
        part_bir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

        # Seed Bottom_IR edges outer face
        coords = []
        y = 0.
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2.)*np.cos(thetarad)
            z = -(r - cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2.)/rmesh
        edges = part_bir.edges.findAt(*tuple(coords), printWarning=False)
        part_bir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = resin_bot_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2.)*np.cos(thetarad)
            z = -(r - cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2.)/rmesh
        edges = part_bir.edges.findAt(*tuple(coords), printWarning=False)
        part_bir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

        # Seed Bottom_OR edges inner face
        coords = []
        y = 0.
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2.)*np.cos(thetarad)
            z = -(r + cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2.)/rmesh
        edges = part_bor.edges.findAt(*tuple(coords), printWarning=False)
        part_bor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = resin_bot_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2.)*np.cos(thetarad)
            z = -(r + cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2.)/rmesh
        edges = part_bor.edges.findAt(*tuple(coords), printWarning=False)
        part_bor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

        # Seed Bottom_OR edges outer face
        coords = []
        y = 0.
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2. + resin_bor_w1)*np.cos(thetarad)
            z = -(r + cosa*tshell/2. + resin_bor_w1)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2. + resin_bor_w1)/rmesh
        edges = part_bor.edges.findAt(*tuple(coords), printWarning=False)
        part_bor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = resin_bot_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2. + resin_bor_w2)*np.cos(thetarad)
            z = -(r + cosa*tshell/2. + resin_bor_w2)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2. + resin_bor_w2)/rmesh
        edges = part_bor.edges.findAt(*tuple(coords), printWarning=False)
        part_bor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

    if cc.resin_ring_top:
        # Seed Top_IR edges inner face
        coords = []
        y = H-resin_top_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2. - resin_tir_w1)*np.cos(thetarad)
            z = -(r - cosa*tshell/2. - resin_tir_w1)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2. - resin_tir_w1)/rmesh
        edges = part_tir.edges.findAt(*tuple(coords), printWarning=False)
        part_tir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = H
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2. - resin_tir_w2)*np.cos(thetarad)
            z = -(r - cosa*tshell/2. - resin_tir_w2)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2. - resin_tir_w2)/rmesh
        edges = part_tir.edges.findAt(*tuple(coords), printWarning=False)
        part_tir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

        # Seed Top_IR edges outer face
        coords = []
        y = H-resin_top_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2.)*np.cos(thetarad)
            z = -(r - cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2.)/rmesh
        edges = part_tir.edges.findAt(*tuple(coords), printWarning=False)
        part_tir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = H
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r - cosa*tshell/2.)*np.cos(thetarad)
            z = -(r - cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r - cosa*tshell/2.)/rmesh
        edges = part_tir.edges.findAt(*tuple(coords), printWarning=False)
        part_tir.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

        # Seed Top_OR edges inner face
        coords = []
        y = H-resin_top_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2.)*np.cos(thetarad)
            z = -(r + cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2.)/rmesh
        edges = part_tor.edges.findAt(*tuple(coords), printWarning=False)
        part_tor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = H
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2.)*np.cos(thetarad)
            z = -(r + cosa*tshell/2.)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2.)/rmesh
        edges = part_tor.edges.findAt(*tuple(coords), printWarning=False)
        part_tor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

        # Seed Top_OR edges outer face
        coords = []
        y = H-resin_top_h
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2. + resin_tor_w1)*np.cos(thetarad)
            z = -(r + cosa*tshell/2. + resin_tor_w1)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2. + resin_tor_w1)/rmesh
        edges = part_tor.edges.findAt(*tuple(coords), printWarning=False)
        part_tor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)
        coords = []
        y = H
        r = fr(y)
        for thetarad in thetarads_search:
            x = (r + cosa*tshell/2. + resin_tor_w2)*np.cos(thetarad)
            z = -(r + cosa*tshell/2. + resin_tor_w2)*np.sin(thetarad)
            coords.append(((x, y, z),))
        size = mesh_size*(r + cosa*tshell/2. + resin_tor_w2)/rmesh
        edges = part_tor.edges.findAt(*tuple(coords), printWarning=False)
        part_tor.seedEdgeBySize(edges=edges, size=size, constraint=FINER)

    # Mesh size for the shell
    part_shell.seedPart(size=mesh_size, deviationFactor=0.1,
                        minSizeFactor=0.1)
    elemType1 = mesh.ElemType(elemCode=elem_type, elemLibrary=STANDARD)
    part_shell.setElementType(regions=Region(faces=part_shell.faces),
                        elemTypes=(elemType1, ))
    part_shell.setMeshControls(regions=part_shell.faces, elemShape=QUAD,
                               technique=SWEEP)
    part_shell.generateMesh()
    if cc.resin_ring_bottom:
        part_bir.generateMesh()
        part_bor.generateMesh()
    if cc.resin_ring_top:
        part_tir.generateMesh()
        part_tor.generateMesh()

    ra = mod.rootAssembly
    ra.DatumCsysByDefault(CYLINDRICAL)
    inst_shell = ra.Instance(name=inst_name_shell, part=part_shell,
                             dependent=ON)
    ra_cyl_csys = ra.DatumCsysByThreePoints(name='ra_cyl_csys',
                              coordSysType=CYLINDRICAL,
                              origin=(0.0, 0.0, 0.0),
                              point1=(1.0, 0.0, 0.0),
                              point2=(0.0, 1.0, 0.0))
    ra_cyl_csys = ra.datums[ra_cyl_csys.id]

    # Regenerate the Part and the Assembly. Although the mesh is created
    # before it has to be updated again to be visible.
    if cc.resin_ring_bottom:
        part_bor.regenerate()
        part_bir.regenerate()
    if cc.resin_ring_top:
        part_tor.regenerate()
        part_tir.regenerate()
    part_shell.regenerate()
    ra.regenerate()

    # Instance the Rings
    if cc.resin_ring_bottom:
        inst_bir = ra.Instance(name='Bottom_IR', part=part_bir, dependent=ON)
        inst_bor = ra.Instance(name='Bottom_OR', part=part_bor, dependent=ON)
    if cc.resin_ring_top:
        inst_tir = ra.Instance(name='Top_IR', part=part_tir, dependent=ON)
        inst_tor = ra.Instance(name='Top_OR', part=part_tor, dependent=ON)

    # Rotate both 'Top_IR' and 'Top_OR'
    ring_names = []
    resin_hs = []
    if cc.resin_ring_bottom:
        ring_names += ['Bottom_IR', 'Bottom_OR']
        resin_hs += [resin_bot_h, resin_bot_h]
    if cc.resin_ring_top:
        ring_names += ['Top_IR', 'Top_OR']
        resin_hs += [resin_top_h, resin_top_h]
    ra.rotate(instanceList=ring_names, axisPoint=(0.0, 0.0, 0),
              axisDirection=(1,0,0), angle=90)

    # Distance matrix to find closest node pairs
    shell_nodes = ra.instances[inst_name_shell].nodes
    shell_bot_nodes = shell_nodes.getByBoundingBox(-2*rbot, -2*rbot, -0.1,
                                                    2*rbot, 2*rbot,
                                                    1.01*resin_bot_h)
    shell_top_nodes = shell_nodes.getByBoundingBox(-2*rbot, -2*rbot,
                                                    H-1.001*resin_top_h,
                                                    2*rbot, 2*rbot, H+0.1)
    shell_edge_nodes = np.array(list(shell_bot_nodes)
                                + list(shell_top_nodes))

    shell_coords = np.array([n.coordinates for n in shell_edge_nodes])

    # creating the PIN connections between the shell and bot/top ring faces
    slaves_set = []
    for i, ring_name in enumerate(ring_names):
        resin_h = resin_hs[i]
        inst = ra.instances[ring_name]
        slave_nodes = inst.nodes
        slave_coords = np.array([n.coordinates for n in slave_nodes])
        dist = np.subtract.outer(shell_coords[:,0], slave_coords[:,0])**2
        dist += np.subtract.outer(shell_coords[:,1], slave_coords[:,1])**2
        dist += np.subtract.outer(shell_coords[:,2], slave_coords[:,2])**2
        if not cc.bc_gaps_top_edge:
            # this will skip the last row of nodes at the top edge
            valid_indices = ((dist.min(axis=1)<=(tshell*0.51)**2)
                              & (shell_coords[:,2]<=(H-0.01*resin_h)))
        else:
            valid_indices = (dist.min(axis=1)<=(tshell*0.51)**2)
        if False:
            # this will skip the last row of nodes at bottom and top
            valid_indices = ((dist.min(axis=1)<=(tshell*0.51)**2)
                              & (shell_coords[:,2]>=0.01*resin_h)
                              & (shell_coords[:,2]<=(H-0.01*resin_h)))

        closest_indices = dist[valid_indices].argsort(axis=1)[:,0]
        master_nodes = shell_edge_nodes[valid_indices]
        sorted_slave_nodes = np.array(slave_nodes)[closest_indices]
        ssn = sorted_slave_nodes
        for master, slave in zip(master_nodes, sorted_slave_nodes):
            master_name = 'shell_{0}'.format(master.label)
            if not master_name in ra.sets.keys():
                nodes = inst_shell.nodes.sequenceFromLabels((master.label,))
                master_set = ra.Set(nodes=nodes, name=master_name)
            else:
                master_set = ra.sets[master_name]
            slave_name = '{0}_{1}'.format(ring_name, slave.label)
            if not slave_name in ra.sets.keys():
                nodes = inst.nodes.sequenceFromLabels((slave.label,))
                slave_set = ra.Set(nodes=nodes, name=slave_name)
            else:
                slave_set = ra.sets[slave_name]
                warn('WARNING repeated slave node', slave.label)
                #TODO maybe raise an error?
            slaves_set.append(ring_name + '.' + str(slave.label))
            mpc_name = 'shell_{0}_{1:04d}_{2:04d}'.format(ring_name,
                       master.label, slave.label)
            mod.MultipointConstraint(name=mpc_name,
                                     controlPoint=master_set,
                                     surface=slave_set,
                                     mpcType=PIN_MPC,
                                     userMode=DOF_MODE_MPC,
                                     userType=0, csys=ra_cyl_csys)

    assert len(slaves_set)==len(set(slaves_set))

    if False:
        # This creates the connection between the shell and top nodes, which
        # will be avoided in most of the cases...

        # creating the top connections between shell and rings
        top_master_sets = []
        top_slave_sets = []
        for i, ring_name in enumerate(ring_names):
            resin_h = resin_hs[i]
            inst = ra.instances[ring_name]
            slave_nodes = ra.instances[ring_name].nodes
            slave_coords = np.array([n.coordinates for n in slave_nodes])
            shell_angles = np.arctan2(shell_coords[:,1], shell_coords[:,0])
            shell_x = rbot*np.cos(shell_angles)
            shell_y = rbot*np.sin(shell_angles)
            slave_angles = np.arctan2(slave_coords[:,1], slave_coords[:,0])
            slave_x = rbot*np.cos(slave_angles)
            slave_y = rbot*np.sin(slave_angles)
            dist = np.subtract.outer(shell_x, slave_x)**2
            dist += np.subtract.outer(shell_y, slave_y)**2
            dist += np.subtract.outer(shell_coords[:,2], slave_coords[:,2])**2
            valid_indices = ((dist.min(axis=1)<=0.1)
                             & (shell_coords[:,2] > (H-0.01*resin_h)))
            closest_indices = dist[valid_indices].argsort(axis=1)[
                                :,0:(resin_numel+1)]
            # Slicing the first resin_numel elements

            master_nodes = shell_edge_nodes[valid_indices]
            sorted_slave_nodes = np.array(slave_nodes)[closest_indices]
            for master, slaves in zip(master_nodes, sorted_slave_nodes):
                master_name = 'shell_{0}'.format(master.label)
                if not master_name in ra.sets.keys():
                    nodes = inst_shell.nodes.sequenceFromLabels((master.label,))
                    master_set = ra.Set(nodes=nodes, name=master_name)
                    top_master_sets.append(master_set)
                else:
                    master_set = ra.sets[master_name]
                for slave in slaves:
                    slave_name = '{0}_{1}'.format(ring_name, slave.label)
                    if not slave_name in ra.sets.keys():
                        nodes = inst.nodes.sequenceFromLabels((slave.label,))
                        slave_set = ra.Set(nodes=nodes, name=slave_name)
                        top_slave_sets.append(slave_set)
                    else:
                        slave_set = ra.sets[slave_name]
                        print('WARNING repeated slave node {0}, for {1}'.format(
                              slave.label, slave_name))
                        #TODO maybe raise an error?
                    slaves_set.append(ring_name + '.' + str(slave.label))
                    mpc_name = 'shell_top_{0}_{1:04d}_{2:04d}'.format(ring_name,
                               master.label, slave.label)
                    mod.MultipointConstraint(name=mpc_name,
                            controlPoint=master_set, surface=slave_set,
                            mpcType=PIN_MPC, userMode=DOF_MODE_MPC, userType=0,
                            csys=ra_cyl_csys)

        assert len(slaves_set)==len(set(slaves_set))
        assert len(top_slave_sets)==len(top_master_sets)*(resin_numel+1)*2

    # Creating sets

    ra.Set(faces=inst_shell.faces, name='shell_faces')

    if cc.resin_ring_bottom:
        faces = ra.instances['Bottom_IR'].faces
        bot_IR_faces = faces.getByBoundingBox(-2*rbot, -2*rbot, -0.0001,
                                               2*rbot, 2*rbot, 0.0001)
        ra.Set(faces=bot_IR_faces, name='Bottom_IR_faces')
        ra.Set(cells=inst_bir.cells, name='resin_ring_Bottom_IR')
        faces = ra.instances['Bottom_OR'].faces
        bot_OR_faces = faces.getByBoundingBox(-2*rbot, -2*rbot, -0.0001,
                                               2*rbot, 2*rbot, 0.0001)
        ra.Set(faces=bot_OR_faces, name='Bottom_OR_faces')
        ra.Set(cells=inst_bor.cells, name='resin_ring_Bottom_OR')
    if cc.resin_ring_top:
        faces = ra.instances['Top_IR'].faces
        top_IR_faces = faces.getByBoundingBox(-2*rbot, -2*rbot, 0.999*H,
                                               2*rbot, 2*rbot, 1.001*H)
        ra.Set(faces=top_IR_faces, name='Top_IR_faces')
        ra.Set(cells=inst_tir.cells, name='resin_ring_Top_IR')
        faces = ra.instances['Top_OR'].faces
        top_OR_faces = faces.getByBoundingBox(-2*rbot, -2*rbot, 0.999*H,
                                               2*rbot, 2*rbot, 1.001*H)
        ra.Set(faces=top_OR_faces, name='Top_OR_faces')
        ra.Set(cells=inst_tor.cells, name='resin_ring_Top_OR')

    edges_shell = ra.instances[inst_name_shell].edges
    shell_bottom_edges = edges_shell.getByBoundingBox(
            -2*rbot, -2*rbot, -0.0001, 2*rbot, 2*rbot, 0.0001)
    ra.Set(edges=shell_bottom_edges, name='shell_bottom_edges')
    shell_top_edges = edges_shell.getByBoundingBox(
            -2*rbot, -2*rbot, 0.999*H, 2*rbot, 2*rbot, 1.001*H)
    ra.Set(edges=shell_top_edges, name='shell_top_edges')

    rp_bot = ra.ReferencePoint(point=(0, 0, 0))
    ra.features.changeKey(fromName='RP-1', toName='RP_bot')
    rp_top = ra.ReferencePoint(point=(0, 0, H))
    ra.features.changeKey(fromName='RP-1', toName='RP_top')
    rps = ra.referencePoints
    refPoints1=(rps[rp_bot.id],)
    ra.Set(referencePoints=refPoints1, name='RP_bot')
    refPoints1=(rps[rp_top.id],)
    ra.Set(referencePoints=refPoints1, name='RP_top')

def _create_load_steps(cc):
    mod = mdb.models[cc.model_name]
    ra = mod.rootAssembly
    minInc1 = cc.minInc1
    maxInc1 = cc.maxInc1
    initialInc1 = cc.initialInc1
    maxNumInc1 = cc.maxNumInc1
    minInc2 = cc.minInc2
    maxInc2 = cc.maxInc2
    initialInc2 = cc.initialInc2
    maxNumInc2 = cc.maxNumInc2
    damping_factor1 = cc.damping_factor1
    damping_factor2 = cc.damping_factor2
    ncpus = cc.ncpus
    if not cc.linear_buckling:
        if cc.separate_load_steps:
            cc.step1Name = 'constant_loads'
            cc.step2Name = 'incremented_loads'
            if damping_factor1==None:
                mod.StaticStep(name='constant_loads', previous='Initial',
                        nlgeom=ON, maxNumInc=maxNumInc1,
                        stabilizationMethod=NONE, initialInc=initialInc1,
                        minInc=minInc1, maxInc=maxInc1)
            else:
                mod.StaticStep(name='constant_loads', previous='Initial',
                        nlgeom=ON, maxNumInc=maxNumInc1,
                        stabilizationMethod=DAMPING_FACTOR,
                        stabilizationMagnitude=damping_factor1,
                        initialInc=initialInc1, minInc=minInc1,
                        maxInc=maxInc1, extrapolation=LINEAR)

            if damping_factor2==None:
                mod.StaticStep(name='incremented_loads',
                        previous='constant_loads', nlgeom=ON,
                        maxNumInc=maxNumInc2, stabilizationMethod=NONE,
                        initialInc=initialInc2, minInc=minInc2,
                        maxInc=maxInc2)
            else:
                mod.StaticStep(name='incremented_loads',
                        previous='constant_loads', nlgeom=ON,
                        maxNumInc=maxNumInc2,
                        stabilizationMethod=DAMPING_FACTOR,
                        stabilizationMagnitude=damping_factor2,
                        initialInc=initialInc2, minInc=minInc2,
                        maxInc=maxInc2, extrapolation=LINEAR)
        else:
            cc.step1Name = 'incremented_loads'
            cc.step2Name = 'incremented_loads'
            if damping_factor2==None:
                mod.StaticStep(name='incremented_loads', previous='Initial',
                        nlgeom=ON, maxNumInc=maxNumInc2,
                        stabilizationMethod=NONE, initialInc=initialInc2,
                        minInc=minInc2, maxInc=maxInc2)
            else:
                mod.StaticStep(name='incremented_loads', previous='Initial',
                        nlgeom=ON, maxNumInc=maxNumInc2,
                        stabilizationMethod=DAMPING_FACTOR,
                        stabilizationMagnitude=damping_factor2,
                        initialInc=initialInc2, minInc=minInc2,
                        maxInc=maxInc2, extrapolation=LINEAR)
    else:
        cc.step1Name = 'linear_buckling_step'
        cc.step2Name = 'linear_buckling_step'
        mod.BuckleStep(name=cc.step1Name, previous='Initial',
                numEigen=NUM_LB_MODES, eigensolver=LANCZOS, minEigen=0.,
                blockSize=DEFAULT, maxBlocks=DEFAULT)

    # create the job
    job = mdb.Job(name=mod.name, model=mod.name, numCpus=ncpus,
                  numDomains=ncpus)

def _create_loads_bcs(cc):
    mod = mdb.models[cc.model_name]
    ra = mod.rootAssembly
    ra_cyl_csys = ra.features['ra_cyl_csys']
    ra_cyl_csys = ra.datums[ra_cyl_csys.id]
    set_RP_bot = ra.sets['RP_bot']
    set_RP_top = ra.sets['RP_top']
    shell_bottom_edges = ra.sets['shell_bottom_edges'].edges
    shell_top_edges = ra.sets['shell_top_edges'].edges
    set_shell_faces = ra.sets['shell_faces']

    distr_load_top = cc.distr_load_top

    if not distr_load_top:
        mod.DisplacementBC(name='BC_RP_top',
                           createStepName='Initial', region=set_RP_top,
                           u1=SET, u2=SET, u3=UNSET,
                           ur1=SET, ur2=SET, ur3=SET,
                           amplitude=UNSET, distributionType=UNIFORM,
                           fieldName='', localCsys=ra_cyl_csys)

    bc_fix_bottom_uR = UNSET
    if cc.bc_fix_bottom_uR:
        bc_fix_bottom_uR = SET
    bc_fix_bottom_v = UNSET
    if cc.bc_fix_bottom_v:
        bc_fix_bottom_v = SET
    bc_fix_bottom_u3 = SET
    if cc.impconf.uneven_bottom_edge:
        bc_fix_bottom_u3 = UNSET
        mod.DisplacementBC(name='BC_RP_bot',
                           createStepName='Initial', region=set_RP_bot,
                           u1=SET, u2=SET, u3=SET,
                           ur1=SET, ur2=SET, ur3=SET,
                           amplitude=UNSET, distributionType=UNIFORM,
                           fieldName='', localCsys=ra_cyl_csys)


    # boundary condition at the bottom edge
    if cc.resin_ring_bottom:
        region = ra.sets['Bottom_IR_faces']
        if (bc_fix_bottom_uR==SET or bc_fix_bottom_v==SET or
            bc_fix_bottom_u3==SET):
            mod.DisplacementBC(name='BC_Bottom_IR',
                               createStepName='Initial', region=region,
                               u1=bc_fix_bottom_uR,
                               u2=bc_fix_bottom_v,
                               u3=bc_fix_bottom_u3,
                               ur1=UNSET,
                               ur2=UNSET,
                               ur3=UNSET,
                               amplitude=UNSET, distributionType=UNIFORM,
                               fieldName='', localCsys=ra_cyl_csys)
            region = ra.sets['Bottom_OR_faces']
            mod.DisplacementBC(name='BC_Bottom_OR',
                               createStepName='Initial', region=region,
                               u1=bc_fix_bottom_uR,
                               u2=bc_fix_bottom_v,
                               u3=bc_fix_bottom_u3,
                               ur1=UNSET,
                               ur2=UNSET,
                               ur3=UNSET,
                               amplitude=UNSET, distributionType=UNIFORM,
                               fieldName='', localCsys=ra_cyl_csys)
    ur1_bottom = UNSET
    ur2_bottom = UNSET
    ur3_bottom = UNSET
    if not cc.resin_ring_bottom and cc.bc_bottom_clamped:
        ur1_bottom = SET
        ur2_bottom = SET
        ur3_bottom = SET
    if (bc_fix_bottom_uR==SET or bc_fix_bottom_v==SET or bc_fix_bottom_u3==SET
        or ur1_bottom==SET or ur2_bottom==SET or ur3_bottom==SET):
        mod.DisplacementBC(name='BC_Bottom_Shell',
                           createStepName='Initial',
                           region=Region(edges=shell_bottom_edges),
                           u1=bc_fix_bottom_uR,
                           u2=bc_fix_bottom_v,
                           u3=bc_fix_bottom_u3,
                           ur1=ur1_bottom,
                           ur2=ur2_bottom,
                           ur3=ur3_bottom,
                           amplitude=UNSET, fixed=OFF,
                           distributionType=UNIFORM, fieldName='',
                           localCsys=ra_cyl_csys)

    bc_fix_top_uR = UNSET
    if cc.bc_fix_top_uR:
        bc_fix_top_uR = SET
    bc_fix_top_v = UNSET
    if cc.bc_fix_top_v:
        bc_fix_top_v = SET

    # boundary conditions at the top edge
    if cc.resin_ring_top:
        region = ra.sets['Top_IR_faces']
        if cc.bc_fix_top_uR or cc.bc_fix_top_v:
            mod.DisplacementBC(name='BC_Top_IR',
                               createStepName='Initial', region=region,
                               u1=bc_fix_top_uR,
                               u2=bc_fix_top_v,
                               u3=UNSET,
                               ur1=UNSET,
                               ur2=UNSET,
                               ur3=UNSET,
                               amplitude=UNSET, distributionType=UNIFORM,
                               fieldName='', localCsys=ra_cyl_csys)
            region = ra.sets['Top_OR_faces']
            mod.DisplacementBC(name='BC_Top_OR',
                               createStepName='Initial', region=region,
                               u1=bc_fix_top_uR,
                               u2=bc_fix_top_v,
                               u3=UNSET,
                               ur1=UNSET,
                               ur2=UNSET,
                               ur3=UNSET,
                               amplitude=UNSET, distributionType=UNIFORM,
                               fieldName='', localCsys=ra_cyl_csys)
    ur1_top = UNSET
    ur2_top = UNSET
    ur3_top = UNSET
    if not cc.resin_ring_top and cc.bc_top_clamped:
        ur1_top = SET
        ur2_top = SET
        ur3_top = SET
    if (cc.bc_fix_top_uR or cc.bc_fix_top_v
        or (not cc.resin_ring_top and cc.bc_top_clamped)):
        mod.DisplacementBC(name='BC_Top_Shell',
                           createStepName='Initial',
                           region=Region(edges=shell_top_edges),
                           u1=bc_fix_top_uR,
                           u2=bc_fix_top_v,
                           u3=UNSET,
                           ur1=ur1_top,
                           ur2=ur2_top,
                           ur3=ur3_top,
                           amplitude=UNSET, fixed=OFF,
                           distributionType=UNIFORM, fieldName='',
                           localCsys=ra_cyl_csys)

    # field outputs
    if cc.linear_buckling:
        mod.fieldOutputRequests.changeKey(fromName='F-Output-1',
                                          toName='shell_outputs')
        mod.fieldOutputRequests['shell_outputs'].setValues(
                               variables=('U',),
                               createStepName=cc.step2Name,
                               region=set_shell_faces)
        if cc.resin_ring_bottom:
            set_Bottom_IR = ra.sets['resin_ring_Bottom_IR']
            set_Bottom_OR = ra.sets['resin_ring_Bottom_OR']
            mod.FieldOutputRequest(name='Bottom_IR', region=set_Bottom_IR,
                    createStepName=cc.step2Name,
                    variables=('U',))
            mod.FieldOutputRequest(name='Bottom_OR', region=set_Bottom_OR,
                    createStepName=cc.step2Name,
                    variables=('U',))
        if cc.resin_ring_top:
            set_Top_IR = ra.sets['resin_ring_Top_IR']
            set_Top_OR = ra.sets['resin_ring_Top_OR']
            mod.FieldOutputRequest(name='Top_IR', region=set_Top_IR,
                    createStepName=cc.step2Name,
                    variables=('U',))
            mod.FieldOutputRequest(name='Top_OR', region=set_Top_OR,
                    createStepName=cc.step2Name,
                    variables=('U',))
    else:
        mod.fieldOutputRequests.changeKey(fromName='F-Output-1',
                                          toName='shell_outputs')
        mod.fieldOutputRequests['shell_outputs'].setValues(
                               variables=('S', 'SF', 'U', 'RF', 'NFORC'),
                               region=set_shell_faces,
                               timeInterval=cc.timeInterval, timeMarks=OFF)
        if cc.resin_ring_bottom:
            set_Bottom_IR = ra.sets['resin_ring_Bottom_IR']
            set_Bottom_OR = ra.sets['resin_ring_Bottom_OR']
            mod.FieldOutputRequest(name='Bottom_IR', region=set_Bottom_IR,
                    createStepName=cc.step2Name,
                    variables=('S', 'U', 'RF'),
                    timeInterval=cc.timeInterval, timeMarks=OFF)
            mod.FieldOutputRequest(name='Bottom_OR', region=set_Bottom_OR,
                    createStepName=cc.step2Name,
                    variables=('S', 'U', 'RF'),
                    timeInterval=cc.timeInterval, timeMarks=OFF)
        if cc.resin_ring_top:
            set_Top_IR = ra.sets['resin_ring_Top_IR']
            set_Top_OR = ra.sets['resin_ring_Top_OR']
            mod.FieldOutputRequest(name='Top_IR', region=set_Top_IR,
                    createStepName=cc.step2Name,
                    variables=('S', 'U', 'RF'),
                    timeInterval=cc.timeInterval, timeMarks=OFF)
            mod.FieldOutputRequest(name='Top_OR', region=set_Top_OR,
                    createStepName=cc.step2Name,
                    variables=('S', 'U', 'RF'),
                    timeInterval=cc.timeInterval, timeMarks=OFF)

        # history outputs
        mod.historyOutputRequests.changeKey(fromName='H-Output-1',
                                            toName='energy')
        mod.HistoryOutputRequest(name='RP_top',
                                 createStepName=cc.step1Name,
                                 variables=('U3','RF3' ),
                                 region=set_RP_top)

    if not cc.linear_buckling:
        # applying imperfections
        cc.impconf.create()
        if cc.pressure_load:
            region = Region(side2Faces=set_shell_faces.faces)
            mod.Pressure(name='pressure',
                    createStepName=cc.get_step_name(cc.pressure_step),
                    region=region, magnitude=cc.pressure_load)
        if cc.displ_controlled:
            rp_top_region = Region(referencePoints=set_RP_top.referencePoints)
            mod.DisplacementBC(name='axial_displ_RP_top',
                    createStepName=cc.get_step_name(cc.axial_step),
                    region=rp_top_region, u1=UNSET, u2=UNSET,
                    u3=-abs(cc.axial_displ), ur1=UNSET, ur2=UNSET, ur3=UNSET,
                    amplitude=UNSET, fixed=OFF, distributionType=UNIFORM,
                    fieldName='', localCsys=ra_cyl_csys)
        else:
            if not distr_load_top:
                rp_top_region = Region(referencePoints=
                                       set_RP_top.referencePoints)
                mod.ConcentratedForce(name='load_RP_top',
                        createStepName=cc.get_step_name(cc.axial_step),
                        region=rp_top_region, cf3=-abs(cc.axial_load),
                        distributionType=UNIFORM, field='',
                        localCsys=ra_cyl_csys)
            else:
                if cc.Nxxtop:
                    Nxxtop = str(cc.Nxxtop)
                    mod.ExpressionField(name='Nxxtop', localCsys=ra_cyl_csys,
                            description='', expression=Nxxtop)
                    if cc.Nxxtop_vec:
                        region = Region(side1Edges=shell_top_edges)
                        mod.ShellEdgeLoad(name='Nxxtop',
                                createStepName=cc.get_step_name(cc.axial_step),
                                region=region, magnitude=1.0,
                                directionVector=cc.Nxxtop_vec,
                                distributionType=FIELD, field='Nxxtop',
                                localCsys=ra_cyl_csys, traction=GENERAL,
                                resultant=ON)
                    else:
                        region = Region(side1Edges=shell_top_edges)
                        mod.ShellEdgeLoad(name='Nxxtop',
                                createStepName=cc.get_step_name(cc.axial_step),
                                region=region, magnitude=1.0,
                                distributionType=FIELD, field='Nxxtop',
                                localCsys=None, resultant=ON)
                else:
                    if cc.Nxxtop_vec:
                        per = 2*np.pi*cc.rtop
                        Nxxtop = cc.axial_load/per
                        region = Region(side1Edges=shell_top_edges)
                        mod.ShellEdgeLoad(name='Nxxtop',
                                createStepName=cc.get_step_name(cc.axial_step),
                                region=region, magnitude=Nxxtop,
                                directionVector=cc.Nxxtop_vec,
                                distributionType=UNIFORM, field='',
                                localCsys=ra_cyl_csys, traction=GENERAL,
                                resultant=ON)
                    else:
                        per = 2*np.pi*cc.rtop*np.cos(cc.alpharad)
                        Nxxtop = cc.axial_load/per
                        region = Region(side1Edges=shell_top_edges)
                        mod.ShellEdgeLoad(name='Nxxtop',
                                createStepName=cc.get_step_name(cc.axial_step),
                                region=region, magnitude=Nxxtop,
                                distributionType=UNIFORM, field='',
                                localCsys=None, resultant=ON)
    else:
        if distr_load_top:
            if cc.Nxxtop_vec:
                region = Region(side1Edges=shell_top_edges)
                Nxxtop_uni = 1.0/(2*np.pi*cc.rtop)
                mod.ShellEdgeLoad(name='Nxxtop',
                        createStepName=cc.get_step_name(cc.axial_step),
                        region=region,
                        magnitude=Nxxtop_uni, directionVector=cc.Nxxtop_vec,
                        distributionType=UNIFORM, field='',
                        localCsys=ra_cyl_csys, traction=GENERAL, resultant=ON)
            else:
                region = Region(side1Edges=shell_top_edges)
                Nxxtop_uni = 1.0/(2*np.pi*cc.rtop*np.cos(cc.alpharad))
                mod.ShellEdgeLoad(name='Nxxtop',
                        createStepName=cc.get_step_name(cc.axial_step),
                        region=region, magnitude=Nxxtop_uni,
                        distributionType=UNIFORM, field='', localCsys=None,
                        resultant=ON)
        else:
            rp_top_region = Region(referencePoints=set_RP_top.referencePoints)
            mod.ConcentratedForce(name='load_RP_top',
                    createStepName=cc.step1Name, region=rp_top_region,
                    cf3=-1., distributionType=UNIFORM, field='',
                    localCsys=ra_cyl_csys)

        text  = '** -----------------------------------------------------------'
        text += '\n**'
        text += '\n*NODE FILE'
        text += '\nU,'
        text += '\n*MODAL FILE'
        abaqus_functions.edit_keywords(mod=mod, text=text,
                                       before_pattern=None)

    if not distr_load_top and not cc.bc_gaps_top_edge:
        mod.MultipointConstraint(name='MPC_RP_top_shell',
                                 controlPoint=set_RP_top,
                                 surface=Region(edges=shell_top_edges),
                                 mpcType=PIN_MPC,
                                 userMode=DOF_MODE_MPC,
                                 userType=0, csys=ra_cyl_csys)
        if cc.resin_ring_top:
            top_IR_faces = ra.sets['Top_IR_faces'].faces
            mod.MultipointConstraint(name='MPC_RP_Top_IR',
                                     controlPoint=set_RP_top,
                                     surface=Region(faces=top_IR_faces),
                                     mpcType=PIN_MPC,
                                     userMode=DOF_MODE_MPC,
                                     userType=0, csys=ra_cyl_csys)
            top_OR_faces = ra.sets['Top_OR_faces'].faces
            mod.MultipointConstraint(name='MPC_RP_Top_OR',
                                     controlPoint=set_RP_top,
                                     surface=Region(faces=top_OR_faces),
                                     mpcType=PIN_MPC,
                                     userMode=DOF_MODE_MPC,
                                     userType=0, csys=ra_cyl_csys)

        # NOTE needed for the "job_stopper.py"
        text  = '** -------------------------------------------------------'
        text += '\n**'
        text += '\n*NODE PRINT, nset=RP_top'
        text += '\nRF3, U3'
        abaqus_functions.edit_keywords(mod=mod, text=text,
                                       before_pattern="*End Step")

    vp = session.viewports[session.currentViewportName]
    part_shell = mod.parts[cc.part_name_shell]
    vp.setValues(displayedObject=part_shell)
    vp.setValues(displayedObject=ra)
    vp.assemblyDisplay.setValues(interactions=ON, constraints=ON,
            connectors=ON, engineeringFeatures=ON, mesh=ON)
    ra.regenerate()

if __name__=='__main__':
    import conecyl
    cc = conecyl.ConeCyl()
    cc.impconf.add_pload(0., 0.5, 0.1, 1)
    cc.pressure_load = 0
    cc.pressure_step = 2
    cc.linear_buckling = False
    cc.resin_ring_bottom = False
    cc.resin_ring_top = False
    cc.bc_bottom_clamped = True
    cc.bc_top_clamped = False
    cc.bc_fix_top_uR = True
    cc.bc_fix_top_v = False
    cc.from_DB('degenhardt_2010_z15')
    cc.numel_r = 240
    cc.elem_type = 'S4R'
    cc.model_name = 'test'
    cc.displ_controlled = True
    #cc.Nxxtop_vec = ((0,0,0), (0,0,-1))
    cc.axial_displ = 1.
    #cc.axial_load = 100000
    cc.rebuild()
    _create_mesh(cc)
    _create_load_steps(cc)
    _create_loads_bcs(cc)




