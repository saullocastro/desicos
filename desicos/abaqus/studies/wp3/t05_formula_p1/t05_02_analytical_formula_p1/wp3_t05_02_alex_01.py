import sys
import os
#
numel_r = 140
#
study_name = 'wp3_t05_02_alex_01'
###########################################
########  FILE MANAGEMENT SECTION  ########
###########################################
source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
sys.path.append( source_python )
study_dir  = os.path.join( r'C:\Temp','abaqus',study_name )
if not os.path.isdir( study_dir ):
    os.makedirs( study_dir )
output_dir = os.path.join( study_dir,'outputs' )
print 'configuring folders...'
print '\t' + output_dir
if not os.path.isdir( output_dir ):
    os.makedirs( output_dir )
###########################################
import study
import conecyl
std = study.Study()
std.name = study_name
std.rebuild()
rh = 0.25
rt = 1000
ploads = [0.5, 1., 2., 3., 4., 5., 7.5, 10., 15.]
for pload in ploads:
    cc = conecyl.ConeCyl()
    cc.stack = [0]
    cc.r = 400.
    cc.h    = cc.r / rh # 1600.
    cc.plyts = [cc.r / rt] # 0.4
    cc.axial_displ = 1.
    cc.laminaprop = (196500., 0.29, 273.15)
    cc.impconf.ploads = []
    cc.impconf.add_pload( theta   = 0. ,
                          pt      = 0.5,
                          pltotal = pload )
    cc.numel_r = numel_r
    cc.elem_type = 'S8R5'
    cc.minInc2 = 1.e-6
    cc.initialInc2 = 1.e-2
    cc.maxInc2 = 1.e-2
    cc.maxNumInc2 = 100000
    cc.damping_factor2 = 1.e-7
    #cc.axial_include = False
    cc.time_points = 40
    std.add_cc( cc )

std.create_models()
#

