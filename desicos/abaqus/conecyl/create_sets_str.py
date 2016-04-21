import numpy as np

from abaqus import *
from abaqusConstants import *
from regionToolset import Region
import mesh
from cor_shell import *

from desicos.logger import warn
from desicos.abaqus import abaqus_functions
from desicos.abaqus.constants import NUM_LB_MODES


def create_sets_str (part_shell,cc):

    shell_faces=[]
    str_faces=[]
    str_faces_1=[]
    str_faces_2=[]
    str_faces_3=[]
#    frames_faces=[]
    short_EDG=[]
    delta_alpha=2*np.pi/float(cc.str_NUM[0])

    if cc.geo_w_str_RB==True:

        str_delta_A=cc.geo_w_str[0]/(2*float(cc.rbot))
        h_str=cc.geo_w_str[1]
        for ii in range(0,cc.str_NUM[0]):
            shell_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+delta_alpha/float(2)),
            cc.rbot*np.sin(delta_alpha*ii+delta_alpha/2),cc.H/float(2)),),))

            str_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+str_delta_A/float(2)),
            cc.rbot*np.sin(delta_alpha*ii+str_delta_A/2),cc.H/float(2)),),))

            str_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii-str_delta_A/float(2)),
            cc.rbot*np.sin(delta_alpha*ii-str_delta_A/2),cc.H/float(2)),),))

            str_faces_1.append(part_shell.faces.findAt((((cc.rbot-h_str)*np.cos(delta_alpha*ii),
            (cc.rbot-h_str)*np.sin(delta_alpha*ii),cc.H/float(2)),),))

            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii-str_delta_A/2),
                                                        (cc.rbot)*np.sin(delta_alpha*ii-str_delta_A/2),
                                                        cc.H),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii+str_delta_A/2),
                                                        (cc.rbot)*np.sin(delta_alpha*ii+str_delta_A/2),
                                                        cc.H),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                        (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                        cc.H),),))

            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii-str_delta_A/2),
                                                        (cc.rbot)*np.sin(delta_alpha*ii-str_delta_A/2),
                                                        0.0),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii+str_delta_A/2),
                                                        (cc.rbot)*np.sin(delta_alpha*ii+str_delta_A/2),
                                                        0.0),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                        (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                        0.0),),))

        create_sets_str.set_shell_faces=shell_faces
        create_sets_str.set_str_faces=str_faces
        create_sets_str.set_str_faces_1=str_faces_1
        create_sets_str.set_short_EDG=short_EDG

    elif cc.geo_i_str_RB==True:

        str_delta_A=cc.geo_I_str[0]/(2*float(cc.rbot))
        str_delta_A_head=cc.geo_I_str[1]/(float(cc.rbot)-float(cc.geo_I_str[2]))
        str_delta_A_head_test=2*np.arctan(((float(cc.geo_I_str[1])/2))/(cc.rbot-cc.geo_I_str[2]))

        alpha_str=np.arctan(float(cc.geo_I_str[1])/(4*(cc.rbot-cc.geo_I_str[2])))

        h_str=cc.geo_I_str[2]

        for ii in range(0,cc.str_NUM[0]):
            shell_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+delta_alpha/float(2)),
            cc.rbot*np.sin(delta_alpha*ii+delta_alpha/2),cc.H/float(2)),),))

            str_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+str_delta_A/float(2)),
            cc.rbot*np.sin(delta_alpha*ii+str_delta_A/2),cc.H/float(2)),),))

            str_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii-str_delta_A/float(2)),
                                                       cc.rbot*np.sin(delta_alpha*ii-str_delta_A/2),
                                                       cc.H/float(2)),),))

            str_faces_1.append(part_shell.faces.findAt((((cc.rbot-h_str/(float(2)))*np.cos(delta_alpha*ii),
                                                         (cc.rbot-h_str/(float(2)))*np.sin(delta_alpha*ii),
                                                          cc.H/float(2)),),))

            str_faces_2.append(part_shell.faces.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+alpha_str),
                                                         ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+alpha_str),
                                                           cc.H/float(2)),),))            

            str_faces_2.append(part_shell.faces.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii-alpha_str),
                                                         ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii-alpha_str),
                                                           cc.H/float(2)),),))  

            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii-str_delta_A/2),
                                                       (cc.rbot)*np.sin(delta_alpha*ii-str_delta_A/2),
                                                        cc.H),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii+str_delta_A/2),
                                                       (cc.rbot)*np.sin(delta_alpha*ii+str_delta_A/2),
                                                        cc.H),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                       (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                        cc.H),),))

            short_EDG.append(part_shell.edges.findAt(((((np.cos(str_delta_A_head/float(4)))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+str_delta_A_head/float(4)),
                                                       ((np.cos(str_delta_A_head/float(4)))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+str_delta_A_head/float(4)),
                                                         cc.H),),))

            short_EDG.append(part_shell.edges.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+alpha_str),
                                                       ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+alpha_str),
                                                         cc.H),),)) 
            short_EDG.append(part_shell.edges.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii-alpha_str),
                                                       ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii-alpha_str),
                                                         cc.H),),))

            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii-str_delta_A/2),
                                                        (cc.rbot)*np.sin(delta_alpha*ii-str_delta_A/2),
                                                        0.0),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii+str_delta_A/2),
                                                       (cc.rbot)*np.sin(delta_alpha*ii+str_delta_A/2),
                                                        0.0),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                       (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                        0.0),),))

            short_EDG.append(part_shell.edges.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+alpha_str),
                                                       ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+alpha_str),
                                                         0.0),),))
            short_EDG.append(part_shell.edges.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii-alpha_str),
                                                       ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii-alpha_str),
                                                         0.0),),))

        create_sets_str.set_shell_faces=shell_faces
        create_sets_str.set_str_faces=str_faces
        create_sets_str.set_str_faces_1=str_faces_1
        create_sets_str.set_str_faces_2=str_faces_2
        create_sets_str.set_short_EDG=short_EDG

    elif cc.geo_z_str_RB==True:
        str_delta_A_head=cc.geo_Z_str[1]/(2*(float(cc.rbot)-cc.geo_Z_str[2]))
        str_delta_A=cc.geo_Z_str[0]/float(cc.rbot)
        h_str=cc.geo_Z_str[2]

        alpha_str=np.arctan(float(cc.geo_Z_str[1])/(2*(cc.rbot-cc.geo_Z_str[2])))

        for ii in range(0,cc.str_NUM[0]):
            shell_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+delta_alpha/float(2)),
                                                         cc.rbot*np.sin(delta_alpha*ii+delta_alpha/2),
                                                         cc.H/float(2)),),))

            str_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii+str_delta_A/float(4)),
                                                       cc.rbot*np.sin(delta_alpha*ii+str_delta_A/float(4)),
                                                       cc.H/float(2)),),))

            str_faces.append(part_shell.faces.findAt(((cc.rbot*np.cos(delta_alpha*ii-str_delta_A/float(4)),
                                                       cc.rbot*np.sin(delta_alpha*ii-str_delta_A/float(4)),
                                                       cc.H/float(2)),),))

            str_faces_1.append(part_shell.faces.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                         (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                          cc.H/float(2)),),))

            str_faces_2.append(part_shell.faces.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+alpha_str),
                                                         ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+alpha_str),
                                                           cc.H/float(2)),),)) 

            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii-str_delta_A/4),
                                                       (cc.rbot)*np.sin(delta_alpha*ii-str_delta_A/4),
                                                        cc.H),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii+str_delta_A/4),
                                                       (cc.rbot)*np.sin(delta_alpha*ii+str_delta_A/4),
                                                        cc.H),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                       (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                        cc.H),),))

            short_EDG.append(part_shell.edges.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+alpha_str),
                                                       ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+alpha_str),
                                                         cc.H),),))

            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii-str_delta_A/4),
                                                       (cc.rbot)*np.sin(delta_alpha*ii-str_delta_A/4),
                                                        0.0),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot)*np.cos(delta_alpha*ii+str_delta_A/4),
                                                       (cc.rbot)*np.sin(delta_alpha*ii+str_delta_A/4),
                                                        0.0),),))
            short_EDG.append(part_shell.edges.findAt((((cc.rbot-h_str/float(2))*np.cos(delta_alpha*ii),
                                                        (cc.rbot-h_str/float(2))*np.sin(delta_alpha*ii),
                                                        0.0),),))

            short_EDG.append(part_shell.edges.findAt(((((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.cos(delta_alpha*ii+alpha_str),
                                                       ((np.cos(alpha_str))**-1)*(cc.rbot-h_str)*np.sin(delta_alpha*ii+alpha_str),
                                                         0.0),),))

        create_sets_str.set_shell_faces=shell_faces
        create_sets_str.set_str_faces=str_faces
        create_sets_str.set_str_faces_1=str_faces_1
        create_sets_str.set_str_faces_2=str_faces_2
        create_sets_str.set_short_EDG=short_EDG
