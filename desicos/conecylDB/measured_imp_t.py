import os
import __main__

import numpy as np

from desicos.abaqus.utils import vec_calc_elem_cg, index_within_linspace
from desicos.constants import FLOAT

def read_file(file_name,
              R_best_fit,
              t_measured = None,
              H_measured = None,
              stretch_H  = False,
              z_offset_bot = None):
    print('Reading imperfection file: %s ...' % file_name)
    # user warnings
    if stretch_H:
        if z_offset_bot:
            print('WARNING! Because of the stretch_H option,')
            print('         consider setting z_offset_bot to None')
    # reading the imperfection file
    mps = np.loadtxt(file_name, dtype=FLOAT)
    t_set = set(mps[:, 3])
    # measuring model dimensions
    z_min = mps[:, 2].min()
    z_max = mps[:, 2].max()
    z_center  = (z_max + z_min)/2.
    H_points = (z_max - z_min)
    # applying user inputs
    if not H_measured:
        H_measured = H_points
        print('WARNING! The cylinder height of the measured points ' +
              'assumed to be %1.2f' % H_measured)
    t_av = t_measured
    if not t_measured:
        t_av = np.average(mps[:, 3])
    # calculating default z_offset_bot
    if not z_offset_bot:
        if stretch_H:
            z_offset_bot = 0.
        else:
            z_offset_bot = (H_measured - H_points) / 2.
    offset_z = z_offset_bot - z_min
    print('H_points       :', H_points)
    print('H_measured     :', H_measured)
    print('z_min          :', z_min)
    print('z_max          :', z_max)
    print('offset_z       :', offset_z)
    print('t_av           :', t_av)
    norm_mps = mps.copy()
    norm_mps[:, 0] /= R_best_fit
    norm_mps[:, 1] /= R_best_fit
    norm_mps[:, 2] += offset_z
    if stretch_H:
        norm_mps[:, 2] /= H_points
    else:
        norm_mps[:, 2] /= H_measured
    norm_mps[:, 3] /= t_av
    t_set_norm = set([t/t_av for t in t_set])
    return mps, norm_mps, t_set_norm

def calc_elems_t(imperfection_file_name,
                 nodes,
                 t_model,
                 t_measured,
                 H_model,
                 H_measured,
                 R_model,
                 R_best_fit,
                 semi_angle,
                 stretch_H,
                 z_offset_bot,
                 num_closest_points,
                 power_parameter,
                 num_sec_z):
    # reading imperfection file
    m, mps, t_set_norm = read_file(file_name     = imperfection_file_name,
                                   R_best_fit    = R_best_fit,
                                   t_measured    = t_measured,
                                   H_measured    = H_measured,
                                   stretch_H     = stretch_H,
                                   z_offset_bot    = z_offset_bot)
    print('Calculating new thicknesses...')
    t_set = set([t*t_model for t in t_set_norm])
    R_top = R_model - np.tan(np.deg2rad(semi_angle)) * H_model
    semi_angle = abs(semi_angle)
    def local_radius(z):
        return R_model + (R_top - R_model) * z / H_model
    # applying scalings when necessary
    mps[:, 2] *= H_model
    if semi_angle < 1.e-6:
        R_local = R_model
    else:
        R_local = local_radius(mps[:, 2])
    mps[:, 0] *= R_local
    mps[:, 1] *= R_local
    mps[:, 3] *= t_model
    num_sec_z = int(num_sec_z)
    mem_limit = 1024*1024*1024*8*2    # 2 GB
    mem_entries = int(mem_limit / 64) # if float64 is used
    sec_size = int(nodes.shape[0]/num_sec_z)
    #TODO better memory control...
    if sec_size**2*10 > mem_entries:
        while True:
            num_sec_z +=1
            sec_size = int(nodes.shape[0]/num_sec_z)
            if sec_size**2*10 <= mem_entries:
                print('WARNING - new sec_size %d' % sec_size)
                break
    ncp = num_closest_points
    nodes = nodes[np.argsort(nodes[:, 2])]
    mps = mps[np.argsort(mps[:, 2])]
    elems_t = np.zeros((nodes.shape[0], 2), dtype=nodes.dtype)
    elems_t[:, 0] = nodes[:, 3]
    limit = int(num_sec_z/5)
    for i in xrange(num_sec_z + 1):
        i_inf = sec_size*i
        i_sup = sec_size*(i+1)
        if i % limit == 0:
            print('\t processed % 7d out of % 7d entries' %
                  (min(i_sup, nodes.shape[0]), nodes.shape[0]))
        sub_nodes = nodes[i_inf : i_sup]
        if not np.any(sub_nodes):
            continue
        inf_z = sub_nodes[:, 2].min()
        sup_z = sub_nodes[:, 2].max()
        c = 0
        tol = 0.01
        if i == 0 or i == num_sec_z:
            tol = 0.05
        while True:
            cond1 = mps[:, 2] >= inf_z - tol*H_model
            cond2 = mps[:, 2] <= sup_z + tol*H_model
            cond = np.all(np.array((cond1, cond2)), axis=0)
            sub_mps = mps[cond]
            if not np.any(sub_mps):
                tol += 0.01
            else:
                break
        dist  = np.subtract.outer(sub_nodes[:, 0], sub_mps[:, 0])**2
        dist += np.subtract.outer(sub_nodes[:, 1], sub_mps[:, 1])**2
        dist += np.subtract.outer(sub_nodes[:, 2], sub_mps[:, 2])**2
        a = np.argsort(dist, axis=1)
        lenn = sub_nodes.shape[0]
        lenp = sub_mps.shape[0]
        a2 = a + np.meshgrid(np.arange(lenn)*lenp,
                             np.arange(lenp))[0].transpose()
        dist_ncp = np.take(dist, a2[:, :ncp])
        dist_ncp[dist_ncp==0] == 1.e-9
        thicks = sub_mps[:, 3]
        thicks_ncp = np.take(thicks, a[:, :ncp])
        total_weight = np.sum(1./dist_ncp**power_parameter, axis=1)
        weight = 1./(dist_ncp**power_parameter)
        elems_t[i_inf:i_sup, 1] = (
                        np.sum(thicks_ncp*weight, axis=1)/total_weight)
    elems_t = elems_t[np.argsort(elems_t[:, 1])]
    print('New thicknesses calculated!')

    return elems_t, t_set

