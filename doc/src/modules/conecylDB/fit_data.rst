.. _fitting_data:

Fitting Data
============

.. _default_coordsys:

Default coordinate system
-------------------------

The default coordinate system defined has its origin at the center of the
bottom edge with the `z` axis pointing upwards towards the cone or cylinder
axis.

The raw imperfection data usually comes in a text file with three columns::

    x1 y1 z1
    x2 y2 z2
    ...
    xn yn zn

where ``xi``, ``yi`` and ``zi`` are the coordinates of the `i^{th}` point.
This data is not necessarily and rarely aligned in the default coordinate
system, such that a fitting algorithm has to be used in order to transform
the data to the default coordinates.


The fit-data module (:mod:`desicos.conecylDB.fit_data`)
-------------------------------------------------------

This module includes functions used to fit measured data using Fourier Series.

.. autofunction:: desicos.conecylDB.fit_data.best_fit_cylinder
.. autofunction:: desicos.conecylDB.fit_data.calc_c0
.. autofunction:: desicos.conecylDB.fit_data.fa
.. autofunction:: desicos.conecylDB.fit_data.fw0

Best-Fit Cylinder
-----------------

The function :func:`desicos.conecylDB.fit_data.best_fit_cylinder` can be
readily used for this task as showed in the given example.

Best-Fit Cone
-------------

TODO

Function for `w_0` from measured data
-------------------------------------

.. note:: requires Cython and a C compiler

After compiling the ``_fit_data.pyx`` file using Cython through the command::

    python setup_fit_data.py build_ext -i clean

The analyst can use the function :func:`desicos.conecylDB.fit_data.calc_c0` to
find the coefficients corresponding to the best fit of the measured data using
three different base functions, detailed below in
:func:`desicos.conecylDB.fit_data.calc_c0`.

Below one can see an example about how to use this function and then plot the
displacement patterns using different approximation levels::

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

which will result in the following figures for ``funcnum=1``:

`m_0=20`, `n_0=30`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_020_n_030.png

`m_0=30`, `n_0=45`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_030_n_045.png

`m_0=40`, `n_0=60`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_040_n_060.png

`m_0=50`, `n_0=75`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f1_z25_m_050_n_075.png

and for ``funcnum=2``:

`m_0=20`, `n_0=30`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_020_n_030.png

`m_0=30`, `n_0=45`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_030_n_045.png

`m_0=40`, `n_0=60`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_040_n_060.png

`m_0=50`, `n_0=75`:

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\fw0_f2_z25_m_050_n_075.png

It can be seen how the `w_0` function approximates the real imperfection
pattern, shown below, with the increase of `m_0` and `n_0`.

.. figure:: ..\..\..\figures\modules\conecylDB\fit_data\measured_z25.png

Comparing the results using ``funcnum=1`` and ``funcnum=2``, one see that
the latter approaches closer the real measurements, since it relaxes the
condition `w_0=0` at the edges.
