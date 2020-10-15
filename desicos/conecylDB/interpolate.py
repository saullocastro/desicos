r"""
Interpolate (:mod:`desicos.conecylDB.interpolate`)
==================================================

.. currentmodule:: desicos.conecylDB.interpolate

This module includes some interpolation utilities that will be used in other
modules.

"""
from __future__ import absolute_import
from collections import Iterable

import numpy as np
from numpy import sin, cos, tan

from desicos.logger import *
from desicos.constants import FLOAT
from .read_write import read_theta_z_imp


def nearest_neighbors(x, y, k):
    """inspired by
    https://stackoverflow.com/a/15366296/832621
    and
    https://stackoverflow.com/a/6913178/832621
    """
    x, y = map(np.asarray, (x, y))
    y = y.copy()
    y_idx = np.arange(len(y))
    nearest_neighbor = np.empty((len(x), k), dtype=np.intp)
    distances = np.empty((len(x), k), dtype=float)
    #TODO after numpy 1.8 we can use np.argpartition(dist, kth=k-1)
    #TODO ABAQUS 2020 comes with scipy, then we can use cKDTree
    for j, xj in enumerate(x) :
        dist = ((y - xj[None, :])**2).sum(axis=1)
        for i in range(k):
            idx = np.argmin(dist)
            nearest_neighbor[j, i] = idx
            distances[j, i] = dist[idx]
            dist[idx] = 1e6
    distances = np.sqrt(distances)
    return distances, nearest_neighbor


def inv_weighted(data, mesh, ncp=5, power_parameter=2):
    r"""Interpolates the values taken at one group of points into
    another using an inverse-weighted algorithm

    In the inverse-weighted algorithm a number of `n_{CP}` measured points
    of the input parameter ``data`` that are closest to a given node in
    the input parameter ``mesh`` are found and the imperfection value of
    this node (represented by the normal displacement `{w_0}_{node}`) is
    calculated as follows:

    .. math::
        {w_0}_{node} = \frac{\sum_{i}^{n_{CP}}{{w_0}_i\frac{1}{w_i}}}
                            {\sum_{i}^{n_{CP}}{\frac{1}{w_i}}}

    where `w_i` is the inverse weight of each measured point, calculated as:

    .. math::
        w_i = \left[(x_{node}-x_i)^2+(y_{node}-y_i)^2+(z_{node}-z_i)^2
              \right]^p

    with `p` being a power parameter that when increased will increase the
    relative influence of a closest point.

    Parameters
    ----------
    data : numpy.ndarray, shape (N, ndim+1)
        The data or an array containing the imperfection file. The values
        to be interpolated must be in the last column.
    mesh : numpy.ndarray, shape (M, ndim)
        The new coordinates where the values will be interpolated to.
    ncp : int, optional
        Number of closest points used in the inverse-weighted interpolation.
    power_parameter : float, optional
        Power of inverse weighted interpolation function.

    Returns
    -------
    ans : numpy.ndarray
        A 1-D array with the interpolated values. The size of this array
        is ``mesh.shape[0]``.

    """
    if mesh.shape[1] != data.shape[1]-1:
        raise ValueError('Invalid input: mesh.shape[1] != data.shape[1]')

    log('Interpolating... ')
    dist, indices = nearest_neighbors(mesh, data[:, :-1], k=ncp)

    # avoiding division by zero
    dist[dist < 1.e-15] = 1.e-15
    # fetching the imperfection
    imp = data[:, -1][indices]
    # weight calculation
    total_weight = np.sum(1./(dist**power_parameter), axis=1)
    weight = 1./(dist**power_parameter)
    # computing the new imp
    imp_new = np.sum(imp*weight, axis=1)/total_weight

    log('Interpolation completed!')

    return dist, imp_new


