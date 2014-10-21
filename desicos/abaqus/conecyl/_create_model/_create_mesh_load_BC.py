import __main__

import numpy as np
from regionToolset import Region
from abaqusConstants import *

from desicos.abaqus.abaqus_functions import (static_step,
                                             displacementBC,
                                             edit_keywords)
import desicos.abaqus.geom as geom
from desicos.abaqus.constants import *

def set_unset(boolvalue):
    if boolvalue:
        return SET
    else:
        return UNSET

def _create_mesh_load_BC(self):
    part = self.part
    #
    # SEEDING EDGES
    # defining mesh controls
    if self.elem_type in SHELL_TRIAS:
        part.setMeshControls(regions   = part.faces,
                             elemShape = TRI,
                             algorithm = NON_DEFAULT)
    else:
        if len(self.cutouts)>0:
            part.setMeshControls(regions   = part.faces,
                                 elemShape = QUAD,
                                 algorithm = ADVANCING_FRONT,
                                 allowMapped = True)
        else:
            part.setMeshControls(regions   = part.faces,
                                 elemShape = QUAD,
                                 algorithm = MEDIAL_AXIS)

    #DEFINING THE MESH SEEDS ALONG ALL EDGES
    #if len(self.cutouts) > 0:
        #for cutout in self.cutouts:
            #print cutout.inner_edges
            #print cutout.middle_edges
            #print cutout.outer_edges

    if True:
        for cs in self.cross_sections:
            for edge in cs.part_edges:
                elsize_r1 = self.elsize_r
                elsize_r2 = self.elsize_r2
                elsize = cs.z/self.h * (elsize_r2 - elsize_r1) + elsize_r1
                edge_size = edge.getSize(printResults=False)
                elnum = int(round(edge_size/elsize))
                part.seedEdgeByNumber(edges = (edge,),
                                      number = elnum,
                                      constraint = FREE)
        for meridian in self.meridians:
            for edge in meridian.part_edges:
                edge_size = edge.getSize(printResults=False)
                elsize_h = self.elsize_h
                elnum = int(round(edge_size/elsize_h))
                part.seedEdgeByNumber(edges = (edge,),
                                      number = elnum,
                                      constraint = FREE)
    else:
        for cs in self.cross_sections:
            for edge in cs.part_edges:
                elsize_r1 = self.elsize_r
                elsize_r2 = self.elsize_r2
                elsize = cs.z/self.h * (elsize_r2 - elsize_r1) + elsize_r1
                part.seedEdgeBySize(edges = (edge,),
                                    size = elsize,
                                    constraint = FREE)

    import mesh
    elemtype = mesh.ElemType(elemCode = eval(self.elem_type),
                             elemLibrary = STANDARD)
    part.setElementType(regions = Region(faces = part.faces),
                        elemTypes = (elemtype,))
    # assemblying the cylinder - creating instance
    mod = self.mod
    assembly = mod.rootAssembly
    inst = assembly.Instance(name='InstanceCylinder', part=part, dependent=ON)
    self.inst = inst
    # creating the top reference point
    maxgap = self.r2*2*np.tan(self.betarad)
    assembly.ReferencePoint(point=(0.0, 0.0, self.h+maxgap))
    self.rp_top = assembly.referencePoints.values()[0]
    # finding instance edges
    import _read_and_map
    _read_and_map._map_edges(self, objname='instance')
    # finding vertices for imperfections
    for imp in self.impconf.imperfections:
        imp.vertice = inst.vertices.findAt(((imp.x, imp.y, imp.z),))
    if self.linear_buckling == True:
        # creating linear buckling analysis step
        self.step1Name = 'Linear_Buckling_Step'
        self.step2Name = self.step1Name
        mod.BuckleStep(name = self.step1Name,
                       previous = 'Initial',
                       numEigen = NUM_LB_MODES,
                       eigensolver = LANCZOS,
                       minEigen = None,
                       blockSize = DEFAULT,
                       maxBlocks = DEFAULT)
    elif self.rsm:
        self.step1Name = 'RSM'
        self.step2Name = 'RSM'
        # creating perturbation load step
        static_step(model                  = mod,
                    name                   = self.step1Name,
                    previous               = 'Initial',
                    damping                = self.artificial_damping1,
                    initialInc             = self.initialInc1,
                    maxNumInc              = self.maxNumInc1,
                    minInc                 = self.minInc1,
                    maxInc                 = self.maxInc1,
                    damping_factor         = self.damping_factor1,
                    adaptiveDampingRatio   = self.adaptiveDampingRatio,)
    else:
        if self.separate_load_steps == True:
            self.step1Name = 'PLoad_Step'
            self.step2Name = 'Axial_Displ_Step'
            # creating perturbation load step
            static_step(model                  = mod,
                        name                   = self.step1Name,
                        previous               = 'Initial',
                        damping                = self.artificial_damping1,
                        initialInc             = self.initialInc1,
                        maxNumInc              = self.maxNumInc1,
                        minInc                 = self.minInc1,
                        maxInc                 = self.maxInc1,
                        damping_factor         = self.damping_factor1,
                        adaptiveDampingRatio   = self.adaptiveDampingRatio,)
            # creating axial load step
            if self.axial_include:
                static_step(
                    model                  = mod,
                    name                   = self.step2Name,
                    previous               = 'PLoad_Step',
                    damping                = self.artificial_damping2,
                    initialInc             = self.initialInc2,
                    maxNumInc              = self.maxNumInc2,
                    minInc                 = self.minInc2,
                    maxInc                 = self.maxInc2,
                    damping_factor         = self.damping_factor2,
                    adaptiveDampingRatio   = self.adaptiveDampingRatio,)
            else:
                self.step2Name = self.step1Name
        else:
            self.step1Name = 'PLoad_Axial_Displ_Step'
            self.step2Name = self.step1Name
            # creating perturbation load and axial displacement at same step
            static_step(model                  = mod,
                        name                   = self.step2Name,
                        previous               = 'Initial',
                        damping                = self.artificial_damping2,
                        maxNumInc              = self.maxNumInc2,
                        initialInc             = self.initialInc2,
                        minInc                 = self.minInc2,
                        maxInc                 = self.maxInc2,
                        damping_factor         = self.damping_factor2,
                        adaptiveDampingRatio   = self.adaptiveDampingRatio,)

    # applying boundary conditions
    AXIALDISPL = self.axial_displ # mm
    #bot boundary conditions
    botU1 = set_unset(self.botU1)
    botU2 = set_unset(self.botU2)
    botU3 = set_unset(self.botU3)
    botUR1 = set_unset(self.botUR1)
    botUR2 = set_unset(self.botUR2)
    botUR3 = set_unset(self.botUR3)
    topU1 = set_unset(self.topU1)
    topU2 = set_unset(self.topU2)
    topU3 = set_unset(self.topU3)
    topUR1 = set_unset(self.topUR1)
    topUR2 = set_unset(self.topUR2)
    topUR3 = set_unset(self.topUR3)
    mpc_top = PIN_MPC
    if self.topUR1 and self.topUR2 and self.topUR3:
        mpc_top = TIE_MPC
    inst_local_csys_datum = inst.datums[ self.local_csys.id ]
    displacementBC(model          = mod,
                   name           = 'BC_bot',
                   createStepName = 'Initial',
                   region         = self.cross_sections[0].inst_edges,
                   u1  = botU1 , u2  = botU2 , u3  = botU3 ,
                   ur1 = botUR1, ur2 = botUR2, ur3 = botUR3,
                   localCsys      = inst_local_csys_datum)
    if self.axial_include and self.linear_buckling == False:
        displacementBC(
                model = mod,
                name  = 'Axial_Displ',
                createStepName = self.step2Name,
                region = Region(referencePoints = (self.rp_top,)),
                u1  = UNSET, u2  = UNSET, u3  = -AXIALDISPL,
                ur1 = UNSET, ur2 = UNSET, ur3 =       UNSET,
                localCsys = inst_local_csys_datum)
    # meshing the part
    part.generateMesh()

    # creating job
    mdb = __main__.mdb
    job = mdb.Job(name    = self.jobname,
                  model   = mod,
                  scratch = r'c:\Temp\abaqus\scratch',
                  memory  = 4,
                  memoryUnits = GIGA_BYTES,
                  #numCpus = 6,
                 )
    self.job = job

    # reading and mapping nodes
    _read_and_map._read_and_map_nodes(self)
    #
    # creating tm_nodes (test machine nodes) used to input load asymmetry
    if abs(self.betarad) > 1.e-9 and self.linear_buckling == False:
        displacementBC(
                model          = mod,
                name           = 'BC_top_TM',
                createStepName = 'Initial',
                region         = Region(referencePoints = (self.rp_top,)),
                u1  = SET , u2 = SET , u3 = UNSET ,
                ur1 = SET, ur2 = SET, ur3 = SET,
                localCsys      = inst_local_csys_datum)
        displacementBC(
                model          = mod,
                name           = 'BC_top',
                createStepName = 'Initial',
                region         = self.cross_sections[-1].inst_edges,
                u1  = topU1 , u2  = topU2 , u3  = topU3 ,
                ur1 = topUR1, ur2 = topUR2, ur3 = topUR3,
                localCsys      = inst_local_csys_datum)
        nodesTM = []
        omegarad = self.omegarad
        betarad = self.betarad
        for node in self.cross_sections[-1].nodes:
            thetarad = np.deg2rad(node.theta)
            clearance = self.r2*np.tan(betarad)*(1 - np.cos(thetarad-omegarad))
            newNode = geom.Node()
            newNode.x = node.x
            newNode.y = node.y
            newNode.z = node.z + clearance
            newNode.clearance = clearance
            rp = assembly.ReferencePoint(point = (newNode.x,
                                                  newNode.y,
                                                  newNode.z))
            newNode.obj = rp
            newNode.ref_id = node.id
            newNode.id = int(rp.name.split('-')[1])
            nodesTM.append(newNode)
        #
        rps = assembly.referencePoints
        rp_ids = [ n.obj.id for n in nodesTM ]
        rps_TM = tuple([rps[rp_id] for rp_id in rp_ids])
        mod.MultipointConstraint(
            name         = 'MPC_rp',
            controlPoint = Region(referencePoints = (self.rp_top,)),
            surface      = Region(referencePoints = rps_TM),
            mpcType      = mpc_top,
            userMode     = DOF_MODE_MPC,
            userType     = 0,
            csys         = inst_local_csys_datum)
        # editing "Keyowords" to include the imperfection file
        text  = '** -----------------------------------------------------------'
        text += '\n**'
        for n in nodesTM:
            text += '\n*Element, type=GAPUNI, elset=gap_{0:06d}'.format(n.id)
            text += '\n{0:d},{1:d},InstanceCylinder.{2:d}'.format(
                     (10000000+n.id), n.id, n.ref_id)
            text += '\n*GAP, elset=gap_{0:06d}'.format(n.id)
            text += '\n{0:f},0,0,-1\n'.format(n.clearance)
        with open('include_LA_gaps.inp', 'w') as f:
            f.write(text)
        pattern = '*Instance'
        text = '*INCLUDE, INPUT=include_LA_gaps.inp'
        edit_keywords(model=mod, text=text, before_pattern=pattern)
    else:
        if self.analytical_model:
            displacementBC(
                    model          = mod,
                    name           = 'BC_top_TM',
                    createStepName = 'Initial',
                    region         = self.cross_sections[-1].inst_edges,
                    u1  = topU1 , u2  = topU2 , u3  = topU3 ,
                    ur1 = topUR1, ur2 = topUR2, ur3 = topUR3,
                    localCsys      = inst_local_csys_datum)
        else:
            displacementBC(
                    model          = mod,
                    name           = 'BC_top_TM',
                    createStepName = 'Initial',
                    region         = Region(referencePoints=(self.rp_top,)),
                    u1  = topU1 , u2  = topU2 , u3  = topU3 ,
                    ur1 = topUR1, ur2 = topUR2, ur3 = topUR3,
                    localCsys      = inst_local_csys_datum)
            mod.MultipointConstraint(
                name         = 'MPC_rp',
                controlPoint = Region(referencePoints = (self.rp_top,)),
                surface      = self.cross_sections[-1].inst_edges,
                mpcType      = mpc_top,
                userMode     = DOF_MODE_MPC,
                userType     = 0,
                csys         = inst_local_csys_datum)

    if self.linear_buckling == False:
        # creating sets (will be used in the output recovery)
        part.Set(name='ALL_NODES', nodes=part.nodes)
        for entity in self.cross_sections + self.meridians:
            nodes = []
            for node in entity.nodes:
                if node == None:
                    continue
                nodes.append(node.obj)
            if not nodes:
                continue
            mesh_node_array = mesh.MeshNodeArray(nodes=nodes)
            name = '{0:s}_{1:03d}'.format(entity.prefix, entity.index)
            part.Set(name=name, nodes=mesh_node_array)
        assembly.Set(referencePoints = (self.rp_top,),
                      name = 'Set_rp_top')
        for imp in self.impconf.imperfections:
            assembly.Set(vertices = imp.vertice,
                         name     = 'Set_' + imp.name)
        # defining output requests
        mod.TimePoint(name='time_points_PLoad_Step',
                      points=((0.0, 1.0, 1.),),)
        time_incr = 1./self.time_points
        mod.TimePoint(name='time_points_Axial_Displ_Step',
                      points=((0.0, 1.0, time_incr),),)
        if self.rsm:
            self.output_requests = ['ENER']
        mod.FieldOutputRequest(
            name                = 'field_PLoad_Step',
            createStepName      = self.step1Name,
            variables           = self.output_requests,
            timePoint           = 'time_points_PLoad_Step',
            timeMarks           = OFF,
            sectionPoints       = DEFAULT,
            rebar               = EXCLUDE,)
        mod.FieldOutputRequest(
            name                = 'field_Axial_Displ_Step',
            createStepName      = self.step2Name,
            variables           = self.output_requests,
            timePoint           = 'time_points_Axial_Displ_Step',
            timeMarks           = OFF,
            sectionPoints       = DEFAULT,
            rebar               = EXCLUDE,)
        del mod.fieldOutputRequests['F-Output-1']
        tmp_set = assembly.sets['Set_rp_top']
        mod.HistoryOutputRequest(
            name           = 'hist_rp_top',
            createStepName = self.step1Name,
            variables      = ('U3','RF3'),
            region         = tmp_set,
            sectionPoints  = DEFAULT,
            rebar          = EXCLUDE,)
        for imp in self.impconf.imperfections:
            tmp_set = assembly.sets['Set_' + imp.name]
            mod.HistoryOutputRequest(
                name           = 'hist_' + imp.name,
                createStepName = self.step1Name,
                variables      = ('U1','U2','U3'),
                region         = tmp_set,
                sectionPoints  = DEFAULT,
                rebar          = EXCLUDE,)

        if self.request_stress_output:
            print 'WARNING - stress outputs requested - this may create huge .odb files'
            mod.FieldOutputRequest(
                name                = 'field_ALL_NODES_stress',
                createStepName      = self.step2Name,
                variables           = ('S', 'HSNFTCRT', 'HSNFCCRT',
                                            'HSNMTCRT', 'HSNMCCRT'),
                layupNames          = ('InstanceCylinder.CompositePlate',),
                timePoint           = 'time_points_Axial_Displ_Step',
                timeMarks           = OFF,
                layupLocationMethod = ALL_LOCATIONS,
                rebar               = EXCLUDE,)

        # applying imperfections

        icount = 0
        for pload in self.impconf.ploads:
            if pload.pltotal < TOL:
                print 'WARNING - pload less than TOL, will be ignored'
                continue
            icount += 1
            # creating the perturbation loads
            mod.ConcentratedForce(name='PLoad_' + str(icount),
                                  createStepName = self.step1Name,
                                  region= Region(vertices = pload.vertice),
                                  cf1 = pload.plx,
                                  cf2 = pload.ply,
                                  cf3 = pload.plz,)

        for single_dimple in self.impconf.dimples:
            single_dimple.create()

        for axisymmetric in self.impconf.axisymmetrics:
            axisymmetric.create()

        if len(self.impconf.lbmis) > 0:
            text  = '** -------------------------------------------------------'
            lb_name = self.study.name + '_lb'
            text += '\n*IMPERFECTION, STEP=1, FILE={0}'.format(lb_name)
            for imp in self.impconf.lbmis:
                # editing "keywords" to include the imperfection file
                text += '\n{0:d}, {1:f}'.format(int(imp.mode),
                                      float(imp.scaling_factor))
            text += '\n**'
            pattern = '*Step'
            edit_keywords(model=mod, text=text, before_pattern=pattern)
    else: #linear_buckling == True
        if self.pressure_include:
                #a = mod.rootAssembly
                #s1 = inst.faces
                #side2Faces1 = s1.getSequenceFromMask(mask=('[#3 ]',),)
                mod.Pressure(name = 'Pressure',
                             createStepName = self.step2Name,
                             region = Region(side2Faces = inst.faces),
                             distributionType = UNIFORM,
                             field = '',
                             magnitude = self.pressure_value,
                             amplitude = UNSET)
        elif self.analytical_model:
            region = self.cross_sections[-1].inst_edges
            mod.ShellEdgeLoad(name='Distributed unitary Nxx',
                createStepName = 'Linear_Buckling_Step',
                region = region,
                magnitude = 1.0,
                distributionType = UNIFORM,
                field='',
                localCsys = inst_local_csys_datum,
                resultant = ON)

        else:
            region = Region(referencePoints = (self.rp_top,))
            mod.ConcentratedForce(name = 'axial_unitary_load',
                                  createStepName = self.step1Name,
                                  region = region,
                                  cf1 =   0.,
                                  cf2 =   0.,
                                  cf3 = -1.0,
                                  distributionType = UNIFORM,
                                  field = '',
                                  localCsys = inst_local_csys_datum)

        # printing buckling modes to a .fil file
        text  = '** -----------------------------------------------------------'
        text += '\n**'
        text += '\n*NODE FILE'
        text += '\nU,'
        text += '\n*MODAL FILE'
        edit_keywords(model=mod, text=text, before_pattern=None)

    if self.rsm:
        # reduced stiffness method, reference Sosa el al. 2006
        self.lam.ABD[0:3,0:3] *= 1./self.rsm_reduction_factor
        self.lam.A *= 1./self.rsm_reduction_factor
        if True:
            self.lam.ABD[0:3,3:6] = 0
            self.lam.ABD[3:6,0:3] = 0
            self.lam.B = np.zeros((3,3),
                                       dtype=self.lam.B.dtype)
        if False:
            self.lam.ABD[0:3,3:6] *= 1./self.rsm_reduction_factor
            self.lam.ABD[3:6,0:3] *= 1./self.rsm_reduction_factor
            self.lam.B *= 1./self.rsm_reduction_factor

    if self.direct_ABD_input:
        text  = '*ELSET,elset=all_elements,generate\n'
        text += '1,1000000,1\n'
        text += '*Orientation, name=Ori-ABD, system=CYLINDRICAL\n'
        text += '          0.,           0.,           0.,           0.,           0.,           1.\n'
        text += '2, 0.\n'
        text += '*SHELL GENERAL SECTION,ELSET=all_elements,ORIENTATION=Ori-ABD\n'
        ABD = self.lam.ABD
        E   = self.lam.E
        ABDij = []
        for ccount in range(6):
            for lcount in range(ccount+1):
                ABDij.append(ABD[lcount][ccount])
        text += '%f,%f,%f,%f,%f,%f,%f,%f\n' % tuple(ABDij[  :8])
        text += '%f,%f,%f,%f,%f,%f,%f,%f\n' % tuple(ABDij[8:16])
        text += '%f,%f,%f,%f,%f\n'          % tuple(ABDij[16: ])
        text += '*TRANSVERSE SHEAR STIFFNESS\n'
        text += '%f,%f,%f\n' % (E[0][0],E[1][1],E[0][1])
        pattern = '*Node'
        edit_keywords(model=mod, text=text, before_pattern=pattern, insert=True)

    if not self.linear_buckling:
        text  = '** -----------------------------------------------------------'
        text += '\n**'
        text += '\n*NODE PRINT, nset=Set_rp_top'
        text += '\nRF3,'
        edit_keywords(model=mod, text=text, before_pattern=None)

    if self.rsm:
        text  = '\n*AMPLITUDE, NAME=FMODAL, VALUE=RELATIVE, DEFINITION=TABULAR'
        text += '\n0.0, 0.0, 1.0, 0.001'
        text += '\n*INCLUDE, input=rsm_PD_mode_%02d.inp' % self.rsm_mode
        edit_keywords(model=mod, text=text, before_pattern=None)


    assembly.regenerate()
    s = __main__.session
    s.viewports[s.currentViewportName].setValues(displayedObject=assembly)
    self.created_model = True

