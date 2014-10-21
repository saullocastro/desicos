import sys
import os
import numpy

source_python = r'C:\clones\desicos\desicos\abaqus'
sys.path.append( source_python )
import study

study_name = 'wp3_t02_03_shims'
###########################################
########  FILE MANAGEMENT SECTION  ########
###########################################
study_dir  = os.path.join( r'C:\Temp','abaqus',study_name )
if not os.path.isdir( study_dir ):
    os.makedirs( study_dir )
output_dir = os.path.join( study_dir,'outputs' )
print 'configuring folders...'
print '\t' + output_dir
if not os.path.isdir( output_dir ):
    os.makedirs( output_dir )
###########################################
std = study.Study()
std.name = study_name
std.rebuild()
count = 0
count += 1
cc = std.add_cc_fromDB('zimmermann_1992_z33')
cc.separate_load_steps = True
cc.impconf.ploads = []
cc.impconf.add_shim(theta = 0.,
                    thick = 0.1,
                    omega = 5)
cc.damping_factor2 = 1.e-7
cc.initialInc2 = 1.e-2
cc.minInc2 = 1.e-6
cc.maxInc2 = 1.e-2
cc.maxNumInc2 = 100000
cc.axial_displ = 1.5

std.create_models()
