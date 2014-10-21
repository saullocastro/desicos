#
study_name_prefix = 'wp2_astrium_03_7b_original_mrs'
#
import numpy as np
#
meshes =  {\
          'NUMEL_080': 080.,
          'NUMEL_100': 100.,
          'NUMEL_120': 120.,
          'NUMEL_140': 140.,
          'NUMEL_160': 160.,
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
    if os.path.isdir( python_dir ):
        os.system('rmdir /s /q ' + python_dir)
    os.makedirs( python_dir )
    os.system('xcopy /s ' + source_python + ' ' + python_dir + '')
    sys.path.append( python_dir )
    #
    import study
    study = reload( study )
    from study import Study
    std = Study()
    std.name = study_name
    std.rebuild()
    ploads = [ 0.,2.,4.,6.,8.,10.,20. ]
    ploads = [ 20. ]
    pt = 0.5
    cname = 'astrium_3_7b_original'
    for pload in ploads:
        cc = std.add_cc_fromDB( cname )
        cc.request_stress_output = True
        cc.numel_r = numel_r
        cc.meshname = meshname
        cc.impconf.ploads = []
        cc.impconf.add_pload(
            theta=  0.,
            pt = pt,
            pltotal = pload )
        cc.minInc2 = 1.e-6
        cc.initialInc2 = 1.e-3
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.damping_factor2 = 4.e-7
        cc.axial_displ = 1.
        cc.elem_type = 'S8R5'
    std.create_models(read_outputs=True)
    studies[ std.name ] = std
