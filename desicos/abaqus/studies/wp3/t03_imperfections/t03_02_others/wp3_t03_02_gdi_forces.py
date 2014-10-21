import sys
import os
#
cname = 'huehne_2008_z07'
#
study_name = 'wp3_t03_02_gdi_forces'
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
dimples = {\
            1:[ 220, 250, 0.04],
            2:[ 220, 250, 0.08],
            3:[ 220, 250, 0.24],
            4:[ 220, 250, 0.40],
            5:[ 220, 250, 0.64],
            6:[ 220, 250, 0.72],
            7:[ 220, 250, 0.80],
            8:[ 220, 250, 1.32],
            9:[ 220, 250, 2.00],
           10:[ 220, 250, 2.64],
          }
for key, dimple in dimples.iteritems():
    cc = std.add_cc_fromDB( cname )
    cc.damping_factor2 = 1.e-7
    cc.initialInc2 = 1.e-2
    cc.minInc2 = 1.e-6
    cc.maxInc2 = 1.e-2
    cc.maxNumInc2 = 100000
    cc.impconf.ploads = []
    cc.impconf.add_dimple( 0., 0.5,\
                                  dimple[0], dimple[1], dimple[2] )
    cc.numel_r    = 120
    cc.elem_type  = 'S8R5'
    cc.axial_displ= 0.46
    cc.create_model()
    cc.request_force_output = True
    cc.time_points = 80
    cc.write_job()
std.create_run_file()
