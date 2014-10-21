import sys
sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')
import numpy as np
np.set_printoptions(precision=1, suppress=True)
# local modules
import mapy.model.properties.composite as composite
#
laminaprop = (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3, 273.15)
stacks = [[  0,  0],
          [-30, 30],
          [-45, 45],
          [-60, 60],
          [ 90, 90]]

plyts = [0.125, 0.125]
#
# reading laminate
for i, stack in enumerate(stacks):
    objL = composite.read_stack( stack = stack,
                                 plyts = plyts,
                                 laminaprop = laminaprop,
                                 general = True )
    np.savetxt('stack_%03d.txt' % i, objL.ABD, delimiter='\t', fmt=('%1.3f'))
