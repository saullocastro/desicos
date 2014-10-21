#
cname = 'zimmermann_1992_z33'
pload  = 0.
studies = []
bs = [30., 45., 90.]
for b in bs:
    study_name = 'wp3_t03_02_asi_z33_b_%03d' % int(b)
    ###########################################
    ########  FILE MANAGEMENT SECTION  ########
    ###########################################
    source_python = r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python'
    import sys
    import os
    study_dir  = os.path.join( r'C:\Temp','abaqus',study_name )
    if not os.path.isdir( study_dir ):
        os.makedirs( study_dir )
    output_dir = os.path.join( study_dir,'outputs' )
    print 'configuring folders...'
    print '\t' + output_dir
    if not os.path.isdir( output_dir ):
        os.makedirs( output_dir )
    sys.path.append( source_python )
    ###########################################
    import study
    study = reload( study )
    std = study.Study()
    std.name = study_name
    std.rebuild()
    wbs = [ 0.08, 0.16, 0.24, 0.32, 0.40, 0.48, 0.72,
            0.80, 0.88, 1.32, 2.00, 2.64, 0.04 ]
    for wb in wbs:
        cc = std.add_cc_fromDB( cname )
        cc.damping_factor2 = 1.e-7
        cc.initialInc2 = 1.e-3
        cc.minInc2 = 1.e-6
        cc.maxInc2 = 1.e-3
        cc.maxNumInc2 = 100000
        cc.impconf.ploads = []
        cc.impconf.add_axisymmetric( 0.5, b, wb )
        cc.numel_r    = 120.
        cc.elem_type  = 'S8R5'
        cc.axial_displ = 1.
    std.create_models()
    studies.append(std)
