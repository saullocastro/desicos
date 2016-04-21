import numpy as np

from desicos.conecylDB.fit_data import calc_c0

method = 'points'
funcnum= 2

path = 'sample_theta_z_imp.txt'

R = 406.4 + 0.8128/2.
H = 1219.2
m0 = 10
n0 = 10

c0, residues = calc_c0(path, m0=m0, n0=n0, funcnum=funcnum, rotatedeg=-88.5)
outname = 'tmp_c0_{0}_f{1:d}_m0_{2:03d}_n0_{3:03d}.txt'.format(method,
        funcnum, m0, n0)
np.savetxt(outname, c0)

