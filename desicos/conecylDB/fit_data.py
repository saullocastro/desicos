r"""
Fitting Data (:mod:`desicos.conecylDB.fit_data`)
==================================================

.. currentmodule:: desicos.conecylDB.fit_data

This module includes functions used to fit measured imperfection data.

"""
from random import sample
import os

import numpy as np
from numpy import sin, cos, pi, deg2rad

from desicos.logger import *
from desicos.constants import FLOAT


def best_fit_cylinder(path, H, R_expected=10., save=True, errorRtol=1.e-9,
                      maxNumIter=1000, sample_size=None):
    r"""Fit a best cylinder for a given set of measured data

    The coordinate transformation which must be performed in order to adjust
    the raw data to the finite element coordinate system is illustrated below:

    .. figure:: ../../../figures/modules/conecylDB/fit_data/coord_sys_trans.png
        :width: 400

    This transformation can be represented in matrix form as:

    .. math::
     [T] = \begin{bmatrix}
     cos(\beta) &  sin(\alpha)sin(\beta) & -cos(\alpha)sin(\beta) & \Delta x_0
     \\
              0 &            cos(\alpha) &            sin(\alpha) & \Delta y_0
     \\
     sin(\beta) & -sin(\alpha)cos(\beta) &  cos(\alpha)cos(\beta) & \Delta z_0
     \\
           \end{bmatrix}

    Note that **five** variables are unknowns:

    - the rotation angles `\alpha` and `\beta`
    - the three components of the translation `\Delta x_0`, `\Delta y_0` and
      `\Delta z_0`

    The five unknowns are calculated iteratively in a non-linear least-sqares
    problem (solved with ``scipy.optimize.leastsq``), where the measured data
    is transformed to the reference coordinate system and there compared with
    a reference cylinder in order to compute the residual error using:

    .. math::
        \begin{Bmatrix} x_{ref} \\ y_{ref} \\ z_{ref} \end{Bmatrix} =
        [T]
        \begin{Bmatrix} x_m \\ y_m \\ z_m \\ 1 \end{Bmatrix}
        \\
        Error = \sqrt{(\Delta r)^2 + (\Delta z)^2}

    where:

    - `x_m`, `y_m` and `z_m` are the data coordinates in the data coordinate
      system
    - `x_{ref}` `x_{ref}` are the data coordinates in the :ref:`reference
      coordinate system <figure_conecyl>`
    - `\Delta r` and `\Delta z` are defined as:

        .. math::
            \Delta r = R - \sqrt{x_{ref}^2 + y_{ref}^2}
            \\
            \Delta z = \begin{cases}
                            -z_{ref}, & \text{if } z_{ref} < 0 \\
                                   0, & \text{if } 0 <= z_{ref} <= H \\
                         z_{ref} - H, & \text{if } z_{ref} > H \\
                       \end{cases}

    Since the measured data may have an unknown radius `R`, the solution of
    these equations has to be performed iteratively with one additional
    external loop in order to update `R`.

    Parameters
    ----------
    path : str or np.ndarray
        The path of the file containing the data. Can be a full path using
        ``r"C:\Temp\inputfile.txt"``, for example.
        The input file must have 3 columns "`x` `y` `z`" expressed
        in Cartesian coordinates.

        This input can also be a ``np.ndarray`` object, with `x`, `y`, `z`
        in each corresponding column.
    H : float
        The nominal height of the cylinder.
    R_expected : float, optional
        The nominal radius of the cylinder, used as a first guess to find
        the best-fit radius (``R_best_fit``). Note that if not specified more
        iterations may be required.
    save : bool, optional
        Whether to save an ``"output_best_fit.txt"`` in the working directory.
    errorRtol : float, optional
        The error tolerance for the best-fit radius to stop the iterations.
    maxNumIter : int, optional
        The maximum number of iterations for the best-fit radius.
    sample_size : int, optional
        If the input file containing the measured data is too big it may
        be convenient to use only a sample of it in order to calculate the
        best fit.

    Returns
    -------
    out : dict
        A Python dictionary with the entries:

        ``out['R_best_fit']`` : float
            The best-fit radius of the input sample.
        ``out['T']`` : np.ndarray
            The transformation matrix as a `3 \times 4` 2-D array. This matrix
            does the transformation: input_pts --> output_pts.
        ``out['Tinv']`` : np.ndarray
            The inverse transformation matrix as a `3 \times 4` 2-D array.
            This matrix does the transformation: output_pts --> input_pts.
        ``out['input_pts']`` : np.ndarray
            The input points in a `3 \times N` 2-D array.
        ``out['output_pts']`` : np.ndarray
            The transformed points in a `3 \times N` 2-D array.

    Examples
    --------

    1) General usage

    For a given cylinder with expected radius and height of ``R_expected`` and
    ``H``::

        from desicos.conecylDB.fit_data import best_fit_cylinder

        out = best_fit_cylinder(path, H=H, R_expected=R_expected)
        R_best_fit = out['R_best_fit']
        T = out['T']
        Tinv = out['Tinv']

    2) Using the transformation matrices ``T`` and ``Tinv``

    For a given input data with `x, y, z` positions in each line::

        x, y, z = np.loadtxt('input_file.txt', unpack=True)

    the transformation could be obtained with::

        xnew, ynew, znew = T.dot(np.vstack((x, y, z, np.ones_like(x))))

    and the inverse transformation::

        x, y, z = Tinv.dot(np.vstack((xnew, ynew, znew, np.ones_like(xnew))))



    """
    from scipy.optimize import leastsq

    if isinstance(path, np.ndarray):
        input_pts = path.T
    else:
        input_pts = np.loadtxt(path, unpack=True)

    if input_pts.shape[0] != 3:
        raise ValueError('Input does not have the format: "x, y, z"')

    if sample_size:
        num = input_pts.shape[1]
        if sample_size < num:
            input_pts = input_pts[:, sample(range(num), int(sample_size))]

    pts = np.vstack((input_pts, np.ones_like(input_pts[0, :])))

    def fT(p):
        a, b, x0, y0, z0 = p
        a %= 2*np.pi
        b %= 2*np.pi
        # rotation in x, y
        T = np.array([[cos(b),  sin(a)*sin(b), -cos(a)*sin(b), x0],
                      [     0,         cos(a),         sin(a), y0],
                      [sin(b), -sin(a)*cos(b),  cos(a)*cos(b), z0]])
        return T

    i = 0
    R = R_expected
    while i <= maxNumIter:
        i += 1

        def calc_dist(p, pts):
            T = fT(p)
            xn, yn, zn = T.dot(pts)
            dz = np.zeros_like(zn)
            factor = 0.1
            # point below the bottom edge
            mask = zn < 0
            dz[mask] = -zn[mask]*factor

            # point inside the cylinder
            pass
            #dz[(zn >= 0) & (zn <= H)] *= 0

            # point above the top edge
            mask = zn > H
            dz[mask] = (zn[mask] - H)*factor

            dr = R - np.sqrt(xn**2 + yn**2)
            dist = np.sqrt(dr**2 + dz**2)
            return dist

        # initial guess for the optimization variables
        # the variables are alpha, beta, x0, y0, z0
        x, y, z = input_pts
        p = [0.5, 0.5, 2*x.mean(), 2*y.mean(), 2*z.mean()]

        # performing the leastsq analysis
        popt, pcov = leastsq(func=calc_dist, x0=p, args=(pts,),
                             ftol=1.e-12, xtol=1.e-12, maxfev=1000000)
        T = fT(popt)
        output_pts = T.dot(pts)
        x, y, z = output_pts
        mask = (z>=0) & (z<=H)
        R_best_fit = np.sqrt(x[mask]**2 + y[mask]**2).mean()
        errorR = abs(R_best_fit - R)/R_best_fit

        log('Iteration: {0}, R_best_fit: {1}, errorR: {2}'.format(
            i, R_best_fit, errorR), level=1)

        if errorR < errorRtol:
            break
        else:
            R = R_best_fit
    else:
        warn('The maximum number of iterations was achieved!')

    alpha, beta = popt[:2]
    alpha %= 2*np.pi
    beta %= 2*np.pi
    log('')
    log('Transformation matrix:\n{0}'.format(T))
    log('')
    log('Z versor: {0}*i + {1}*j + {2}*k'.format(*T[-1,:-1]))
    log('')
    log('alpha: {0} rad; beta: {1} rad'.format(alpha, beta))
    log('')
    log('x0, y0, z0: {0}, {1}, {2}'.format(*T[:,-1]))
    log('')
    log('Best fit radius: {0}'.format(R_best_fit))
    log('    errorR: {0}, numiter: {1}'.format(errorR, i))
    log('')

    if save:
        np.savetxt('output_best_fit.txt', np.vstack((x, y, z)).T)

    Tinv = np.zeros_like(T)
    Tinv[:3, :3] = T[:3, :3].T
    Tinv[:, 3] = -T[:, 3]
    return dict(R_best_fit=R_best_fit,
                input_pts=input_pts,
                output_pts=output_pts,
                T=T, Tinv=Tinv)


