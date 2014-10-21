#
numel_r = 120
cname = 'huehne_2008_z07'
studies = {}
#
ploads = [1., 2., 2.5, 3., 4., 10.]
pts = [0.50]
for pt in pts:
    study_name = 'imp_spl_stressfree'
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
    for pload in ploads:
        cc = std.add_cc_fromDB( cname )
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta   =   0.,
                                pt      =   pt,
                                pltotal =   0. )
        cc.numel_r = numel_r
        cc.elem_type = 'S8R5'
        cc.axial_displ = 0.35
        if pload == 1. or pload == 2.:
            cc.axial_displ = 0.5
        cc.minInc2 = 1.e-6
        cc.initialInc2 = 1.e-3
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.damping_factor2 = 4.e-7
        cc.imperfection_activate = True
        cc.imperfection_buckling_modes = [1]
        cc.imperfection_scaling_factors = [1.]
        cc.imperfection_step_num = 1
        tmp = 'imp_spl_stressfree_fil'
        cc.imperfection_filename = \
            'c:\\Temp\\abaqus\\' + tmp + '\\outputs\\' + tmp +\
            '_PL_%04d' % int(pload*10)
        cc.rebuild()
        cc.jobname = study_name + '_PL_%04d' % int(pload*10)
        cc.create_model()
    studies[study_name] = std
#
    std.create_models( read_outputs = False )
#
for std in studies.values():
    for cc in std.ccs:
        cc.plot_forces()

