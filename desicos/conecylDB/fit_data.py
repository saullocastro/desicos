import gc
from random import sample

import numpy as np
from numpy import sin, cos, pi

from desicos.logger import *
from desicos.constants import FLOAT

def best_fit_cylinder(path, R, H, save=True, errorRtol=1.e-9,
                      maxNumIter=1000):
    r'''Fit a best cylinder for a given set of measured data

    The routine will transform the points to a new coordinate system
    based on a best fit cylinder with radius ``R`` and height ``H``.
    The best fit is calculated using the least square method from SciPy
    (``scipy.optimize.leastsq``).

    Parameters
    ----------
    path : str or np.ndarray
        The path of the file containing the data. Can be a full path using
        ``r"C:\Temp\inputfile.txt"``, for example.
        The input file must have 3 columns "`x` `y` `z`" expressed
        in Cartesian coordinates.

        This input can also be a ``np.ndarray`` object, with `x`, `y`, `z`
        in each corresponding column.
    R : float
        The nominal radius of the cylinder, used as a first guess for the
        best-fit radius.
    H : float
        The nominal height of the cylinder.
    save : bool, optional
        Whether to save an ``"output_best_fit.txt"`` in the working directory.
        Default is ``True``.
    errorRtol : float, optional
        The error tolerance for the best-fit radius to stop the iterations.
    maxNumIter : int, optional
        The maximum number of iterations for the best-fit radius.

    Returns
    -------
    out : dict
        A Python dictionary with the entries:

        ``out['R_best_fit']`` : float
            The best-fit radius of the input sample.
        ``out['T']`` : np.ndarray
            The transformation matrix as a `3 \times 4` 2-D array.
        ``out['input_pts']`` : np.ndarray
            The input points in a `3 \times N` 2-D array.
        ``out['output_pts']`` : np.ndarray
            The transformed points in a `3 \times N` 2-D array.

    Examples
    --------

        >>> from desicos.conecylDB.fit_data import best_fit_cylinder
        >>> best_fit_cylinder(path, R, H)

    '''
    from scipy.optimize import leastsq
    if isinstance(path, np.ndarray):
        input_pts = path.T
    else:
        input_pts = np.loadtxt(path, unpack=True)

    if input_pts.shape[0] != 3:
        raise ValueError('Input does not have the format: "x, y, z"')

    pts = np.vstack((input_pts, np.ones_like(input_pts[0, :])))

    def fT(p):
        a, b, x0, y0, z0 = p
        if False:
            g = 0.
            # rotation in x, y, z
            T = np.array([[cos(b)*cos(g),
                           (sin(a)*sin(b)*cos(g) + cos(a)*sin(g)),
                           (sin(a)*sin(g) - cos(a)*sin(b)*cos(g))],
                          [-cos(b)*sin(g),
                           (cos(a)*cos(g) - sin(a)*sin(b)*sin(g)),
                           (sin(a)*cos(g) + cos(a)*sin(b)*sin(g))],
                          [sin(b), -sin(a)*cos(b),  cos(a)*cos(b)]])
        if True:
            # rotation in x, y
            T = np.array([[cos(b),  sin(a)*sin(b), -cos(a)*sin(b), x0],
                          [     0,         cos(a),         sin(a), y0],
                          [sin(b), -sin(a)*cos(b),  cos(a)*cos(b), z0]])
        return T

    i = 0
    while i <= maxNumIter:
        i += 1
        def calc_dist(p, pts):
            T = fT(p)
            xn, yn, zn = T.dot(pts)
            dz = zn

            # point below the bottom edge
            dz[zn < 0] = -dz[zn < 0]

            # point inside the cylinder
            dz[(zn >= 0) & (zn <= H)] *= 0

            # point above the top edge
            dz[zn > H] = H - dz[zn > H]


            dr = R - (xn**2 + yn**2)**0.5
            dist = (dr**2 + dz**2)**0.5
            return dist

        # initial guess for the optimization variables
        # the variables are alpha, beta, x0, y0, z0
        x, y, z = input_pts
        p = [0., 0., x.mean(), y.mean(), z.mean()]

        # performing the leastsq analysis
        popt, pcov = leastsq(func=calc_dist, x0=p, args=(pts,),
                             ftol=1.e-12, xtol=1.e-12, maxfev=1000000)
        T = fT(popt)
        output_pts = T.dot(pts)
        x, y, z = output_pts
        R_best_fit = ((x**2 + y**2)**0.5).mean()
        errorR = abs(R_best_fit - R)/R_best_fit

        if errorR < errorRtol:
            break
        else:
            R = R_best_fit
    else:
        warn('The maximum number of iterations was achieved!')

    log('')
    log('Transformation matrix:\n{0}'.format(T))
    log('')
    log('Best fit radius: {0}'.format(R_best_fit))
    log('    errorR: {0}, numiter: {1}'.format(errorR, i))
    log('')
    log('Z versor: {0}*i + {1}*j + {2}*k'.format(*T[-1,:-1]))
    log('')
    log('x0, y0, z0: {0}, {1}, {2}'.format(*T[:,-1]))
    log('')

    if save:
        np.savetxt('output_best_fit.txt', np.vstack((x, y, z)).T)

    return dict(R_best_fit=R_best_fit,
                input_pts=input_pts,
                output_pts=output_pts,
                T=T)

