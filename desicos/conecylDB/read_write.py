import numpy as np

from desicos.constants import *
from desicos.logger import *
from desicos.conecylDB.fit_data import best_fit_cylinder

def read_theta_z_imp(path,
                     H_measured=None,
                     stretch_H=False,
                     z_offset_bot=None):
    r"""Read an imperfection file in the format `\theta`, `z`, imperfection.

    Where the angles `\theta` are given in radians.

    Example of input file:

        theta1 z1 imp1
        theta2 z2 imp2
        ...
        thetan zn impn

    Parameters
    ----------
    path : str or numpy.ndarray
        The path to the imperfection file, or a ``numpy.ndarray``, with
        three columns.
    H_measured : float, optional
        The height of the measured test specimen.
    stretch_H : bool, optional
        Tells if the height of the measured points, which is usually smaller
        than the height of the test specimen, should be stretched to fill
        the whole test specimen. If not, the points will be placed in the
        middle or using the offset given by ``z_offset_bot`` and the
        area not covered by the measured points will be interpolated
        using the closest available points (the imperfection
        pattern will look like there was an extrusion close to the edges).
    z_offset_bot : float, optional
        The offset that should be used from the bottom of the measured points
        to the bottom of the test specimen.
        Default is ``None``.

    Returns
    -------
    mps : numpy.ndarray
        A 2-D array with `\theta`, `z`, `value` in the first, second
        and third columns, respectively.
    offset_mps : numpy.ndarray
        A 2-D array similar to ``mps`` but offset according to place the
        measured data according to the inputs given.
    norm_mps : numpy.ndarray
        A 2-D array similar to ``mps`` but normalized in `z` by the height.

    """
    # user warnings
    if stretch_H:
        if z_offset_bot:
            warn('Because of the stretch_H option,\n\t' +
                 'consider setting "z_offset_bot" to None')
    # reading the imperfection file
    if isinstance(path, np.ndarray):
        log('Reading imperfection array: ...')
        mps = path
    else:
        log('Reading imperfection file: {0} ...'.format(path))
        mps = np.loadtxt(path, dtype=FLOAT)

    # measuring model dimensions
    z_min = mps[:, 1].min()
    z_max = mps[:, 1].max()
    z_center  = (z_max + z_min)/2.
    H_points  = (z_max - z_min)
    H_model = H_points
    if not H_measured:
        H_measured = H_points
        warn('The cylinder height of the test specimen assumed\n\t' +
             'to be {0:1.2f}'.format(H_measured))

    # calculating default z_offset_bot
    if not z_offset_bot:
        if stretch_H:
            z_offset_bot = 0.
        else:
            z_offset_bot = (H_measured - H_points) / 2.
    offset_z = z_offset_bot - z_min

    log('H_points       : {0}'.format(H_points))
    log('H_measured     : {0}'.format(H_measured))
    log('z_min          : {0}'.format(z_min))
    log('z_max          : {0}'.format(z_max))
    log('offset_z       : {0}'.format(offset_z))

    offset_mps = mps.copy()
    offset_mps[:, 1] += offset_z

    norm_mps = offset_mps.copy()
    if stretch_H:
        norm_mps[:, 1] /= H_points
    else:
        norm_mps[:, 1] /= H_measured

    return mps, offset_mps, norm_mps