def interp(x, xp, fp, left=None, right=None, period=None):
    """
    One-dimensional linear interpolation

    Returns the one-dimensional piecewise linear interpolant to a function
    with given values at discrete data-points.

    Parameters
    ----------
    x : array_like
        The x-coordinates of the interpolated values.
    xp : 1-D sequence of floats
        The x-coordinates of the data points, must be increasing if argument
        ``period`` is not specified. Otherwise, ``xp`` is internally sorted
        after normalizing the periodic boundaries with ``xp = xp % period``.
    fp : 1-D sequence of floats
        The y-coordinates of the data points, same length as ``xp``.
    left : float, optional
        Value to return for ``x < xp[0]``, default is ``fp[0]``.
    right : float, optional
        Value to return for ``x > xp[-1]``, default is ``fp[-1]``.
    period : float, optional
        A period for the x-coordinates. This parameter allows the proper
        interpolation of angular x-coordinates. Parameters ``left`` and
        ``right`` are ignored if ``period`` is specified.

    Returns
    -------
    y : {float, ndarray}
        The interpolated values, same shape as ``x``.

    Raises
    ------
    ValueError
        If ``xp`` and ``fp`` have different length
        If ``xp`` or ``fp`` are not 1-D sequences
        If ``period==0``

    Notes
    -----
    Does not check that the x-coordinate sequence ``xp`` is increasing.
    If ``xp`` is not increasing, the results are nonsense.
    A simple check for increasing is::

        np.all(np.diff(xp) > 0)


    Examples
    --------
    >>> xp = [1, 2, 3]
    >>> fp = [3, 2, 0]
    >>> interp(2.5, xp, fp)
    1.0
    >>> interp([0, 1, 1.5, 2.72, 3.14], xp, fp)
    array([ 3. ,  3. ,  2.5 ,  0.56,  0. ])
    >>> UNDEF = -99.0
    >>> interp(3.14, xp, fp, right=UNDEF)
    -99.0

    Plot an interpolant to the sine function:

    >>> x = np.linspace(0, 2*np.pi, 10)
    >>> y = np.sin(x)
    >>> xvals = np.linspace(0, 2*np.pi, 50)
    >>> yinterp = interp(xvals, x, y)
    >>> import matplotlib.pyplot as plt
    >>> plt.plot(x, y, 'o')
    [<matplotlib.lines.Line2D object at 0x...>]
    >>> plt.plot(xvals, yinterp, '-x')
    [<matplotlib.lines.Line2D object at 0x...>]
    >>> plt.show()

    Interpolation with periodic x-coordinates:

    >>> x = [-180, -170, -185, 185, -10, -5, 0, 365]
    >>> xp = [190, -190, 350, -350]
    >>> fp = [5, 10, 3, 4]
    >>> interp(x, xp, fp, period=360)
    array([7.5, 5., 8.75, 6.25, 3., 3.25, 3.5, 3.75])

    """
    if period is None:
        return np.interp(x, xp, fp, left, right)
    else:
        if period==0:
            raise ValueError('Argument `period` must be a non-zero value')
        period = abs(period)
        if not isinstance(x, Iterable):
            x = [x]
        x = np.asarray(x)
        xp = np.asarray(xp)
        fp = np.asarray(fp)
        if xp.ndim != 1 or fp.ndim != 1:
            raise ValueError('Data points must be 1-D sequences')
        if xp.shape[0] != fp.shape[0]:
            raise ValueError('Inputs `xp` and `fp` must have the same shape')
        # eliminating discontinuity between periods
        x = x % period
        xp = xp % period
        asort_xp = np.argsort(xp)
        xp = xp[asort_xp]
        fp = fp[asort_xp]
        xp = np.concatenate((xp[-1:]-period, xp, xp[0:1]+period))
        fp = np.concatenate((fp[-1:], fp, fp[0:1]))
        return np.interp(x, xp, fp)


