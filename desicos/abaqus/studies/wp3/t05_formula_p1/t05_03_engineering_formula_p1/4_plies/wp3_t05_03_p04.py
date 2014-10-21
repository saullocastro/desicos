import sys
import os
import inspect
source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
sys.path.append( source_python )
#
#cycle 00
#ploads  = [0.5,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.]
#cycle 01
ploads  = [0.2,0.4,0.6,0.8,1.,1.5,2.0,2.5,3.0,3.5]
studies = []
inspect.getfile(inspect.currentframe())
abspath = os.path.abspath(inspect.getfile(inspect.currentframe()))
execfile(os.path.join(os.path.dirname(abspath), 'ccs.py'))
from study import Study
from conecyl import ConeCyl
for ccname in sorted(ccs.keys()):
    cc_dict = ccs[ccname]
    study_name = 'wp3_t05_03_' + ccname
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
    std = Study()
    std.name = study_name
    std.rebuild()
    for pload in ploads:
        cc = ConeCyl()
        for k,v in cc_dict.items():
            setattr( cc, k, v )
        cc.damping_factor2 = 1.e-8
        cc.initialInc2 = 1.e-2
        cc.minInc2 = 1.e-6
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta   =   0.,
                              pt      =   0.5,
                              pltotal = pload )
        cc.numel_r    = 120.
        cc.elem_type  = 'S8R5'
        cc.axial_displ = 3.
        std.add_cc(cc)
    std.create_models()
    studies.append(std)
