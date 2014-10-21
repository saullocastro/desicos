import numpy as np
import sys
import os
#
cylnames = [\
           'r_100_h_800',
           'r_200_h_800',
           'r_300_h_800',
           'r_400_h_800',
           ]
numel_r = 80
alphadeg = 0
#
#
#
prefix = 'zimmermann_r_effect_t_const'
#
studies = {}
stack = [24.,-24.,41.,-41.]
for cylname in cylnames:
    study_name = '_'.join( [ prefix, cylname,
                             'a%02d' % alphadeg,
                             'numel_r_%03d' % numel_r,
                           ])
    source_python = r'\\MA-CASTRO\abaqus-conecyl-python'
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
    os.system('copy ' + source_python + ' ' + python_dir + '')
    sys.path.append( python_dir )
    #
    import study
    study = reload( study )
    std = study.Study()
    std.name = study_name
    ploads = [4.,6.,8.,10.,12.,16.,20.,24.,28.,32.,36.]
    #ploads = [2.,6.,10.]
    for pload in ploads:
        cc = std.add_cc_fromDB( cylname )
        cc.impconf.ploads = []
        cc.impconf.add_pload( theta = 0.,
                                pt = 0.5,
                                pltotal = pload )
        cc.stack = stack
        cc.numel_r = numel_r
        cc.axial_displ = 10.
        cc.alphadeg = alphadeg
        #cc.axial_include = False
    std.create_models( read_outputs=True )
    studies[std.name] = std
print 'OK'
for std in studies.values():
    for cc in std.ccs:
        cc.plot_forces( step_num = 2 )
    std.plot( step_num = 1,
              only_PL = False,
              cir_criterion = 'zero_radial_displ',
              cir_threshold = 0.0125 )