def interp_theta_z_imp(data, mesh, alphadeg, H_measured, H_model, R_bottom,
        stretch_H=False, z_offset_bot=None, rotatedeg=0., num_sub=10, ncp=5,
        power_parameter=2, ignore_bot_h=None, ignore_top_h=None, T=None):
    r"""Interpolates a data set in the `\theta, z, imp` format

    This function uses the inverse-weighted algorithm (:func:`.inv_weighted`).

    Parameters
    ----------
    data : str or numpy.ndarray, shape (N, 3)
        The data or an array containing the imperfection file in the `(\theta,
        Z, imp)` format.
    mesh : numpy.ndarray, shape (M, 3)
        The mesh coordinates `(x, y, z)` where the values will be interpolated
        to.
    alphadeg : float
        The cone semi-vertex angle in degrees.
    H_measured : float
        The total height of the measured test specimen, including eventual
        resin rings at the edges.
    H_model : float
        The total height of the new model, including eventual resin rings at
        the edges.
    R_bottom : float
        The radius of the model taken at the bottom edge.
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
    rotatedeg : float, optional
        Rotation angle in degrees telling how much the imperfection pattern
        should be rotated about the `X_3` (or `Z`) axis.
    num_sub : int, optional
        The number of sub-sets used during the interpolation. The points
        are divided in sub-sets to increase the algorithm's efficiency.
    ncp : int, optional
        Number of closest points used in the inverse-weighted interpolation.
    power_parameter : float, optional
        Power of inverse weighted interpolation function.
    ignore_bot_h : None or float, optional
        Nodes close to the bottom edge are ignored according to this
        meridional distance.
    ignore_top_h : None or float, optional
        Nodes close to the top edge are ignored according to this meridional
        distance.
    T : None or np.ndarray, optional
        A transformation matrix (cf. :func:`.transf_matrix`) required when the
        mesh is not in the :ref:`default coordinate system <figure_conecyl>`.

    Returns
    -------
    ans : numpy.ndarray
        An array with M elements containing the interpolated values.

    """
    if not isinstance(data, np.ndarray):
        d, d, data = read_theta_z_imp(path=data,
                                      H_measured=H_measured,
                                      stretch_H=stretch_H,
                                      z_offset_bot=z_offset_bot)
    else:
        if stretch_H:
            H_points = data[:, 1].max() - data[:, 1].min()
            data[:, 1] /= H_points
        else:
            data[:, 1] /= H_measured

    if data.shape[1] != 3:
        raise ValueError('data must have shape (N, 3)')

    if mesh.shape[1] != 3:
        raise ValueError('Mesh must have shape (M, 3)')

    data3D = np.zeros((data.shape[0], 4), dtype=FLOAT)

    if rotatedeg:
        data[:, 0] += np.deg2rad(rotatedeg)

    z = data[:, 1]
    z *= H_model

    alpharad = np.deg2rad(alphadeg)
    tana = tan(alpharad)

    def r_local(z):
        return R_bottom - z*tana

    data3D[:, 0] = r_local(z)*cos(data[:, 0])
    data3D[:, 1] = r_local(z)*sin(data[:, 0])
    data3D[:, 2] = z
    data3D[:, 3] = data[:, 2]

    if T is not None:
        tmp = np.vstack((mesh.T, np.ones((1, mesh.shape[0]))))
        mesh = np.dot(T, tmp).T
        del tmp
    dist, ans = inv_weighted(data3D, mesh, ncp=ncp, power_parameter=power_parameter)

    z_mesh = mesh[:, 2]
    if ignore_bot_h is not None:
        ans[(z_mesh - z_mesh.min()) <= ignore_bot_h] = 0.
    if ignore_top_h is not None:
        ans[(z_mesh.max() - z_mesh) <= ignore_top_h] = 0.

    return ans


if __name__=='__main__':
    a = np.array([[1.1, 1.2, 10],
                  [1.2, 1.2, 10],
                  [1.3, 1.3, 10],
                  [1.4, 1.3, 10],
                  [1.5, 1.3, 10],
                  [2.6, 2.3, 5],
                  [2.7, 2.3, 5],
                  [2.6, 2.1, 5],
                  [2.7, 2.1, 5],
                  [2.8, 2.2, 5],
                  [2.8, 2.2, 5],
                  [5.6, 5.3, 20],
                  [5.7, 5.3, 20],
                  [5.6, 5.1, 20],
                  [5.7, 5.1, 20],
                  [5.8, 5.2, 20],
                  [5.8, 5.2, 20]])

    b = np.array([[1., 1.],
                  [2., 2.],
                  [4., 4.],
                  [5., 5.]])

    print(inv_weighted(a, b, ncp=10))