def calc_c0(path, m0=40, n0=40, funcnum=2, inverted_z=False,
            sample_size=None, maxmem=8):
    r'''Find the coefficients that best fit the `w_0` imperfection.

    The measured data will be fit using one of the following functions,
    selected using the ``funcnum`` parameter:

    1)

    .. math::
        w_0 = \sum_{i=1}^{m_0}{ \sum_{j=0}^{n_0}{
                 c_{ij}^a sin{b_z} sin{b_\theta}
                +c_{ij}^b sin{b_z} cos{b_\theta} }}

    2) (default)

    .. math::
        w_0 = \sum_{i=0}^{m_0}{ \sum_{j=0}^{n_0}{
                c_{ij}^a cos{b_z} sin{b_\theta}
                +c_{ij}^b cos{b_z} cos{b_\theta} }}

    3)

    .. math::
        w_0 = \sum_{i=0}^{m_0}{ \sum_{j=0}^{n_0}{
                 c_{ij}^a sin{b_z} sin{b_\theta}
                +c_{ij}^b sin{b_z} cos{b_\theta}
                +c_{ij}^c cos{b_z} sin{b_\theta}
                +c_{ij}^d cos{b_z} cos{b_\theta} }}

    where:

    .. math::
        b_z = i \pi \frac z H_{points}

        b_\theta = j \theta

    where `H_{points}` represents the difference between the maximum and
    the minimum `z` values in the imperfection file.

    The approximation can be written in matrix form as:

    .. math::
        w_0 = [g] \{c\}

    where `[g]` carries the base functions and `{c}` the respective
    amplitudes. The solution consists on finding the best `{c}` that minimizes
    the least-square error between the measured imperfection pattern and the
    `w_0` function.

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
    inverted_z : bool, optional
        The :ref:`default coordinate system <default_coordsys>` has the
        `z` axis starting
        at the center of the bottom circumference pointing to the top.
        If the `z` axis of the imperfection file is inverted this boolean
        should be ``True``.
        Default is ``False``.
    sample_size : int or None, optional
        An in  specifying how many points of the imperfection file
        should be used. If the default ``None`` is used
        all points file will be used in the computations.
    maxmem : int, optional
        Maximum RAM memory in GB allowed to compute the base functions.
        The ``scipy.interpolate.lstsq`` will go beyond this limit.

    Returns
    -------
    out : np.ndarray
        A 1-D array with the best-fit coefficients.

    '''
    from scipy.linalg import lstsq

    if isinstance(path, np.ndarray):
        input_pts = path
        path = 'unmamed.txt'
    else:
        input_pts = np.loadtxt(path)

    if input_pts.shape[1] != 3:
        raise ValueError('Input does not have the format: "theta, z, imp"')

    log('Finding w0 coefficients for {0}, using funcnum {1}'.format(
        str(os.path.basename(path)), funcnum))

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
    zs = input_pts[:, 1]
    w0pts = input_pts[:, 2]
    #NOTE using `H_measured` did not allow a good fitting result
    #zs /= H_measured
    zs = (zs - zs.min())/(zs.max() - zs.min())
    if inverted_z:
        #TODO
        zs *= -1
        zs += 1

    a = fa(m0, n0, zs, ts, funcnum)

    log('Base functions calculated', level=1)
    c, residues, rank, s = lstsq(a, w0pts)
    log('Finished scipy.linalg.lstsq', level=1)

    return c, residues

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
        The function used for the approximation (see
        :func:`desicos.conecylDB.fit_data.calc_c0`)

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
    r"""Calculates the imperfection field `w_0` for a given input.

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
        The function used for the approximation (see the ``calc_c0`` function)

    Notes
    -----
    The inputs ``xs_norm`` and ``ts`` must be of the same size.

    If ``funcnum==1 or funcnum==2`` then ``size=2``, if ``funcnum==3`` then
    ``size=4`` and the inputs must satisfy ``c0.shape[0] == size*m0*n0``.

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


if __name__=='__main__':
    import matplotlib.pyplot as plt

    from _fit_data import fa

    path = r'C:\clones\desicos\desicos\conecylDB\files\dlr\degenhardt_2010_z25\degenhardt_2010_z25_msi_theta_z_imp.txt'
    m0 = 20
    n0 = 20
    c, residues = calc_c0(path, m0=m0, n0=n0, sample_size=0.75)
    theta = np.linspace(-pi, pi, 1000)
    z = np.linspace(0, 1., 400)

    theta, z = np.meshgrid(theta, z, copy=False)
    a = fa(m0, n0, z.ravel(), theta.ravel(), funcnum=1)
    w = a.dot(c).reshape(1000, 400)

    levels = np.linspace(w.min(), w.max(), 400)
    plt.contourf(theta, z, w.reshape(theta.shape), levels=levels)

    plt.gcf().savefig('plot.png', transparent=True,
                      bbox_inches='tight', pad_inches=0.05)



