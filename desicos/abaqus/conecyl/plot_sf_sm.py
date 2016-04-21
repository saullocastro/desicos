import numpy as np
from numpy.linalg import lstsq
from numpy import sin, cos
from regionToolset import Region

from desicos.abaqus.utils import vec_calc_elem_cg

elem_cgs = vec_calc_elem_cg( cc.part.elements )
ce = elem_cgs[ np.all( (elem_cgs[:,2] > 0.95*cc.h/2,
                                      elem_cgs[:,2] <   1.*cc.h/2),axis=0 ) ]
ce = ce[ np.argsort(ce[:,3]) ]
elem_ids = np.int_(ce[:,3])
odb = cc.attach_results()
inst = odb.rootAssembly.instances['INSTANCECYLINDER']
odb_mesh_elem_array = inst.ElementSetFromElementLabels(
                                 name='ce',
                                 elementLabels=elem_ids  )
frames = odb.steps[cc.step2Name].frames
#def get_outputs(frame, key='SF'):
def calc_sfs(frame):
    key = 'SF'
    fieldOutput = frame.fieldOutputs[key]
    output = fieldOutput.getSubset(region=odb_mesh_elem_array)
    sfs =np.array([[v.data[0], v.data[1], v.data[2], v.elementLabel] \
                      for v in output.values], dtype='float32')
    sfs = np.average(np.array([sfs[i:i+4] for i in range(0,len(elem_ids)*4,4)]),
                     axis=1)
    return sfs

vec_calc_sfs = np.vectorize(calc_sfs, otypes=[object])

test = np.array( tuple(vec_calc_sfs( frames )), dtype='float32' )
import pickle
pickle.dump( test, open(r'c:\temp\%s.ndarray' % cc.jobname,'wb') )
cc.detach_results(odb)


for i, t in enumerate(test):
    cc.plot_xy( np.arctan2(ce[:,1],ce[:,0]), t[:,0], name='thetaxRF1_%03d' % i )

#return output


