import numpy as np
import mayavi.mlab as mlab

from desicos.conecylDB.read_write import xyz2thetazimp

R = 406.4 # nominal radius
H = 1219.2 # nominal height
R_best_fit = 407.193 # radius obtained with the best-fit routine

thetas, zfit, dR = np.genfromtxt('sample_theta_z_imp.txt', unpack=True)

xpos = R_best_fit*np.cos(thetas)
ypos = R_best_fit*np.sin(thetas)
sf = 20
x2 = xpos + sf*dR*np.cos(thetas)
y2 = ypos + sf*dR*np.sin(thetas)
z2 = zfit

Tinv = np.loadtxt('tmp_Tinv.txt')
x, y, z = Tinv.dot(np.vstack((x2, y2, z2, np.ones_like(x2))))

black = (0,0,0)
white = (1,1,1)
mlab.figure(bgcolor=white)
mlab.points3d(x, y, z, color=(0,1,0))
mlab.plot3d([0, 600], [0, 0], [0, 0], color=black, tube_radius=10.)
mlab.plot3d([0, 0], [0, 1600], [0, 0], color=black, tube_radius=10.)
mlab.plot3d([0, 0], [0, 0], [0, 600], color=black, tube_radius=10.)
mlab.text3d(650, -50, +50, 'x', color=black, scale=100.)
mlab.text3d(0, 1650, +50, 'y', color=black, scale=100.)
mlab.text3d(0, -50, 650, 'z', color=black, scale=100.)
mlab.savefig('plot_sample_3d.png', size=(500, 500))
