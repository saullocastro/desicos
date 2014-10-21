#
study_name_prefix = 'wp2_astrium_03_less_4x0_plies_stress'
#
import numpy as np
#
meshes =  {\
          #'NUMEL_060': 60.,
          #'NUMEL_080': 80.,
          #'NUMEL_120': 120.,
          #'NUMEL_160': 160.,
          #'NUMEL_200': 200.,
          #'NUMEL_240': 240.,
          #'NUMEL_280': 280.,
          #'NUMEL_320': 320.,
          'NUMEL_360': 360.,
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
    #ploads = [ 0.,0.5,1.,4.,5.,8.,10.,12.,16.,20. ]
    ploads = [20.]
    pt = 0.5
    cname = 'astrium_3_less_4x0_plies_45_out'
    for pload in ploads:
        cc = std.add_cc_fromDB( cname )
        cc.request_stress_output = True
        cc.damping_factor2 = 4.e-7
        cc.output_requests = ('U', 'NFORC')
        cc.numel_r = numel_r
        cc.meshname = meshname
        cc.impconf.ploads = []
        cc.impconf.add_pload(
            theta=  0.,
            pt = pt,
            pltotal = pload )
        cc.axial_displ = 1.0
        cc.rebuild()
        cc.time_points = 40
    std.create_models(read_outputs=True)
    studies[ std.name ] = std
