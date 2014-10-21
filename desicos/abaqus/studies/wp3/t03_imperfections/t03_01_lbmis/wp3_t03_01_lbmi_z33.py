#
numel_r = 120
cname = 'zimmermann_1992_z33'
studies = []
modes = [1,3,5,7,9,11,13,15,17,19,21,23,25,27,29,31,33,35,37,39,41,43,45,47,49]
factors = [ 0.015625,
            0.031250,
            0.062500,
            0.125000,
            0.250000,
            0.500000,
            1.000000,
            2.000000,
            4.000000,
            5.000000 ]
for mode in modes:
    study_name = 'wp3_t03_01_lbmi_z33_mode_%02d' % mode
    ###########################################
    ########  FILE MANAGEMENT SECTION  ########
    ###########################################
    source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
    import sys
    sys.path.append( source_python )
    import os
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
    for factor in factors:
        cc = std.add_cc_fromDB( cname )
        cc.impconf.ploads = []
        cc.impconf.add_lbmi( mode, factor )
        cc.numel_r = numel_r
        cc.elem_type = 'S8R5'
        cc.axial_displ = 0.9
        cc.minInc2 = 1.e-6
        cc.initialInc2 = 1.e-2
        cc.maxInc2 = 1.e-2
        cc.maxNumInc2 = 100000
        cc.damping_factor2 = 1.e-7
        cc.separate_load_steps = False
        cc.request_force_output = False
        cc.time_points = 80

    std.create_models()
    studies.append( std )
#
#
