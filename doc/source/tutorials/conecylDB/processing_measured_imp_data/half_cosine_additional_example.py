from numpy import *

from desicos.conecylDB.fit_data import fw0

ntheta = 420
nz = 180
funcnum = 2
path = 'degenhardt_2010_z25_msi_theta_z_imp.txt'

theta = linspace(-pi, pi, ntheta)
z = linspace(0., 1., nz)
theta, z = meshgrid(theta, z, copy=False)

for m0, n0 in [[20, 30], [30, 45], [40, 60], [50, 75]]:
    c, residues = calc_c0(path, m0=m0, n0=n0, sample_size=(10*2*m*n),
                          funcnum=funcnum)

    w0 = fw0(m0, n0, z.ravel(), theta.ravel(), funcnum=funcnum)

    plt.figure(figsize=(3.5, 2))

    levels = np.linspace(w0.min(), w0.max(), 400)
    plt.contourf(theta, z*H_measured, w0.reshape(theta.shape),
                 levels=levels)

    ax = plt.gca()
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.xaxis.set_ticks([-pi, pi])
    ax.xaxis.set_ticklabels([r'$-\pi$', r'$\pi$'])
    ax.set_xlabel('Circumferential Position, $rad$')
    ax.xaxis.labelpad=-10

    ax.yaxis.set_ticks([0, 500])
    ax.set_ylabel('Height, $mm$')
    ax.yaxis.labelpad=-15

    filename = 'fw0_f{0}_z25_m_{1:03d}_n_{2:03d}.png'.format(
                funcnum, m0, n0)

    plt.gcf().savefig(filename, transparent=True, bbox_inches='tight',
                      pad_inches=0.05, dpi=90)
