import sys
import mapy
mapy = reload( mapy )
import mapy.model.properties.composite
mapy.model.properties.composite = reload( mapy.model.properties.composite )
a1s = [ -1.,-0.75, 0.75,  1.]
a3s = [ -1.,-0.75, 0.75,  1.]
d1s = [ -1.,-0.75, 0.75,  1.]
d3s = [ -1.,-0.75, 0.75,  1.]
thicks = [0.5, 1.]
radius = [100, 200]
ploads = [5.,10.,15.,20.,25.,30.]
# assumptions
a2,a4  = 0.,0.
b1,b2,b3,b4 = 0.,0.,0.,0.
d2,d4  = 0.,0.
e1,e2,e3,e4 = 0.,0.,0.,0.
#
# COCOMAT, see Degenhardt, 2010
laminaprop = (142.5e3,8.7e3,0.28,5.1e3,5.1e3,3.4e3,273.15)
import numpy as np
count = 0
totalcount = 0
group = 0
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
                        mapper[group] = {'x1':a1,
                                         'x2':a3,
                                         'x3':d1,
                                         'x4':d3,
                                         'x5':t ,
                                         'x6':r ,
                                         'ccs':[]}
                        for pload in ploads:
