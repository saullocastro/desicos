import sys
import os
#
numel_r = 128
studies = {}
#
study_name = 'wp3_t03_04_rsm_sosa'
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
cname = 'sosa_2006_steel'
rsm_alphas = [1.,2.,3.,4.,5., 10., 100., 1000., 10000.]
mode = 1
for rsm_alpha in rsm_alphas:
    cc = std.add_cc_fromDB( cname )
    cc.impconf.ploads = []
    cc.rsm = True
    cc.rsm_reduction_factor = rsm_alpha
    cc.pressure_include = True
    cc.rsm_mode = mode
    cc.numel_r = numel_r
    cc.botU1 = True
    cc.botU2 = True
    cc.botU3 = True
    cc.botUR1 = True
    cc.botUR2 = True
    cc.botUR3 = True
    cc.topU1 = False
    cc.topU2 = False
    cc.topU3 = False
    cc.topUR1 = False
    cc.topUR2 = False
    cc.topUR3 = False
    cc.rebuild()


studies[study_name] = std
std.create_models(run_rsm=True)
#
#

