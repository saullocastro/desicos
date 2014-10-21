#
numel_r = 120
cname = 'huehne_2008_z07'
studies = []
study_names = [ 'imp_lb_%s_no_PL_mode_01'  % cname,
                'imp_lb_%s_no_PL_mode_03'  % cname,
                'imp_lb_%s_no_PL_mode_05'  % cname,
                #'imp_lb_%s_yes_PL_mode_01' % cname,
                #'imp_lb_%s_yes_PL_mode_02' % cname,
                #'imp_lb_%s_yes_PL_mode_03' % cname,
              ]
#
pload = 0.
factors = [ 0.015625,
            0.03125,
            0.0625,
            0.1250,
            0.2500,
            0.5000,
            1.0000,
            2.0000]
for study_name in study_names:
    ###########################################
    ########  FILE MANAGEMENT SECTION  ########
    ###########################################
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
    os.system('xcopy /s /y ' + source_python + ' ' + python_dir + '')
    sys.path.append( python_dir )
    ###########################################
    import study
    study = reload( study )
    std = study.Study()
    std.name = study_name
    std.rebuild()
    for factor in factors:
        cc = std.add_cc_fromDB( cname )
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta   =   0.,
                                pt      =  0.5,
                                pltotal = pload )
        cc.numel_r = numel_r
        cc.elem_type = 'S8R5'
        cc.axial_displ = 0.5
        cc.minInc2 = 1.e-6
        cc.initialInc2 = 1.e-3
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.damping_factor2 = 4.e-7
        cc.separate_load_steps = False
        cc.imperfection_activate = True
        cc.imperfection_scaling_factors = [factor]

    studies.append( std )
#
#
for std in studies:
    for cc in std.ccs:
        if   std.name.find( 'mode_01' ) > -1:
            cc.imperfection_buckling_modes = [1]
        elif std.name.find( 'mode_02' ) > -1:
            cc.imperfection_buckling_modes = [2]
        elif std.name.find( 'mode_03' ) > -1:
            cc.imperfection_buckling_modes = [3]
        elif std.name.find( 'mode_05' ) > -1:
            cc.imperfection_buckling_modes = [5]
        if std.name.find( 'no_PL' ) > -1:
            cc.imperfection_step_num = 1
            cc.imperfection_filename = \
                'c:\\Temp\\abaqus\\imp_lb_%s_buckling_no_PL' % cname
        elif std.name.find( 'yes_PL' ) > -1:
            cc.imperfection_step_num = 2
            cc.imperfection_filename = \
                'c:\\Temp\\abaqus\\imp_lb_%s_buckling_yes_PL' % cname
    #
    std.create_models()
#
for std in studies:
    for cc in std.ccs:
        cc.plot_forces()