def best_fit_cone(path, H, alphadeg, R_expected=10., save=True,
        errorRtol=1.e-9, maxNumIter=1000, sample_size=None):
    r"""Fit a best cone for a given set of measured data

    .. note:: NOT IMPLEMENTED YET

    """
    raise NotImplementedError('Function not implemented yet!')


def calc_c0(path, m0=50, n0=50, funcnum=2, fem_meridian_bot2top=True,
        rotatedeg=0., filter_m0=None, filter_n0=None, sample_size=None,
        maxmem=8):
    r"""Find the coefficients that best fit the `w_0` imperfection

    The measured data will be fit using one of the following functions,
    selected using the ``funcnum`` parameter:

    1) Half-Sine Function

    .. math::
        w_0 = \sum_{i=1}^{m_0}{ \sum_{j=0}^{n_0}{
                 {c_0}_{ij}^a sin{b_z} sin{b_\theta}
                +{c_0}_{ij}^b sin{b_z} cos{b_\theta} }}

    2) Half-Cosine Function (default)

    .. math::
        w_0 = \sum_{i=0}^{m_0}{ \sum_{j=0}^{n_0}{
                {c_0}_{ij}^a cos{b_z} sin{b_\theta}
                +{c_0}_{ij}^b cos{b_z} cos{b_\theta} }}

    3) Complete Fourier Series

    .. math::
        w_0 = \sum_{i=0}^{m_0}{ \sum_{j=0}^{n_0}{
                 {c_0}_{ij}^a sin{b_z} sin{b_\theta}
                +{c_0}_{ij}^b sin{b_z} cos{b_\theta}
                +{c_0}_{ij}^c cos{b_z} sin{b_\theta}
                +{c_0}_{ij}^d cos{b_z} cos{b_\theta} }}

    where:

    .. math::
        b_z = i \pi \frac z H_{points}

        b_\theta = j \theta

    where `H_{points}` represents the difference between the maximum and
    the minimum `z` values in the imperfection file.

    The approximation can be written in matrix form as:

    .. math::
        w_0 = [g] \{c_0\}

    where `[g]` carries the base functions and `{c_0}` the respective
    amplitudes. The solution consists on finding the best `{c_0}` that
    minimizes the least-square error between the measured imperfection pattern
    and the `w_0` function.

    Parameters
    ----------
    path : str or np.ndarray
        The path of the file containing the data. Can be a full path using
        ``r"C:\Temp\inputfile.txt"``, for example.
        The input file must have 3 columns "`\theta` `z` `imp`" expressed
        in Cartesian coordinates.

        This input can also be a ``np.ndarray`` object, with
        `\theta`, `z`, `imp` in each corresponding column.
    m0 : int
        Number of terms along the meridian (`z`).
    n0 : int
        Number of terms along the circumference (`\theta`).
    funcnum : int, optional
        As explained above, selects the base functions used for
        the approximation.
    fem_meridian_bot2top : bool, optional
        A boolean indicating if the finite element has the `x` axis starting
        at the bottom or at the top.
    rotatedeg : float, optional
        Rotation angle in degrees telling how much the imperfection pattern
        should be rotated about the `X_3` (or `Z`) axis.
    filter_m0 : list, optional
        The values of ``m0`` that should be filtered (see :func:`.filter_c0`).
    filter_n0 : list, optional
        The values of ``n0`` that should be filtered (see :func:`.filter_c0`).
    sample_size : int or None, optional
        An in  specifying how many points of the imperfection file should
        be used. If ``None`` is used all points file will be used in the
        computations.
    maxmem : int, optional
        Maximum RAM memory in GB allowed to compute the base functions.
        The ``scipy.interpolate.lstsq`` will go beyond this limit.

    Returns
    -------
    out : np.ndarray
        A 1-D array with the best-fit coefficients.

    Notes
    -----
    If a similar imperfection pattern is expected along the meridian and along
    the circumference, the analyst can use an optimized relation between
    ``m0`` and ``n0`` in order to achieve a higher accuracy for a given
    computational cost, as proposed by Castro et al. (2014):

    .. math::
        n_0 = m_0 \frac{\pi(R_{bot}+R_{top})}{2H}

    """
    from scipy.linalg import lstsq

    if isinstance(path, np.ndarray):
        input_pts = path
        path = 'unmamed.txt'
    else:
        input_pts = np.loadtxt(path)

    if input_pts.shape[1] != 3:
        raise ValueError('Input does not have the format: "theta, z, imp"')
    if (input_pts[:,0].min() < -2*np.pi or input_pts[:,0].max() > 2*np.pi):
        raise ValueError(
                'In the input: "theta, z, imp"; "theta" must be in radians!')

    log('Finding c0 coefficients for {0}'.format(str(os.path.basename(path))))
    log('using funcnum {0}'.format(funcnum), level=1)

    if sample_size:
        num = input_pts.shape[0]
        if sample_size < num:
            input_pts = input_pts[sample(range(num), int(sample_size))]

    if funcnum==1:
        size = 2
    elif funcnum==2:
        size = 2
    elif funcnum==3:
        size = 4
    else:
        raise ValueError('Valid values for "funcnum" are 1, 2 or 3')

    maxnum = maxmem*1024*1024*1024*8/(64*size*m0*n0)
    num = input_pts.shape[0]
    if num >= maxnum:
        input_pts = input_pts[sample(range(num), int(maxnum))]
        warn('Using {0} measured points due to the "maxmem" specified'.
                format(maxnum), level=1)

    ts = input_pts[:, 0].copy()
    if rotatedeg:
        ts += deg2rad(rotatedeg)
    zs = input_pts[:, 1]
    w0pts = input_pts[:, 2]
    #NOTE using `H_measured` did not allow a good fitting result
    #zs /= H_measured
    zs = (zs - zs.min())/(zs.max() - zs.min())
    if not fem_meridian_bot2top:
        #TODO
        zs *= -1
        zs += 1

    a = fa(m0, n0, zs, ts, funcnum)

    log('Base functions calculated', level=1)
    c0, residues, rank, s = lstsq(a, w0pts)
    log('Finished scipy.linalg.lstsq', level=1)
    if filter_m0!=None or filter_n0!=None:
        c0 = filter_c0(m0, n0, c0, filter_m0, filter_n0, funcnum=funcnum)

    return c0, residues


def filter_c0(m0, n0, c0, filter_m0, filter_n0, funcnum=2):
    r"""Apply filter to the imperfection coefficients `\{c_0\}`

    A filter consists on removing some frequencies that are known to be
    related to rigid body modes or spurious measurement noise. The frequencies
    to be removed should be passed through inputs ``filter_m0`` and
    ``filter_n0``.

    Parameters
    ----------
    m0 : int
        The number of terms along the meridian.
    n0 : int
        The number of terms along the circumference.
    c0 : np.ndarray
        The coefficients of the imperfection pattern.
    filter_m0 : list
        The values of ``m0`` that should be filtered.
    filter_n0 : list
        The values of ``n0`` that should be filtered.
    funcnum : int, optional
        The function used for the approximation (see function :func:`.calc_c0`)

    Returns
    -------
    c0_filtered : np.ndarray
        The filtered coefficients of the imperfection pattern.

    """
    log('Applying filter...')
    log('using c0.shape={0}, funcnum={1}'.format(c0.shape, funcnum), level=1)
    fm0 = filter_m0
    fn0 = filter_n0
    log('using filter_m0={0}'.format(fm0))
    log('using filter_n0={0}'.format(fn0))
    if funcnum==1:
        if 0 in fm0:
            raise ValueError('For funcnum==1 m0 starts at 1!')
        pos = ([2*(m0*j + (i-1)) + 0 for j in range(n0) for i in fm0] +
               [2*(m0*j + (i-1)) + 1 for j in range(n0) for i in fm0])
        pos += ([2*(m0*j + (i-1)) + 0 for j in fn0 for i in range(1, m0+1)] +
                [2*(m0*j + (i-1)) + 1 for j in fn0 for i in range(1, m0+1)])
    elif funcnum==2:
        pos = ([2*(m0*j + i) + 0 for j in range(n0) for i in fm0] +
               [2*(m0*j + i) + 1 for j in range(n0) for i in fm0])
        pos += ([2*(m0*j + i) + 0 for j in fn0 for i in range(m0)] +
                [2*(m0*j + i) + 1 for j in fn0 for i in range(m0)])
    elif funcnum==3:
        pos = ([4*(m0*j + i) + 0 for j in range(n0) for i in fm0] +
               [4*(m0*j + i) + 1 for j in range(n0) for i in fm0] +
               [4*(m0*j + i) + 2 for j in range(n0) for i in fm0] +
               [4*(m0*j + i) + 3 for j in range(n0) for i in fm0])
        pos += ([4*(m0*j + i) + 0 for j in fn0 for i in range(m0)] +
                [4*(m0*j + i) + 1 for j in fn0 for i in range(m0)] +
                [4*(m0*j + i) + 2 for j in fn0 for i in range(m0)] +
                [4*(m0*j + i) + 3 for j in fn0 for i in range(m0)])
    c0_filtered = c0.copy()
    c0_filtered[pos] = 0
    log('Filter applied!')
    return c0_filtered


def fa(m0, n0, zs_norm, thetas, funcnum=2):
    """Calculates the matrix with the base functions for `w_0`

    The calculated matrix is directly used to calculate the `w_0` displacement
    field, when the corresponding coefficients `c_0` are known, through::

        a = fa(m0, n0, zs_norm, thetas, funcnum)
        w0 = a.dot(c0)

    Parameters
    ----------
    m0 : int
        The number of terms along the meridian.
    n0 : int
        The number of terms along the circumference.
    zs_norm : np.ndarray
        The normalized `z` coordinates (from 0. to 1.) used to compute
        the base functions.
    thetas : np.ndarray
        The angles in radians representing the circumferential positions.
    funcnum : int, optional
        The function used for the approximation (see function :func:`.calc_c0`)

    """
    try:
        import _fit_data
        return _fit_data.fa(m0, n0, zs_norm, thetas, funcnum)
    except:
        warn('_fit_data.pyx could not be imported, executing in Python/NumPy'
                + '\n\t\tThis mode is slower and needs more memory than the'
                + '\n\t\tPython/NumPy/Cython mode',
             level=1)
        zs = zs_norm.ravel()
        ts = thetas.ravel()
        n = zs.shape[0]
        zsmin = zs.min()
        zsmax = zs.max()
        if zsmin < 0 or zsmax > 1:
            log('zs.min()={0}'.format(zsmin))
            log('zs.max()={0}'.format(zsmax))
            raise ValueError('The zs array must be normalized!')
        if funcnum==1:
            a = np.array([[sin(i*pi*zs)*sin(j*ts), sin(i*pi*zs)*cos(j*ts)]
                           for j in range(n0) for i in range(1, m0+1)])
            a = a.swapaxes(0,2).swapaxes(1,2).reshape(n,-1)
        elif funcnum==2:
            a = np.array([[cos(i*pi*zs)*sin(j*ts), cos(i*pi*zs)*cos(j*ts)]
                           for j in range(n0) for i in range(m0)])
            a = a.swapaxes(0,2).swapaxes(1,2).reshape(n,-1)
        elif funcnum==3:
            a = np.array([[sin(i*pi*zs)*sin(j*ts), sin(i*pi*zs)*cos(j*ts),
                           cos(i*pi*zs)*sin(j*ts), cos(i*pi*zs)*cos(j*ts)]
                           for j in range(n0) for i in range(m0)])
            a = a.swapaxes(0,2).swapaxes(1,2).reshape(n,-1)
    return a