def read_xyz(path,
             alphadeg_measured= None,
             R_measured= None,
             H_measured= None,
             stretch_H= False,
             z_offset_bot= None,
             r_TOL= 1.):
    r"""Read an imperfection file in the format `x`, `y`, `z`.

    Example of input file:

        x1 y1 z1
        x2 y2 z2
        ...
        xn yn zn

    Parameters
    ----------
    path : str or np.ndarray
        The path to the imperfection file, or a ``numpy.ndarray``, with
        three columns.
    alphadeg_measured : float, optional
        The semi-vertex angle of the measured sample.
    R_measured : float, optional
        The radius of the measured test specimen.
    H_measured : float, optional
        The height of the measured test specimen.
    stretch_H : bool, optional
        Tells if the height of the measured points, which is usually smaller
        than the height of the test specimen, should be stretched to fill
        the whole test specimen. If not, the points will be placed in the
        middle or using the offset given by ``z_offset_bot`` and the
        area not covered by the measured points will be interpolated
        using the closest available points (the imperfection
        pattern will look like there was an extrusion close to the edges).
    z_offset_bot : float, optional
        The offset that should be used from the bottom of the measured points
        to the bottom of the test specimen.
        Default is ``None``.
    r_TOL : float, optional
        The tolerance used to ignore points farer than ``r_TOL*R_measured``,
        given in percent. Default is ``1`` %.

    Returns
    -------
    mps : numpy.ndarray
        A 2-D array with `x`, `y`, `z` in the first, second
        and third columns, respectively.
    offset_mps : numpy.ndarray
        A 2-D array similar to ``mps`` but with the z coordinates offset
        according to the inputs given.
    norm_mps : numpy.ndarray
        A 2-D array similar to ``mps`` but normalized in `z` by the height
        and in `x` and `y` by the radius.

    """
    # user warnings
    if stretch_H:
        if z_offset_bot:
            warn('Because of the stretch_H option,\n\t' +
                 'consider setting "z_offset_bot" to None')
    # reading the imperfection file
    if isinstance(path, np.ndarray):
        mps = path
    else:
        mps = np.loadtxt(path, dtype=FLOAT)
    r = np.sqrt(mps[:, 0]**2 + mps[:, 1]**2)
    # measuring model dimensions
    if R_measured == None:
        R   = np.average(r)
        warn('The cylinder average radius of the measured points\n\t' +
             'assumed to be {0:1.2f}'.format(R_measured))
    else:
        R = R_measured
    z_min = mps[:, 2].min()
    z_max = mps[:, 2].max()
    z_center  = (z_max + z_min)/2.
    H_points  = (z_max - z_min)
    log('R_average     : {0}'.format(np.average(r)))
    log('R_measured     : {0}'.format(R_measured))
    # applying user inputs
    H_model = H_points
    if not H_measured:
        H_measured = H_points
        warn('The cylinder height of the measured points assumed\n\t' +
             'to be {0:1.2f}'.format(H_measured))
    # calculating default z_offset_bot
    if not z_offset_bot:
        if stretch_H:
            z_offset_bot = 0.
        else:
            z_offset_bot = (H_measured - H_points) / 2.
    offset_z = z_offset_bot - z_min
    log('H_points       : {0}'.format(H_points))
    log('H_measured     : {0}'.format(H_measured))
    log('z_min          : {0}'.format(z_min))
    log('z_max          : {0}'.format(z_max))
    log('offset_z       : {0}'.format(offset_z))
    r_TOL_min = (R * (1-r_TOL/100.))
    r_TOL_max = (R * (1+r_TOL/100.))
    cond = np.all(np.array((r > r_TOL_max,
                            r < r_TOL_min)), axis=0)
    skept = mps[cond]
    log('Skipping {0} points'.format(len(skept)))
    mps = mps[np.logical_not(cond)]
    offset_mps = mps.copy()
    offset_mps[:, 2] += offset_z
    norm_mps = offset_mps.copy()
    norm_mps[:, 0] /= R
    norm_mps[:, 1] /= R
    if stretch_H:
        norm_mps[:, 2] /= H_points
    else:
        norm_mps[:, 2] /= H_measured

    return mps, offset_mps, norm_mps

def xyz2thetazimp(path, alphadeg_measured, R_measured, H_measured,
                  use_best_fit=True,
                  stretch_H=False,
                  z_offset_bot=None,
                  r_TOL=1.,
                  save=True,
                  fmt='%.18e'):
    r"""Transforms an imperfection file from the format "`x` `y` `z`"
    to the format "`\theta` `z` `imp`".

    The input file::

        x1 y1 z1
        x2 y2 z2
        ...
        xn yn zn

    Is transformed to a file::

        theta1 z1 imp1
        theta2 z2 imp2
        ...
        thetan zn impn

    Parameters
    ----------
    path : str
        The path to the imperfection file.
    alphadeg_measured : float
        The semi-vertex angle of the measured sample
        (it is ``0.`` for a cylinder).
    R_measured : float
        The radius of the measured test specimen.
    H_measured : float
        The height of the measured test specimen.
    use_best_fit : bool, optional
        If ``True`` it overwrites the values for: ``R_measured`` (for
        cylinders and cones) and ``z_offset_bot`` (for cones), which are
        automatically determined from the `best_fitting` routine.
        Default is ``True``.
    z_offset_bot : float, optional
        The offset that should be used from the bottom of the measured points
        to the bottom of the test specimen.
        Default is ``None``.
    r_TOL : float, optional
        The tolerance used to ignore points farer than ``r_TOL*R_measured``,
        given in percent. Default is ``1`` %.
    save : bool, optional
        If the returned array ``mps`` should also be saved to a ``.txt`` file.
        Default is ``True``.
    fmt : str or sequence of strs, optional
        See ``numpy.savetxt()`` documentation for more details.

    Returns
    -------
    mps : numpy.ndarray
        A 2-D array with `\theta`, `z`, `imp` in the first, second
        and third columns, respectively.

    """
    if use_best_fit:
        log('Finding the best-fit ...')
        if alphadeg_measured==0.:
            ans = best_fit_cylinder(path, R_measured, H_measured, save=False)
            R_measured = ans['R_best_fit']
            x, y, z = ans['output_pts']
            z -= z.min()
            H_points = z.max() - z.min()
            if z_offset_bot:
                z += z_offset_bot
            else:
                z += (H_measured - H_points)/2. # centralizes the points
    else:
        log('Reading the data ...')
        d, data, d = read_xyz(path, alphadeg_measured, R_measured,
                              H_measured, None, z_offset_bot, r_TOL)
        x, y, z = data.T

    r = np.sqrt(x**2 + y**2)
    theta = np.arctan2(y, x)
    imp = r - R_measured
    log('Minimum imperfection: {0}'.format(imp.min()))
    log('Maximum imperfection: {0}'.format(imp.max()))

    mps = np.vstack((theta, z, imp)).T
    if save:
        outpath = '.'.join(path.split('.')[:-1]) + '_theta_z_imp.txt'
        np.savetxt(outpath, mps, fmt=fmt)

    return mps

