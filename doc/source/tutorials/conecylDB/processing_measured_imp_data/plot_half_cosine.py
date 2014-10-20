import numpy as np
from numpy import pi
import matplotlib.cm as cm
import matplotlib.pyplot as plt

from compmech.conecyl.imperfections import fw0

plt.rcParams['axes.labelsize'] = 9.
plt.rcParams['font.size'] = 9.

method = 'points'
funcnum = 2
names = ['C01']

nz = 180
nt = 560

H = 1219.2
zpts_min = 25.4
zpts_max = H - 25.4
R = 406.4 + 0.8128/2.

#cmap = cm.jet
cmap = cm.gist_rainbow_r

m0 = 10
n0 = 10

filename = 'tmp_c0_{0}_f{1:d}_m0_{2:03d}_n0_{3:03d}.txt'.format(method,
        funcnum, m0, n0)
c0 = np.loadtxt(filename)
ts = np.linspace(-pi, pi, nt)
xs = np.linspace(0, 1., nz)
zs = xs*H
check = (zs >= zpts_min) & (zs <= zpts_max)
test = xs[check]
xs -= test.min()
xs /= xs.max()
xs[xs<0] = 0
xs[xs>1] = 1

dummy, xs = np.meshgrid(ts, xs, copy=False)
ts, zs = np.meshgrid(ts, zs, copy=False)

w0 = fw0(m0, n0, c0, xs, ts, funcnum=funcnum)
w0.flat[(zs.flat < zpts_min) | (zs.flat > zpts_max)] = 0

fig = plt.figure(figsize=(3.5, 3.5), dpi=220)

levels = np.linspace(w0.min(), w0.max(), 400)
contour = plt.contourf(ts*R, zs, w0.reshape(ts.shape), levels=levels,
        cmap=cmap)

ax = plt.gca()
ax.set_aspect('equal')
ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('left')
ax.spines['bottom'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)

ax.xaxis.set_ticks([-pi*R, pi*R])
ax.xaxis.set_ticklabels([r'$-\pi$', r'$\pi$'])
ax.set_xlabel(r'$\theta$ $[rad]$', va='center', ha='center')
ax.xaxis.labelpad = -7

ax.yaxis.set_ticks([0, H])
ax.set_ylabel('$z$\n$[mm]$', rotation='horizontal', va='center',
        ha='center')
ax.yaxis.labelpad = -10


colorbar = True
if colorbar:
    from mpl_toolkits.axes_grid1 import make_axes_locatable

    fsize = 10
    cbar_nticks = 2
    divider = make_axes_locatable(ax)
    cax = divider.append_axes('right', size='5%', pad=0.05)
    cbarticks = np.linspace(w0.min(), w0.max(), cbar_nticks)
    cbar = plt.colorbar(contour, ticks=cbarticks, format='%1.3f',
                        cax=cax, cmap=cmap)
    cax.text(0.5, 1.1, '$w_0$ $[mm]$', ha='left', va='bottom',
            fontsize=fsize)
    cbar.outline.remove()
    cbar.ax.tick_params(labelsize=fsize, pad=0., tick2On=False)

fig.savefig('plot_half_cosine.png', transparent=True, bbox_inches='tight',
        pad_inches=0.05, dpi=220)



