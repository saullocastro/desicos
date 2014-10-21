import sys
import os
#
numel_r = 120
studies = {}
#
ploads = [1.,2.,3.,4.,5.,10.,15.,20.,30.]
study_name = 'wp3_t03_01_spli_d796'
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
study = reload( study )
std = study.Study()
std.name = study_name
std.rebuild()
cname = 'wp2_rtu_d796'
for pload in ploads:
    cc = std.add_cc_fromDB( cname )
    cc.impconf.ploads = []
    cc.impconf.add_pload( theta   =   0.,
                          pt      =   0.5,
                          pltotal = pload )
    cc.numel_r = numel_r
    cc.elem_type = 'S8R5'
    cc.axial_displ = 0.5
    cc.minInc2 = 1.e-6
    cc.initialInc2 = 1.e-2
    cc.maxInc2 = 1.e-2
    cc.maxNumInc2 = 100000
    cc.damping_factor2 = 5.e-7
    cc.request_force_output = True
    cc.time_points = 80

studies[study_name] = std
#
std.create_models()
#

