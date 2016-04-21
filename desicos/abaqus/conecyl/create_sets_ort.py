import numpy as np

from abaqus import *
from abaqusConstants import *
from regionToolset import Region
import mesh
from cor_shell import *

from desicos.logger import warn
from desicos.abaqus import abaqus_functions
from desicos.abaqus.constants import NUM_LB_MODES


def create_sets_ort (part_shell,cc):

    shell_faces=[]
    str_faces=[]
    frames_faces=[]
    short_EDG=[]
    delta_alpha=2*np.pi/float(cc.geo_ortho[0])
    delta_H=cc.H/float((cc.geo_ortho[1]-1))
    for i in range(0,cc.geo_ortho[1]-1):
        for ii in range(0,cc.geo_ortho[0]):

            shell_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+delta_alpha/float(2)),
            cc.rbot*np.sin(delta_alpha*ii+delta_alpha/2),delta_H*i+delta_H/float(2)),),))
            str_faces.append(part_shell.faces.findAt((((cc.rbot-cc.geo_ortho[2]/float(2))*np.cos(delta_alpha*ii),
            (cc.rbot-cc.geo_ortho[2]/float(2))*np.sin(delta_alpha*ii),delta_H*i+delta_H/float(2)),),))
            frames_faces.append(part_shell.faces.findAt((((cc.rbot-cc.geo_ortho[2]/float(2))*np.cos(delta_alpha*ii+delta_alpha/float(2)),
            (cc.rbot-cc.geo_ortho[2]/float(2))*np.sin(delta_alpha*ii+delta_alpha/float(2)),delta_H*i+delta_H),),))

            short_EDG.append(part_shell.edges.findAt((((cc.rbot-cc.geo_ortho[2]/float(2))*np.cos(delta_alpha*ii),
            (cc.rbot-cc.geo_ortho[2]/float(2))*np.sin(delta_alpha*ii),delta_H*i+delta_H),),))

            if i==0:
                frames_faces.append(part_shell.faces.findAt((((cc.rbot-cc.geo_ortho[2]/float(2))*np.cos(delta_alpha*ii+delta_alpha/float(2)),
                (cc.rbot-cc.geo_ortho[2]/float(2))*np.sin(delta_alpha*ii+delta_alpha/float(2)),delta_H*i),),))

                short_EDG.append(part_shell.edges.findAt((((cc.rbot-cc.geo_ortho[2]/float(2))*np.cos(delta_alpha*ii),
                (cc.rbot-cc.geo_ortho[2]/float(2))*np.sin(delta_alpha*ii),delta_H*i),),))
    
    create_sets_ort.ort_shell_faces_all=part_shell.faces
    create_sets_ort.ort_shell_faces=shell_faces
    create_sets_ort.ort_str_faces=str_faces
    create_sets_ort.ort_frames_faces=frames_faces
    create_sets_ort.ort_SEDG=short_EDG

