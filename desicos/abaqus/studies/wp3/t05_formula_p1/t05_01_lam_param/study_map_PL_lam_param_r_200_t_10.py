#
study_name = 'study_map_PL_lam_param'
#
import numpy as np
#
modules = ['abaqus-conecyl-python',
           'modeling-analysis-python']
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
for module in modules:
    source = '\\\\MA-CASTRO\\' + module
    destin = os.path.join( study_dir, module )
    if not os.path.isdir( destin ):
        os.makedirs( destin )
    os.system('xcopy /s /y ' + source + ' ' + destin + '')
    sys.path.append( destin )
#
import study
study = reload( study )
from study import Study
import conecyl
conecyl = reload( conecyl )
import mapy
mapy = reload( mapy )
import mapy.model.properties.composite
a1s    = [ -1.,-0.75, 0.75,  1.]
a3s    = [ -1.,-0.75, 0.75,  1.]
d1s    = [ -1.,-0.75, 0.75,  1.]
d3s    = [ -1.,-0.75, 0.75,  1.]
thicks = [1.]
radius = [200]
ploads = [5.,10.,15.,20.,25.,30.,35.,40.]
# assumptions
a2,a4  = 0.,0.
b1,b2,b3,b4 = 0.,0.,0.,0.
d2,d4  = 0.,0.
e1,e2,e3,e4  = 0.,0.,0.,0.
#
# COCOMAT, see Degenhardt, 2010
laminaprop = (142.5e3,8.7e3,0.28,5.1e3,5.1e3,3.4e3,273.15)
group = 21000
mapper = {}
for a1 in a1s:
    for a3 in a3s:
        for d1 in d1s:
            for d3 in d3s:
                for t in thicks:
                    for r in radius:
                        lam =\
                            mapy.model.properties.composite.laminate.\
                                read_lamination_parameters(\
                                    a1, a2, a3, a4,
                                    b1, b2, b3, b4,
                                    d1, d2, d3, d4,
                                    e1, e2, e3, e4,
                                    laminaprop )
                        lam.t = t
                        lam.calc_ABDE_from_lamination_parameters()
                        try:
                            np.linalg.cholesky( lam.ABD )
                        except:
                            continue
                        #
                        group += 1
                        std = Study()
                        std.name = study_name
                        std.group = group
                        std.rebuild()
                        mapper[group] = { 'x1' :   a1,
                                          'x2' :   a3,
                                          'x3' :   d1,
                                          'x4' :   d3,
                                          'x5' :    t,
                                          'x6' :    r,
                                          'std':  std,
                                          'ccs':   [] }
                        for pload in ploads:
                            h = 2*r
                            cc = conecyl.ConeCyl()
                            cc.name = 'map_PL_lam_param_group_%05d' % group
                            cc.r = r
                            cc.h = h
                            cc.numel_r = 80.
                            cc.axial_displ = 10.
                            cc.separate_load_steps = False
                            cc.using_lam_parameters = True
                            cc.laminaprop = laminaprop
                            cc.impconf.ploads = []
                            cc.impconf.add_pload( theta   = 0. ,
                                                    pt      = 0.5,
                                                    pltotal = pload  )
                            cc.mapy_laminate = lam
                            std.add_cc( cc )
                            mapper[group]['ccs'].append( cc )
print 'Initialized models creation...'
#groups = mapper.keys()
#for g in groups[:5]:
#    std = mapper[g]['std']
#    std.create_models()
#    std.create_run_file()
for value in mapper.values():
    std = value['std']
    std.create_models(read_outputs=False)
    std.create_run_file()
