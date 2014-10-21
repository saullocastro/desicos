#
study_name = 'study_PL_buckle_diameter_damping'
#
import numpy as np
#
source_python = r'\\MA-CASTRO\abaqus-conecyl-python'
import sys
import os
study_dir  = os.path.join( r'C:\Temp','abaqus',study_name )
if not os.path.isdir( study_dir ):
    os.makedirs( study_dir )
python_dir = os.path.join( study_dir, 'abaqus-conecyl-python' )
output_dir = os.path.join( study_dir,'outputs' )
print 'configuring folders...'
print '\t' + python_dir
print '\t' + output_dir
if not os.path.isdir( output_dir ):
    os.makedirs( output_dir )
if not os.path.isdir( python_dir ):
    os.makedirs( python_dir )
os.system('copy ' + source_python + ' ' + python_dir + '')
sys.path.append( python_dir )
#
import study
study = reload( study )
std = study.Study()
std.name = study_name
std.rebuild()
cname = 'r_100_h_200'
ploads = [2.,6.,10.,12.,16.,20.,24.,28.,32.]
#ploads = [2.,4.]
for pload in ploads:
    cc = std.add_cc_fromDB( cname )
    cc.impconf.ploads = []
    cc.impconf.add_pload( theta=  0.,
                            pt = 0.5,
                            pltotal = pload )
    cc.numel_r = 80.
    cc.axial_displ = 10.
    cc.separate_load_steps = True
    cc.axial_include = False
    cc.meshname = 'NO_AXIAL'
    cc.artificial_dumping = True
    cc.rebuild()
    cc.create_model()
    if not cc.check_completed():
        cc.write_job( submit = False )
    cc.read_outputs( )
#    cc.plot_displacements( step_num = 1 )
#    cc.plot_displacements( step_num = 2 )
#    cc.plot_forces( step_num = 1 )
    cc.plot_forces( step_num = 2 )
std.plot( step_num = 1,
          only_PL = False,
          cir_criterion = 'zero_radial_displ',
          cir_threshold = 0.0125 )
