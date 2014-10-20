import numpy as np

from desicos.conecylDB.read_write import xyz2thetazimp

mps, out = xyz2thetazimp('sample.txt', alphadeg_measured=0, R_expected=406.4,
        H_measured=1219.2, clip_bottom=10, clip_top=10, use_best_fit=True,
        best_fit_output=True)

np.savetxt('tmp_Tinv.txt', out['Tinv'])
