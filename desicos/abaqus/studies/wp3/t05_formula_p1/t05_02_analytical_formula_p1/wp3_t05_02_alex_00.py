import sys
import os
#
numel_r = 140
#
study_name = 'wp3_t05_02_alex_00'
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
rhs = [1., 0.5, 0.25]
rts = [100, 250, 500, 1000]
ploads = {\
           100:{1.: 750., 0.5: 500., 0.25: 300.},
           250:{1.:  75., 0.5:  50., 0.25:  40.},
           500:{1.:  10., 0.5:  7.5, 0.25:   5.},
          1000:{1.:   1., 0.5: 0.75, 0.25:  0.5},
         }
axial_displs = {\
           100:{1.:   5., 0.5:   5., 0.25:  10.},
           250:{1.:   5., 0.5:   5., 0.25:   5.},
           500:{1.:   5., 0.5:   5., 0.25:   5.},
          1000:{1.:   5., 0.5:   5., 0.25:   5.},
         }
for rh in rhs:
    for rt in rts:
        for linear_buckling in [False, True]:
            cc = conecyl.ConeCyl()
            cc.linear_buckling = linear_buckling
            cc.stack = [0]
            cc.r = 400.
            cc.h     = cc.r / rh
            cc.plyts = [cc.r / rt]
            cc.laminaprop = (196500., 0.29, 273.15)
            cc.impconf.ploads = []
            pload = ploads[rt][rh]
            cc.impconf.add_pload( theta   = 0. ,
                                  pt      = 0.5,
                                  pltotal = pload )
            cc.numel_r = numel_r
            cc.elem_type = 'S8R5'
            cc.axial_displ = axial_displs[rt][rh]
            cc.minInc2 = 1.e-6
            cc.initialInc2 = 1.e-2
            cc.maxInc2 = 1.e-2
            cc.maxNumInc2 = 100000
            cc.damping_factor2 = 1.e-7
            #cc.axial_include = False
            cc.time_points = 2

            std.add_cc( cc )

std.create_models()
#

