import numpy
import sys
source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
sys.path.append( source_python )
import os
#
from conecylDB import imperfection_amplitudes
numel_r = 120
studies = {}
#

imp_name = 'degenhardt_2010_z23'
amp_thick_ratios = numpy.array([0.1,0.25,0.5,1.,1.5,2.,3.,4.,5.,6.])
amplitude = imperfection_amplitudes[imp_name]
lamt = 0.5
scaling_factors = amp_thick_ratios * lamt / amplitude
study_name = 'wp3_t03_02_msi_z07_z23'
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
cname = 'huehne_2008_z07'
for i, scaling_factor in enumerate(scaling_factors):
    cc = std.add_cc_fromDB( cname )
    cc.impconf.ploads = []
    cc.impconf.add_msi(imp_name, scaling_factor)
    # the line below is only necessary to quickly post-process without
    # the need to create again the imperfections
    cc.impconf.msis[0].amplitude = scaling_factor * amplitude
    cc.numel_r = numel_r
    cc.elem_type = 'S8R5'
    cc.axial_displ = 0.5
    cc.minInc2 = 1.e-6
    cc.initialInc2 = 1.e-2
    cc.maxInc2 = 1.e-2
    cc.maxNumInc2 = 100000
    cc.damping_factor2 = 5.e-7
    if i > 5: # models 07, 08, 09, 10 ...
        cc.damping_factor2 = 1.e-7
    cc.time_points = 80

studies[study_name] = std
#
std.create_models( apply_msis=False, apply_tis=False )
#
