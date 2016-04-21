import numpy as np
import mayavi.mlab as mlab

from desicos.conecylDB.read_write import xyz2thetazimp

R = 406.4
R_best_fit = 407.168

data = np.genfromtxt('sample_theta_z_imp.txt')
thetas, zfit, dR = data.T

xpos = R_best_fit*np.cos(thetas)
ypos = R_best_fit*np.sin(thetas)
sf = 20
x2 = xpos + sf*dR*np.cos(thetas)
y2 = ypos + sf*dR*np.sin(thetas)
z2 = zfit

black = (0,0,0)
white = (1,1,1)
mlab.figure(bgcolor=white)
mlab.points3d(x2, y2, z2, color=(0.5,0.5,0.5))
mlab.plot3d([0, 600], [0, 0], [0, 0], color=black, tube_radius=10.)
mlab.plot3d([0, 0], [0, 600], [0, 0], color=black, tube_radius=10.)
mlab.plot3d([0, 0], [0, 0], [0, 1600], color=black, tube_radius=10.)
mlab.text3d(650, -50, +50, 'x', color=black, scale=100.)
mlab.text3d(0, 650, +50, 'y', color=black, scale=100.)
mlab.text3d(0, -50, 1650, 'z', color=black, scale=100.)
mlab.savefig('plot_sample_3d_transformed.png')
