import numpy as np
from numpy import pi
import matplotlib.cm as cm
import matplotlib.pyplot as plt

plt.rcParams['axes.labelsize'] = 9.
plt.rcParams['font.size'] = 9.

path = 'tmp_inv_weighted.txt'

nz = 180
nt = 560

R = 407.168

#cmap = cm.jet
cmap = cm.gist_rainbow_r

theta, z, w0 = np.loadtxt(path, unpack=True)

fig = plt.figure(figsize=(3.5, 3.5), dpi=220)
levels = np.linspace(w0.min(), w0.max(), 400)
contour = plt.contourf(theta.reshape(nz, nt)*R, z.reshape(nz, nt),
        w0.reshape(nz, nt), levels=levels, cmap=cmap)

ax = plt.gca()
ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('left')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

ax.set_aspect('equal')
ax.xaxis.set_ticks([-pi*R, pi*R])
ax.xaxis.set_ticklabels([r'$-\pi$', r'$\pi$'])
ax.set_xlabel(r'$\theta$ $[rad]$', ha='center', va='center')
ax.xaxis.labelpad=-7

ax.yaxis.set_ticks([0, 1219.2])
ax.set_ylabel('$x$\n$[mm]$', rotation='horizontal', ha='center',
        va='center')
ax.yaxis.labelpad=-10

colorbar=True
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

fig.savefig('plot_inv_weighted.png', transparent=True,
                  bbox_inches='tight', pad_inches=0.05, dpi=220)