def fw0(m0, n0, c0, xs_norm, ts, funcnum=2):
    r"""Calculates the imperfection field `w_0` for a given input

    Parameters
    ----------
    m0 : int
        The number of terms along the meridian.
    n0 : int
        The number of terms along the circumference.
    c0 : np.ndarray
        The coefficients of the imperfection pattern.
    xs_norm : np.ndarray
        The meridian coordinate (`x`) normalized to be between ``0.`` and
        ``1.``.
    ts : np.ndarray
        The angles in radians representing the circumferential coordinate
        (`\theta`).
    funcnum : int, optional
        The function used for the approximation (see function :func:`.calc_c0`)

    Returns
    -------
    w0s : np.ndarray
        An array with the same shape of ``xs_norm`` containing the calculated
        imperfections.

    Notes
    -----
    The inputs ``xs_norm`` and ``ts`` must be of the same size.

    The inputs must satisfy ``c0.shape[0] == size*m0*n0``, where:

    - ``size=2`` if ``funcnum==1 or funcnum==2``
    - ``size=4`` if ``funcnum==3``

    """
    if xs_norm.shape != ts.shape:
        raise ValueError('xs_norm and ts must have the same shape')
    if funcnum==1:
        size = 2
    elif funcnum==2:
        size = 2
    elif funcnum==3:
        size = 4
    if c0.shape[0] != size*m0*n0:
        raise ValueError('Invalid c0 for the given m0 and n0!')
    try:
        import _fit_data
        w0s = _fit_data.fw0(m0, n0, c0, xs_norm.ravel(), ts.ravel(), funcnum)
    except:
        a = fa(m0, n0, xs_norm.ravel(), ts.ravel(), funcnum)
        w0s = a.dot(c0)
    return w0s.reshape(xs_norm.shape)


