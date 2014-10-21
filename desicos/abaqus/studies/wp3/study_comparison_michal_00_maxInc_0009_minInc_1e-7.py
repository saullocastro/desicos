#
study_name_prefix = 'study_comparison_michal_00_maxInc0009_minInc_1e-7'
#
import numpy as np
#
meshes =  {\
          #'NUMEL_160': 160.,
          'NUMEL_180': 180.,
          #'NUMEL_240': 240.,
          #'NUMEL_320': 320.,
         }
studies = {}
for meshname, numel_r in meshes.iteritems():
    study_name = study_name_prefix + '_' + meshname
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
    from study import Study
    std = Study()
    std.name = study_name
    std.rebuild()
    ploads = [ 0.,1.,2.,3.,4.,5.,6.,7.,8.,9.,10.]
    pt = 0.5
    cname = 'michal_cone'
    for pload in ploads:
        cc = std.add_cc_fromDB( cname )
        cc.separate_load_steps = True
        cc.artificial_damping = True
        cc.maxInc = 0.009
        cc.minInc = 1.e-7
        cc.maxNumInc = 100000
        cc.numel_r = numel_r
        cc.meshname = meshname
        cc.impconf.ploads = []
        cc.impconf.add_pload(
            theta=  0.,
            pt = pt,
            pltotal = pload )
        cc.axial_displ = 10.
        cc.rebuild()
    std.create_models(read_outputs=True)
    studies[ std.name ] = std
