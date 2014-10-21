#
numel_r = 80
elem_type = 'S8R'
cname = 'huehne_2008_z07'
meshes = {\
           'NUMEL_060' :  60.,
           'NUMEL_080' :  80.,
           'NUMEL_100' : 100.,
           'NUMEL_120' : 120.,
         }
#
pload  = 0.
factor = 0.0200
labels  = [ 'yes_PL' , 'no_PL' ]
studies = []
for meshname, numel_r in meshes.iteritems():
    for label in labels:
        study_name = 'imp_lb_%s_mrs_%s_%s_%s' \
                     % (cname, elem_type, meshname, label)
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
        cc = std.add_cc_fromDB( cname )
        cc.damping_factor2 = 4.e-6
        cc.meshname = meshname
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta   =   0.,
                                pt      =  0.5,
                                pltotal = pload )
        cc.numel_r                      = numel_r
        cc.elem_type                    = elem_type
        cc.axial_displ                   = 1.
        cc.imperfection_activate        = True
        cc.imperfection_scaling_factors = [factor]
        if label == 'no_PL':
            cc.imperfection_step_num    = 1
        elif label == 'yes_PL':
            cc.imperfection_step_num    = 2
        cc.imperfection_buckling_modes  = [1]
        cc.imperfection_filename = \
            'c:\\Temp\\abaqus\\imp_lb_mrs_%s_%s_%s' \
            % (elem_type, meshname, label)
        studies.append( std )
#
#
for std in studies:
    std.create_models()
    #
    #for std in studies:
    #    for cc in std.ccs:
    #        cc.plot_forces()
    #for std in studies:
    #    std.plot( imp_factor = True )

