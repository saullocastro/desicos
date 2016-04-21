import numpy as np

from abaqus import mdb, session
from abaqusConstants import *
from regionToolset import Region
import mesh
from cor_shell import *

from desicos.logger import warn
from desicos.abaqus import abaqus_functions
from desicos.abaqus.constants import NUM_LB_MODES

def create_frame (cc,mod):
    if cc.geo_w_F_RB==True: 
        geo_w_F=cc.geo_w_F
        if cc.geo_STR_CB==True and cc.geo_w_str_RB==True:
            STR_geo=cc.geo_w_str
            str_R=STR_geo[1]/2+STR_geo[2]/2  
        elif cc.geo_STR_CB==True and cc.geo_i_str_RB==True:
            STR_geo=cc.geo_I_str
            str_R=STR_geo[2]+STR_geo[5]/2 
        elif cc.geo_STR_CB==True and cc.geo_z_str_RB==True:
            STR_geo=cc.geo_Z_str
            str_R=STR_geo[2]+STR_geo[5]/2 
        else:
            str_R=0                

        s1 = mod.ConstrainedSketch(name='Sketch_frame', sheetSize=2*cc.rbot)
        s1.setPrimaryObject(option=STANDALONE)
        s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(cc.rbot-str_R, 0.0))
        s1.unsetPrimaryObject()
        s = mod.ConstrainedSketch(name='Sketch_frame_section', 
            sheetSize=2*cc.rbot, transform=(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -0.0, -1.0, -0.0, 
            cc.rbot-geo_w_F[0]/2-geo_w_F[2]/2-str_R, 0.0, 0.0))
        
        s.setPrimaryObject(option=SUPERIMPOSE)
        s.ConstructionLine(point1=(-cc.rbot, 0.0), point2=(cc.rbot, 0.0))
        s.ConstructionLine(point1=(0.0, cc.rbot), point2=(0.0, cc.rbot))

        delta_H=(cc.H-geo_w_F[1])/float((cc.F_NUM[0]-1))
        for i in range(0,cc.F_NUM[0]):   
            p1=(-geo_w_F[0]-geo_w_F[3]/2,geo_w_F[1]/2+i*delta_H)
            p2=(-geo_w_F[2]/2,geo_w_F[1]/2+i*delta_H)
            p3=(-geo_w_F[2]/2,geo_w_F[1]+i*delta_H)
            p4=(-geo_w_F[2]/2,i*delta_H)
            s.Line(point1=p1, point2=p2)
            s.Line(point1=p2, point2=p3)
            s.Line(point1=p2, point2=p4)

    if cc.geo_c_F_RB==True: 

        geo_c_F=cc.geo_c_F
        if cc.geo_STR_CB==True and cc.geo_w_str_RB==True:
            STR_geo=cc.geo_w_str
            str_R=STR_geo[1]/2+STR_geo[2]/2  
        elif cc.geo_STR_CB==True and cc.geo_i_str_RB==True:
            STR_geo=cc.geo_I_str
            str_R=STR_geo[2]+STR_geo[5]/2   
        elif cc.geo_STR_CB==True and cc.geo_z_str_RB==True:
            STR_geo=cc.geo_Z_str
            str_R=STR_geo[2]+STR_geo[5]/2   
        else:
            str_R=0

        s1 = mod.ConstrainedSketch(name='Sketch_frame', sheetSize=2*cc.rbot)
        s1.setPrimaryObject(option=STANDALONE)
        s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(cc.rbot-str_R, 0.0))
        s1.unsetPrimaryObject()
        s = mod.ConstrainedSketch(name='Sketch_frame_section', 
            sheetSize=2*cc.rbot, transform=(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -0.0, -1.0, -0.0, 
            cc.rbot-geo_c_F[0]/2-str_R, 0.0, 0.0))
        
        s.setPrimaryObject(option=SUPERIMPOSE)
        s.ConstructionLine(point1=(-cc.rbot, 0.0), point2=(cc.rbot, 0.0))
        s.ConstructionLine(point1=(0.0, cc.rbot), point2=(0.0, cc.rbot))

        delta_H=(cc.H-geo_c_F[1])/float((cc.F_NUM[0]-1))
        for i in range(0,cc.F_NUM[0]):   
            p1=(-geo_c_F[0],geo_c_F[1]+i*delta_H)
            p2=(-geo_c_F[2]/2,geo_c_F[1]+i*delta_H)
            p3=(-geo_c_F[2]/2,i*delta_H)
            p4=(-geo_c_F[0],i*delta_H)
            s.Line(point1=p1, point2=p2)
            s.Line(point1=p2, point2=p3)
            s.Line(point1=p3, point2=p4)

    if cc.geo_ort_RB==True:
        geo_ortho=cc.geo_ortho
        s1 = mod.ConstrainedSketch(name='Sketch_frame', sheetSize=2*cc.rbot)
        s1.setPrimaryObject(option=STANDALONE)
        s1.CircleByCenterPerimeter(center=(0.0, 0.0), point1=((cc.rbot), 0.0))
        s1.unsetPrimaryObject()
        s = mod.ConstrainedSketch(name='Sketch_frame_section', 
            sheetSize=2*cc.rbot, transform=(1.0, 0.0, 0.0, 0.0, 0.0, 1.0, -0.0, -1.0, -0.0, 
            cc.rbot-geo_ortho[2]/2, 0.0, 0.0))
        
        s.setPrimaryObject(option=SUPERIMPOSE)
        s.ConstructionLine(point1=(-cc.rbot/2, 0.0), point2=(cc.rbot/2, 0.0))
        s.ConstructionLine(point1=(0.0, cc.rbot/2), point2=(0.0, -cc.rbot/2))

        delta_H=(cc.H)/float((geo_ortho[1]-1))
        for i in range(0,geo_ortho[1]):   
            p1=(-geo_ortho[2],i*delta_H)
            p2=(0,i*delta_H)
            s.Line(point1=p1, point2=p2)


    p = mod.Part(name='Frames', dimensionality=THREE_D, 
        type=DEFORMABLE_BODY)
    p.BaseShellSweep(sketch=s, path=s1)
    s.unsetPrimaryObject()
    create_frame.frame=p