def xyzthick2thetazthick(path, alphadeg_measured, R_measured, H_measured,
                         use_best_fit=True,
                         stretch_H=False,
                         z_offset_bot=None,
                         r_TOL=1.,
                         save=True,
                         fmt='%.18e'):
    r"""Transforms an imperfection file from the format: "`x` `y` `z` `thick`"
    to the format "`\theta` `z` `thick`".

    The input file::

        x1 y1 z1 thick1
        x2 y2 z2 thick2
        ...
        xn yn zn thickn

    Is transformed in a file::

        theta1 z1 thick1
        theta2 z2 thick2
        ...
        thetan zn thickn

    Parameters
    ----------
    path : str
        The path to the imperfection file.
    alphadeg_measured : float
        The semi-vertex angle of the measured sample
        (it is ``0.`` for a cylinder).
    R_measured : float
        The radius of the measured test specimen.
    H_measured : float
        The height of the measured test specimen.
    use_best_fit : bool, optional
        If ``True`` it overwrites the values for: ``R_measured`` (for
        cylinders and cones) and ``z_offset_bot`` (for cones), which are
        automatically determined from the `best_fitting` routine.
        Default is ``True``.
    z_offset_bot : float, optional
        The offset that should be used from the bottom of the measured points
        to the bottom of the test specimen.
        Default is ``None``.
    r_TOL : float, optional
        The tolerance used to ignore points farer than ``r_TOL*R_measured``,
        given in percent. Default is ``1`` %.
    save : bool, optional
        If the returned array ``mps`` should also be saved to a ``.txt`` file.
        Default is ``True``.
    fmt : str or sequence of strs, optional
        See ``numpy.savetxt()`` documentation for more details.

    Returns
    -------
    mps : numpy.ndarray
        A 2-D array with `\theta`, `z`, `imp` in the first, second
        and third columns, respectively.

    """
    inputa = np.loadtxt(path)
    if inputa.shape[1] != 4:
        raise ValueError('Input file does not have the format: "x y z thick"')

    xyz = inputa[:, :3]
    thick = inputa[:, 3]

    if use_best_fit:
        log('Finding the best-fit ...')
        if alphadeg_measured==0.:
            ans = best_fit_cylinder(xyz, R_measured, H_measured, save=False)
            R_measured = ans['R_best_fit']
            x, y, z = ans['output_pts']
            z -= z.min()
            H_points = z.max() - z.min()
            if z_offset_bot:
                z += z_offset_bot
            else:
                z += (H_measured - H_points)/2. # centralizes the points
    else:
        log('Reading the data ...')
        d, data, d = read_xyz(xyz, alphadeg_measured, R_measured,
                              H_measured, False, z_offset_bot, r_TOL)
        x, y, z = data.T

    theta = np.arctan2(y, x)
    log('Minimum thickness: {0}'.format(thick.min()))
    log('Maximum thickness: {0}'.format(thick.max()))

    mps = np.vstack((theta, z, thick)).T
    if save:
        outpath = '.'.join(path.split('.')[:-1]) + '_theta_z_thick.txt'
        np.savetxt(outpath, mps, fmt=fmt)

    return mps
