#
study_name_prefix = 'wp3_t04_02_zimmermann_z33_real_imp'
#
import numpy as np
#
meshes =  {\
          #'NUMEL_060':  60.,
          #'NUMEL_080':  80.,
          #'NUMEL_100': 100.,
          'NUMEL_120': 120.,
          #'NUMEL_140': 140.,
          #'NUMEL_160': 160.,
          #'NUMEL_180': 180.,
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
    factors = [ 0.5, 0.75, 1., 1.25, 1.5, 2. ]
    axial = 0.75
    cname = 'zimmermann_1992_z33'
    for factor in factors:
        cc = std.add_cc_fromDB( cname )
        cc.numel_r = numel_r
        cc.meshname = meshname
        cc.impconf.ploads = []
        cc.minInc2 = 1.e-6
        cc.initialInc2 = 1.e-2
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.damping_factor2 = 1.e-7
        cc.axial_displ = axial
        cc.separate_load_steps = False
        cc.elem_type = 'S8R5'
        cc.time_points = 1000
        cc.rename = False
        cc.jobname = 'real_imp_%03d' % int(100 * factor)

    std.create_models()
    from gui.gui_defaults import imps, H_measured
    from measured_imp_geom import disturb_my_model_ABAQUS_CAE
    for i, cc in enumerate(std.ccs):
        factor = factors[i]
        disturb_my_model_ABAQUS_CAE(
                 imperfection_file_name = imps['z33'],
                 model_name = cc.jobname,
                 part_name  = 'Cylinder',
                 H_model            = cc.h,
                 H_measured         = H_measured['z33'],
                 R_model            = cc.r,
                 cyl_coord_sys      = False,
                 theta_in_degrees   = True,
                 stretch_H          = False,
                 z_offset_1         = None,
                 scaling_factor     = factor,
                 r_TOL              = 1.,
                 num_closest_points = 5,
                 power_parameter    = 2.,
                 num_sec_z          = 25)

    for cc in std.ccs:
        cc.write_job()
    studies[ std.name ] = std
