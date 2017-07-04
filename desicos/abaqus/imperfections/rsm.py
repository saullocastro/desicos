from __future__ import absolute_import

import os

import numpy as np
from abaqusConstants import *

from desicos.abaqus.constants import NUM_LB_MODES

def read_displacements(cc, mode):
    odb = cc.attach_results()
    u_dict  = {}
    ur_dict = {}
    frames = odb.steps[cc.step1Name].frames
    # only using the first engenmode
    frame = frames[mode]
    u_values = frame.fieldOutputs['U'].values
    ur_values = frame.fieldOutputs['UR'].values
    for u_value in u_values:
        u_dict[u_value.nodeLabel]   = u_value.data
    for ur_value in ur_values:
        ur_dict[ur_value.nodeLabel] = ur_value.data
    return u_dict, ur_dict

def create_prescribed_displacements(cc, mode=1):
    cc = cc.study.ccs[0]
    if cc.read_outputs():
        u, ur = read_displacements(cc, mode)
    else:
        cc.write_job(submit=True)
        if cc.read_outputs():
            u, ur = read_displacements(cc, mode)
        else:
            print 'ERROR - The linear buckling load outputs could not be read!'
            return False
    instance = cc.mod.rootAssembly.instances['InstanceCylinder']
    bot_top_nodes = [n.id for n in cc.cross_sections[0].nodes +\
                                   cc.cross_sections[-1].nodes]
    out = open(os.path.join(cc.output_dir,'rsm_PD_mode_%02d.inp' % mode),'w')
    out.write('*Boundary, type=displacement, amplitude=FMODAL\n')
    for n in cc.part.nodes:
        nid = int(n.label)
        if nid in bot_top_nodes:
            continue
        ut = np.concatenate( (u[nid],ur[nid]), axis=1 )
        #ut = u[nid]
        for dof, u_dof in enumerate(ut):
            out.write('InstanceCylinder.%d,%d,%d, %f\n' %\
                      (nid, dof+1, dof+1, u_dof))
    out.close()
    return True

def run_LB_read_PDs(std):
    for mode in range(1, NUM_LB_MODES+1):
        print 'RSM - reading buckling mode %02d' % mode
        create_prescribed_displacements(std.ccs[1], mode)
