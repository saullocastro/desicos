#
cname = 'huehne_2008_z07'
meshes = {\
           'NUMEL_120' : 120.,
         }
#
pload  = 0.
studies = []
for meshname, numel_r in meshes.iteritems():
    study_name = 'wp3_T03_02_single_dimple_pl_curve'
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
    ploads = [1.,2.,3.,4.,5.,6.,7.,8.,9.,10.,20.]
    for pload in ploads:
        cc = std.add_cc_fromDB( cname )
        cc.meshname = meshname
        cc.damping_factor2 = 1.e-7
        cc.axial_include = False
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta   = 0.,
                                pt      = 0.5,
                                pltotal = pload )
        cc.numel_r    = numel_r
        cc.elem_type  = 'S8R5'
        cc.axial_displ= 0.5
    std.create_models()
#
#
for std in studies:
    std.create_models( read_outputs = False )
    #
    #for std in studies:
    #    for cc in std.ccs:
    #        cc.plot_forces()
    #for std in studies:
    #    std.plot( imp_factor = True )

