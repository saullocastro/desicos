import sys
import os
#
numel_r = 240
studies = {}
#
study_name = 'wp3_t03_04_rsm_z07'
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
rsm_alphas = [1., 2., 3., 5., 10., 100., 1000.]
for rsm_alpha in rsm_alphas:
    for mode in xrange(1,50,2):
        cc = std.add_cc_fromDB( cname )
        cc.impconf.ploads = []
        cc.rsm = True
        cc.rsm_reduction_factor = rsm_alpha
        cc.rsm_mode = mode
        cc.numel_r = numel_r
        cc.rebuild()

studies[study_name] = std
std.create_models(run_rsm=False)
#
#

