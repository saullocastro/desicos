r"""
Interpolate (:mod:`desicos.conecylDB.interpolate`)
==================================================

.. currentmodule:: desicos.conecylDB.interpolate

This module includes some interpolation utilities that will be used in other
modules.

"""
import os
import __main__

import numpy as np
from numpy import sin, cos, tan

from desicos.logger import *
from desicos.constants import FLOAT
from read_write import read_theta_z_imp

def inv_weighted(data, mesh, num_sub, col, ncp=5, power_parameter=2):
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

    where `w_i` is the imperfection at each measured point, calculated as:

    .. math::
        w_i = \left[(x_{node}-x_i)^2+(y_{node}-y_i)^2+(z_{node}-y_i)^2
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
    num_sub : int
        The number of sub-sets used during the interpolation. The points
        are divided in sub-sets to increase the algorithm's efficiency.
    col : int
        The index of the column to be used in order to divide the data
        in sub-sets. Note that the first column index is ``0``.
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
    num_sub = int(num_sub)
    mesh_size = mesh.shape[0]

    # memory control
    mem_limit = 1024*1024*1024*8*2    # 2 GB
    mem_entries = int(mem_limit / 64) # if float64 is used
    sec_size = int(mesh_size/num_sub)
    while sec_size**2*10 > mem_entries:
        num_sub +=1
        sec_size = int(mesh_size/num_sub)
        if sec_size**2*10 <= mem_entries:
            warn('New num_sub: {0}'.format(int(mesh_size/float(sec_size))))
            break

    mesh_seq = np.arange(mesh.shape[0])

    mesh_argsort = np.argsort(mesh[:, col])
    mesh_seq = mesh_seq[mesh_argsort]
    back_argsort = np.argsort(mesh_seq)

    mesh = np.asarray(mesh[mesh_argsort], order='F')

    length = mesh[:, col].max() - mesh[:, col].min()

    data = np.asarray(data[np.argsort(data[:, col])], order='F')

    ans = np.zeros(mesh.shape[0], dtype=mesh.dtype)

    # max_num_limits defines how many times the log will print
    # "processed ... out of ... entries"
    max_num_limits = 10
    for den in range(max_num_limits, 0, -1):
        if num_sub % den == 0:
            limit = int(num_sub/den)
            break

    for i in range(num_sub+1):
        i_inf = sec_size*i
        i_sup = sec_size*(i+1)

        if i % limit == 0:
            log('\t processed {0:7d} out of {1:7d} entries'.format(
                  min(i_sup, mesh_size), mesh_size))
        sub_mesh = mesh[i_inf : i_sup]
        if not np.any(sub_mesh):
            continue
        inf = sub_mesh[:, col].min()
        sup = sub_mesh[:, col].max()

        tol = 0.03
        if i == 0 or i == num_sub:
            tol = 0.06

        while True:
            cond1 = data[:, col] >= inf - tol*length
            cond2 = data[:, col] <= sup + tol*length
            cond = np.all(np.array((cond1, cond2)), axis=0)
            sub_data = data[cond]
            if not np.any(sub_data):
                tol += 0.01
            else:
                break

        dist = np.subtract.outer(sub_mesh[:, 0], sub_data[:, 0])**2
        for j in range(1, sub_mesh.shape[1]):
            dist += np.subtract.outer(sub_mesh[:, j], sub_data[:, j])**2
        asort = np.argsort(dist, axis=1)
        lenn = sub_mesh.shape[0]
        lenp = sub_data.shape[0]
        asort_mesh = asort + np.meshgrid(np.arange(lenn)*lenp,
                                         np.arange(lenp))[0].transpose()
        # getting the distance of the closest points
        dist_cp = np.take(dist, asort_mesh[:, :ncp])
        # avoiding division by zero
        dist_cp[(dist_cp==0)] == 1.e-12
        # fetching the imperfection of the sub-data
        imp = sub_data[:, -1]
        # taking only the imperfection of the closest points
        imp_cp = np.take(imp, asort[:, :ncp])
        # weight calculation
        total_weight = np.sum(1./(dist_cp**power_parameter), axis=1)
        weight = 1./(dist_cp**power_parameter)
        # computing the new imp
        imp_new = np.sum(imp_cp*weight, axis=1)/total_weight
        # updating the answer array
        ans[i_inf : i_sup] = imp_new

    ans = ans[back_argsort]

    log('Interpolation completed!')

    return ans

def interp_polar(t, tp, fp, degrees=False, smooth=False):
    """One-dimensional linear interpolation for polar coordinates

    This function supports angular inputs at any range, and uses a
    spatial-based interpolation to overcome angle discontinuities.

    Parameters
    ----------
    t : np.ndarray
        The angular coordinates of the interpolated values.
    tp : np.ndarray
        The angular coordinates of the data points.
    fp : np.ndarray
        The response being interpolated, same length as ``tp``.
    degrees : bool, optional
        If the input angles are in degrees.
    smooth : bool, optional
        If ``True`` uses the linear distance instead of the arc distance to
        compute the linear interpolation, resulting in a smoothed pattern.

    Returns
    -------
    f : {float, ndarray}
        The interpolated values, same shape as `t`.

    """
    r = 1.e3 # any arbitrary float within the machine limits can be used here
    t = np.asarray(t)
    tp = np.asarray(tp)
    fp = np.asarray(fp)
    if degrees:
        t = np.deg2rad(t)
        tp = np.deg2rad(tp)
    x = r*np.cos(t)
    y = r*np.sin(t)
    xp = r*np.cos(tp)
    yp = r*np.sin(tp)
    dist = np.subtract.outer(x, xp)**2
    dist += np.subtract.outer(y, yp)**2
    asort = np.argsort(dist, axis=1)
    sdist = np.sort(dist, axis=1)
    fp1 = fp[asort[:,0]]
    fp2 = fp[asort[:,1]]
    if smooth:
        # linear distance
        d1 = sdist[:,0]
        d2 = sdist[:,1]
    else:
        # arc distance
        x1 = xp[asort[:,0]]
        x2 = xp[asort[:,1]]
        y1 = yp[asort[:,0]]
        y2 = yp[asort[:,1]]
        def calc_arc(x1, y1, x2, y2):
            xm = 0.5*(x1 + x2)
            ym = 0.5*(y1 + y2)
            posm = (xm**2 + ym**2)**0.5
            pos1 = (x1**2 + y1**2)**0.5
            theta = 2*np.arccos(posm/pos1)
            return r*theta
        d1 = calc_arc(x1, y1, x, y)
        d2 = calc_arc(x, y, x2, y2)
    den = (d1+d2)
    den[den==0] = 1.e-15
    factor = d1/den
    f = fp1*(1-factor) + fp2*factor
    return f

def interp_theta_z_imp(data, mesh, semi_angle, H_measured, H_model, R_model,
        stretch_H=False, z_offset_bot=None, rotatedeg=0., num_sub=200, ncp=5,
        power_parameter=2):
    r"""Interpolates a data set in the `\theta, z, imp` format

    This function uses the inverse-weighted algorithm (:func:`.inv_weighted`).

    Parameters
    ----------
    data : str or numpy.ndarray, shape (N, ndim+1)
        The data or an array containing the imperfection file in the `(\theta,
        Z, imp)` format. The values to be interpolated must be in the last
        column.
    mesh : numpy.ndarray, shape (M, ndim)
        The new coordinates `(\theta, Z)` where the values will be
        interpolated to.
    semi_angle : float
        The cone semi-vertex angle in degrees.
    H_measured : float
        The total height of the measured test specimen, including eventual
        resin rings at the edges.
    H_model : float
        The total height of the new model, including eventual resin rings at
        the edges.
    R_model : float
        The radius (at the bottom) of the new model.
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

    if mesh.shape[1] != data.shape[1]-1:
        raise ValueError('Invalid input: mesh.shape[1] != data.shape[1]')

    data3D = np.zeros((data.shape[0], 4), dtype=FLOAT)

    if rotatedeg:
        data[:, 0] += np.deg2rad(rotatedeg)

    z = data[:, 1]
    z *= H_model

    alpharad = np.deg2rad(semi_angle)
    tana = tan(alpharad)
    def r_local(z):
        return R_model - z*tana
    data3D[:, 0] = r_local(z)*cos(data[:, 0])
    data3D[:, 1] = r_local(z)*sin(data[:, 0])
    data3D[:, 2] = z
    data3D[:, 3] = data[:, 2]

    coords = np.zeros((mesh.shape[0], 3), dtype=FLOAT)
    thetas = mesh[:, 0]
    z = mesh[:, 1]
    coords[:, 0] = r_local(z)*cos(thetas)
    coords[:, 1] = r_local(z)*sin(thetas)
    coords[:, 2] = z

    ans = inv_weighted(data3D, coords, col=2, ncp=ncp, num_sub=num_sub,
            power_parameter=power_parameter)

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

    print inv_weighted(a, b, num_sub=1, col=1, ncp=10)

