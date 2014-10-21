#
study_name = 'study_comparison_direct_ABD_input'
#
import numpy as np
#
if __name__ == '__main__':
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
    os.system('copy ' + source_python + ' ' + python_dir + '')
    sys.path.append( python_dir )
    #
    import study
    study = reload( study )
    from study import Study
    std = Study()
    std.name = study_name
    std.rebuild()
    import conecyl
    conecyl = reload( conecyl )
    import mapy
    mapy = reload( mapy )
    import mapy.model.properties.composite
    a1s = [ -1.,  1.]
    a3s = [ -1.,  1.]
    d1s = [ -1.,  1.]
    d3s = [ -1.,  1.]
    thicks = [0.5, 1.]
    radius = [100, 200]
    ploads = [5.,10.,15.,20.,25.,30.]
    # assumptions
    a2,a4  = 0.,0.
    b1,b2,b3,b4 = 0.,0.,0.,0.
    d2,d4  = 0.,0.
    e1,e2,e3,e4  = 0.,0.,0.,0.
    #
    ccs = []
    e3s = [ -1.,  1.]
    # COCOMAT, see Degenhardt, 2010
    laminaprop = (142.5e3,8.7e3,0.28,5.1e3,5.1e3,3.4e3,273.15)

    r=100
    h=200
    h = 2*r
    cc = conecyl.ConeCyl()
    cc.jobname = 'test_abd'
    cc.name = 'r_%d_h_%d' % (int(r), int(h))
    cc.r = r
    cc.h = h
    cc.numel_r = 80.
    cc.axial_displ = 10.
    cc.axial_include = True
    cc.stack = [24,-24,41,-41]
    cc.laminaprop = laminaprop
    cc.plyts = [0.125 for i in cc.stack]
    cc.separate_load_steps = True
    cc.using_lam_parameters = True
    cc.impconf.ploads = []
    cc.impconf.add_pload( theta   = 0. ,
                            pt      = 0.5,
                            pltotal = 20. )
    cc.create_model()
    std.add_cc( cc )
    cc.write_job( submit = True )
    cc.read_outputs()
    cc.read_axial_load_displ( cc.step2Name )

    cc2 = conecyl.ConeCyl()
    cc2.jobname              = 'test_conventional'
    cc2.name                 = cc.name
    cc2.r                    = cc.r
    cc2.h                    = cc.h
    cc2.numel_r              = cc.numel_r
    cc2.axial_displ           = cc.axial_displ
    cc2.axial_include = cc.axial_include
    cc2.stack                = cc.stack
    cc2.laminaprop           = cc.laminaprop
    cc2.plytt                = cc.plyts
    cc2.separate_load_steps  = cc.separate_load_steps
    cc2.using_lam_parameters = False
    cc2.impconf.ploads     = []
    cc2.impconf.add_pload( theta = 0.,
                             pt = 0.5,
                             pltotal = 20. )
    cc2.create_model()
    std.add_cc( cc2 )
    cc2.write_job( submit = True )
    cc2.read_outputs()
    cc2.read_axial_load_displ( cc2.step2Name )

