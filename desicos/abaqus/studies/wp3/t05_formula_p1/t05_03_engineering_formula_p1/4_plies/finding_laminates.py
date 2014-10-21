import sys
sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')
import numpy as np
np.set_printoptions(precision=1, suppress=True)
# local modules
import mapy.model.properties.composite as composite
from utils import empirical_P1_isotropic
from conecylDB import laminaprops
#
laminaprop = (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,    5.1e3, 273.15)
stacks = [\
          [  0,   0, -30, 30 ],
          [ 30, -30,   0,  0 ],
          [  0,   0, -45, 45 ],
          [ 45, -45,   0,  0 ],
          [  0,   0, -60, 60 ],
          [ 60, -60,   0,  0 ],
          [  0,   0,  90, 90 ],
          [ 90,  90,   0,  0 ],
          [  0,   0,   0,  0 ],
          [ 90,  90,  90, 90 ],
         ]

plyts = [0.125, 0.125, 0.125, 0.125]
#
# reading laminate
r = 400.
t = sum(plyts)
for i, stack in enumerate(stacks):
    lam = composite.read_stack( stack = stack,
                                 plyts = plyts,
                                 laminaprop = laminaprop,
                                 general = True )
    lam.calc_equivalent_modulus()
    E = (lam.e1 + lam.e2)/2.
    nu = min(max(lam.nu12, lam.nu21), 0.3)
    print empirical_P1_isotropic(r, t, E, nu)
    np.savetxt('stack_%03d.txt' % i, lam.ABD, delimiter='\t', fmt=('%1.3f'))

from ccs import ccs
print '----'
for cc in map( ccs.get, sorted(ccs.keys()) ):
    laminaprop = laminaprops[ cc['laminapropKey'] ]
    lam = composite.read_stack( stack = cc['stack'],
                                 plyts = [cc['plyt'] for i in cc['stack']],
                                 laminaprop = laminaprop,
                                 general = True )
    lam.calc_equivalent_modulus()
    E = (lam.e1 + lam.e2)/2.
    nu = min(max(lam.nu12, lam.nu21), 0.3)
    print empirical_P1_isotropic(r, t, E, nu)
    np.savetxt('stack_%03d.txt' % i, lam.ABD, delimiter='\t', fmt=('%1.3f'))