def transf_matrix(alphadeg, betadeg, gammadeg, x0, y0, z0):
    r"""Calculates the transformation matrix

    The transformation matrix `[T]` is used to transform a set of points
    from one coordinate system to another:

    .. math::
         [T] = \begin{bmatrix}
         cos(\beta)cos(\gamma) &
         sin(\alpha)sin(\beta)cos(\gamma) + cos(\alpha)sin(\gamma) &
         sin(\alpha)sin(\gamma) - cos(\alpha)sin(\beta)cos(\gamma) &
         \Delta x_0
         \\
         -cos(\beta)sin(\gamma) &
         cos(\alpha)cos(\gamma) - sin(\alpha)sin(\beta)sin(\gamma)&
         sin(\alpha)cos(\gamma) + cos(\alpha)sin(\beta)sin(\gamma) &
         \Delta y_0
         \\
         sin(\beta) &
         -sin(\alpha)cos(\beta) &
         cos(\alpha)cos(\beta) &
         \Delta z_0
         \\
               \end{bmatrix}

    Parameters
    ----------
    alphadeg : float
        Rotation around the x axis, in degrees.
    betadeg : float
        Rotation around the y axis, in degrees.
    gammadeg : float
        Rotation around the z axis, in degrees.
    x0 : float
        Translation along the x axis.
    y0 : float
        Translation along the y axis.
    z0 : float
        Translation along the z axis.

    Returns
    -------
    T : np.ndarray
        The 3 by 4 transformation matrix.

    """
    a = deg2rad(alphadeg)
    b = deg2rad(betadeg)
    g = deg2rad(gammadeg)
    return np.array([[cos(b)*cos(g),
                   (sin(a)*sin(b)*cos(g) + cos(a)*sin(g)),
                   (sin(a)*sin(g) - cos(a)*sin(b)*cos(g)), x0],
                  [-cos(b)*sin(g),
                   (cos(a)*cos(g) - sin(a)*sin(b)*sin(g)),
                   (sin(a)*cos(g) + cos(a)*sin(b)*sin(g)), y0],
                  [sin(b), -sin(a)*cos(b),  cos(a)*cos(b), z0]])


if __name__=='__main__':
    import matplotlib.pyplot as plt

    from _fit_data import fa

    path = r'C:\clones\desicos\desicos\conecylDB\files\dlr\degenhardt_2010_z25\degenhardt_2010_z25_msi_theta_z_imp.txt'
    m0 = 20
    n0 = 20
    c0, residues = calc_c0(path, m0=m0, n0=n0, sample_size=0.75)
    theta = np.linspace(-pi, pi, 1000)
    z = np.linspace(0, 1., 400)

    theta, z = np.meshgrid(theta, z, copy=False)
    a = fa(m0, n0, z.ravel(), theta.ravel(), funcnum=1)
    w = a.dot(c0).reshape(1000, 400)

    levels = np.linspace(w.min(), w.max(), 400)
    plt.contourf(theta, z, w.reshape(theta.shape), levels=levels)

    plt.gcf().savefig('plot.png', transparent=True,
                      bbox_inches='tight', pad_inches=0.05)



