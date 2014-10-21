#
study_name_prefix = 'pocher_huehne2008_4e-7_adaptive_no'
#
import numpy as np
#
meshes =  {\
          'NUMEL_240': 240.,
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
    ploads = [ 0., 2., 4., 8., 10. ]
    pt = 0.5
    cname = 'huehne2008_z07'
    for pload in ploads:
        cc = std.add_cc_fromDB( cname )
        cc.separate_load_steps = True
        cc.artificial_damping1 = True
        cc.artificial_damping2 = True
        cc.damping_factor1 = 4.e-7
        cc.damping_factor2 = 4.e-7
        cc.numel_r = numel_r
        cc.meshname = meshname
        cc.impconf.ploads = []
        cc.impconf.add_pload(
            theta=  0.,
            pt = pt,
            pltotal = pload )
        cc.axial_displ = 1.
        cc.rebuild()
    std.create_models(read_outputs=True)
    studies[ std.name ] = std
