import numpy as np

from desicos.conecylDB.interpolate import interp_theta_z_imp

R_model = 406.4 + 0.8128/2.
H_measured = 1219.2
ignore_bot_h = 25.4
ignore_top_h = 25.4

nz = 180
nt = 560

theta = np.linspace(-np.pi, np.pi, nt)
z = np.linspace(0, H_measured, nz)
T, Z = np.meshgrid(theta, z, copy=False)

data = np.loadtxt('sample_theta_z_imp.txt')
ts, zs, imps = data.T
a = np.vstack((ts, zs, imps)).T
mesh = np.vstack((T.ravel(), Z.ravel())).T
w0 = interp_theta_z_imp(data=a, mesh=mesh, semi_angle=0,
        H_measured=H_measured, H_model=H_measured, R_model=R_model,
        stretch_H=False, rotatedeg=-88.5, num_sub=100, ncp=5,
        power_parameter=2, ignore_bot_h=ignore_bot_h,
        ignore_top_h=ignore_top_h)
np.savetxt('tmp_inv_weighted.txt',
           np.vstack((T.ravel(), Z.ravel(), w0)).T, fmt='%1.8f')
