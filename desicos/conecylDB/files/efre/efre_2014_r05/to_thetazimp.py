import glob
import sys

import numpy as np

from desicos.conecylDB.read_write import xyz2thetazimp, xyzthick2thetazthick

for path in glob.glob('*_msi.txt'):
    print('')
    print('WITHOUT BEST FIT')
    print('')
    xyz2thetazimp(path, 0, 150, 300, fmt='%1.6f', use_best_fit=False)
    print('')
    print('WITH BEST FIT')
    print('')
    xyz2thetazimp(path, 0, 150, 300, fmt='%1.6f')

    np.savetxt(path, np.loadtxt(path), fmt='%1.6f')

for path in glob.glob('*_ti.txt'):
    print('')
    print('WITHOUT BEST FIT')
    print('')
    xyzthick2thetazthick(path, 0, 150, 300, fmt='%1.6f', use_best_fit=False)
    print('')
    print('WITH BEST FIT')
    print('')
    xyzthick2thetazthick(path, 0, 150, 300, fmt='%1.6f')

    np.savetxt(path, np.loadtxt(path), fmt='%1.6f')

