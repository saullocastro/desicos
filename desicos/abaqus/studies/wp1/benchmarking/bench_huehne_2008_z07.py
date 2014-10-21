#
numel_r = 240
cname = 'huehne_2008_z07'
studies = {}
#
ploads = [10.]
pts = [0.50]
for pt in pts:
    study_name = 'bench_%s' % cname
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
        cc.damping_factor2 = 4.e-6
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta   =   0.,
                                pt      =   pt,
                                pltotal = pload )
        cc.numel_r = numel_r
        cc.elem_type = 'S4R'
        cc.axial_displ = 1.

    studies[study_name] = std
#
    std.create_models( read_outputs = True )
#
for std in studies.values():
    for cc in std.ccs:
        cc.plot_forces()
for std in studies.values():
    std.plot()

