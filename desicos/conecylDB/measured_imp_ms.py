import os
import __main__

import numpy as np

from desicos.constants import FLOAT

DOC_COMMON = '''
    scaling_factor     - scales the original imperfection (default = 1.)
    r_TOL              - defines a tolerance to ignore measured points
                         (default = 1. percent)
    num_closest_points - number of measured points to be interpolated for each
                         node (default = 5)
    power_parameter    - power of inverse weighted interpolation function
                         (default = 2.)
    num_sec_z          - number of cross-sections in Z to classify the measured
                         points (default = 25)
'''
def read_file(file_name,
               frequency             = 1,
               forced_average_radius = None,
               H_measured            = None,
               R_measured            = None,
               stretch_H             = False,
               z_offset_bot            = None,
               r_TOL                 = 1.):
    print 'Reading imperfection file: %s ...' % file_name
    # user warnings
    if stretch_H:
        if z_offset_bot:
            print 'WARNING! Because of the stretch_H option,'
            print '         consider setting z_offset_bot to None'
    # reading the imperfection file
    ignore = False
    mps = np.loadtxt(file_name, dtype=FLOAT)
    r = np.sqrt(mps[:, 0]**2 + mps[:, 1]**2)
    # measuring model dimensions
    if R_measured == None:
        R_measured   = np.average(r)
        print 'WARNING! The cylinder average radius of the measured points\n'+\
              '         assumed to be %1.2f' % R_measured
    z_min = mps[:, 2].min()
    z_max = mps[:, 2].max()
    z_center  = (z_max + z_min)/2.
    H_points  = (z_max - z_min)
    print 'R_measured     :', R_measured
    # applying user inputs
    R = R_measured
    if forced_average_radius:
        R = forced_average_radius
        print 'Forced measured radius:', forced_average_radius
    H_model = H_points
    if not H_measured:
        H_measured = H_points
        print 'WARNING! The cylinder height of the measured points assumed\n'+\
              '         to be %1.2f' % H_measured
    # calculating default z_offset_bot
    if not z_offset_bot:
        if stretch_H:
            z_offset_bot = 0.
        else:
            z_offset_bot = (H_measured - H_points) / 2.
    offset_z = z_offset_bot - z_min
    print 'H_points       :', H_points
    print 'H_measured     :', H_measured
    print 'z_min          :', z_min
    print 'z_max          :', z_max
    print 'offset_z       :', offset_z
    r_TOL_min = (R * (1-r_TOL/100.))
    r_TOL_max = (R * (1+r_TOL/100.))
    cond = np.all(np.array((r > r_TOL_max,
                            r < r_TOL_min)), axis=0)
    skept = mps[cond]
    print 'Skipping %d points' % len(skept)
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

def plot_file(file_name,
               R_model,
               H_model,
               semi_angle,
               H_measured,
               R_measured=None,
               stretch_H        = False,
               z_offset_bot       = None,
               r_TOL            = 1.,
               frequency        = 100):
    # reading imperfection file
    m, o, mps = read_file(file_name             = file_name,
                          H_measured            = H_measured,
                          forced_average_radius = R_measured,
                          stretch_H              = stretch_H,
                          z_offset_bot            = z_offset_bot,
                          r_TOL                 = r_TOL)
    R_top = R_model - np.tan(np.deg2rad(semi_angle)) * H_model
    semi_angle = abs(semi_angle)
    def local_radius(z):
        r = R_model + (R_top - R_model) * z / H_model
        return r
    #
    model_name = os.path.basename(file_name).split('.')[0]
    mod = __main__.mdb.Model(model_name)
    part = mod.Part(model_name)
    # applying scalings when necessary
    mps[:, 2] *= H_model
    if semi_angle < 1.e-6:
        R_local = R_model
    else:
        R_local = local_radius(mps[:, 2])
    x = mps[:, 0] * R_local
    y = mps[:, 1] * R_local
    for i, xi in enumerate(x):
        part.DatumPointByCoordinate(coords=(xi, y[i], z[i]))
    #
    #
    from abaqusConstants import PARALLEL
    vpname = __main__.session.currentViewportName
    session = __main__.session
    session.viewports[vpname].setValues(displayedObject=part)
    session.viewports[vpname].view.setProjection(projection=PARALLEL)
    session.viewports[vpname].view.setValues(nearPlane=1232.67,
        farPlane=2195.51, cameraPosition=(-528.899, -505.13, 1304.85),
        cameraUpVector=(-0.00801664, 0.951535, 0.307437),
        cameraTarget=(-0.331696, 0.209839, -245.425))
    session.viewports[vpname].view.fitView()

def calc_nodal_translations(imperfection_file_name,
                            nodes,
                            H_model,
                            H_measured,
                            R_model,
                            R_measured,
                            semi_angle,
                            stretch_H,
                            z_offset_bot,
                            r_TOL,
                            num_closest_points,
                            power_parameter,
                            num_sec_z):
    # reading imperfection file
    m, o, mps = read_file(file_name = imperfection_file_name,
                          H_measured = H_measured,
                          R_measured = R_measured,
                          forced_average_radius = R_measured,
                          stretch_H = stretch_H,
                          z_offset_bot = z_offset_bot,
                          r_TOL = r_TOL)
    print 'Calculating nodal translations!'
    num_nodes = nodes.shape[0]
    R_top = R_model - np.tan(np.deg2rad(semi_angle)) * H_model
    semi_angle = abs(semi_angle)
    def local_radius(z):
        return R_model + (R_top - R_model) * z / H_model
    mps[:, 2] *= H_model
    if semi_angle < 1.e-6:
        R_local = R_model
    else:
        R_local = local_radius(mps[:, 2])
    mps[:, 0] *= R_local
    mps[:, 1] *= R_local
    num_sec_z = int(num_sec_z)
    mem_limit = 1024*1024*1024*8*2    # 2 GB
    mem_entries = int(mem_limit / 64) # if float64 is used
    sec_size = int(num_nodes/num_sec_z)
    #TODO better memory control...
    if sec_size**2*10 > mem_entries:
        while True:
            num_sec_z +=1
            sec_size = int(num_nodes/num_sec_z)
            if sec_size**2*10 <= mem_entries:
                print 'WARNING - new sec_size %d' % sec_size
                break
    ncp = num_closest_points
    nodes = nodes[np.argsort(nodes[:, 2])]
    mps = mps[np.argsort(mps[:, 2])]
    nodal_t = np.zeros(nodes.shape, dtype=nodes.dtype)
    limit = int(num_sec_z/5)
    for i in xrange(num_sec_z+1):
        i_inf = sec_size*i
        i_sup = sec_size*(i+1)
        if i % limit == 0:
            print '\t processed % 7d out of % 7d entries' %\
                  (min(i_sup, num_nodes), num_nodes)
        sub_nodes = nodes[i_inf : i_sup]
        if not np.any(sub_nodes):
            continue
        inf_z = sub_nodes[:, 2].min()
        sup_z = sub_nodes[:, 2].max()
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
        asort = np.argsort(dist, axis=1)
        lenn = sub_nodes.shape[0]
        lenp = sub_mps.shape[0]
        asort_mesh = asort + np.meshgrid(np.arange(lenn)*lenp,
                                         np.arange(lenp))[0].transpose()
        # getting the z coordinate of the closest points
        sub_mps_z = np.take(sub_mps[:, 2], asort[:, :ncp])
        # getting the distance of the closest points
        dist_ncp = np.take(dist, asort_mesh[:, :ncp])
        # avoiding division by zero
        dist_ncp[(dist_ncp==0)] == 1.e-12
        # calculating the radius of the sub-group of measured points
        radius = np.sqrt(sub_mps[:, 0]**2 + sub_mps[:, 1]**2)
        # taking only the radius of the closest points
        radius_ncp = np.take(radius, asort[:, :ncp])
        # weight calculation
        total_weight = np.sum(1./(dist_ncp**power_parameter), axis=1)
        weight = 1./(dist_ncp**power_parameter)
        # calculating the local radius for the closest points
        r_local_ncp = local_radius(sub_mps_z)
        # computing the new radius
        r_new = np.sum(radius_ncp*weight/r_local_ncp, axis=1)/total_weight
        r_new *= local_radius(sub_nodes[:, 2])
        #NOTE modified after Regina, Mariano and Saullo decided to use
        #     the imperfection amplitude constant along the whole cone
        #     surface, which represents better the real manufacturing
        #     conditions. In that case the amplitude will be re-scaled
        #     using only  the bottom radius
        # calculating the local radius for the nodes for the new assumption
        r_local_nodes = np.sqrt(sub_nodes[:,0]**2 + sub_nodes[:, 1]**2)
        # calculating the scaling factor required for the new assumption
        sf = R_model/r_local_nodes
        theta = np.arctan2(sub_nodes[:, 1], sub_nodes[:, 0])
        nodal_t[i_inf : i_sup][:, 0] = \
                (r_new*np.cos(theta) - sub_nodes[:, 0])*sf
        nodal_t[i_inf : i_sup][:, 1] = \
                (r_new*np.sin(theta) - sub_nodes[:, 1])*sf
        nodal_t[i_inf : i_sup][:, 3] = sub_nodes[:, 3]
    nodal_t = nodal_t[np.argsort(nodal_t[:, 3])]
    print 'Nodal translations calculated!'

    return nodal_t


def get_nodes_from_txt_file(nodes_file_name):
    '''The file name must be: x y z node_id
    '''
    nodes = np.loadtxt(nodes_file_name, dtype=FLOAT)
    nodes = nodes[np.argsort(nodes[:, 3])]
    return

def disturb_my_model(imperfection_file_name,
                     nodes_file_name,
                     output_file_name,
                     H_model,
                     H_measured,
                     R_model,
                     R_measured         = None,
                     semi_angle         = 0.,
                     stretch_H          = False,
                     z_offset_bot         = None,
                     scaling_factor     = 1.,
                     r_TOL              = 1.,
                     num_closest_points = 5,
                     power_parameter    = 2,
                     num_sec_z          = 25):
    # reading nodes data
    print 'Reading nodes data from %s ...' % nodes_file_name
    nodes = get_nodes_from_txt_file(nodes_file_name)
    # calling translate_nodes function
    nodal_translations = calc_nodal_translations(
                                     imperfection_file_name,
                                     nodes = nodes,
                                     H_model = H_model,
                                     H_measured = H_measured,
                                     R_model = R_model,
                                     R_measured = R_measured,
                                     semi_angle = semi_angle,
                                     stretch_H = stretch_H,
                                     z_offset_bot = z_offset_bot,
                                     r_TOL = r_TOL,
                                     num_closest_points = num_closest_points,
                                     power_parameter = power_parameter,
                                     num_sec_z = num_sec_z)
    # writing output file
    print 'Writing output file "%s" ...' % output_file_name
    outfile = open(output_file_name, 'w')
    for i, node in enumerate(nodal_translations):
        original_coords = node[0:3]
        translations = nodal_translations[k]
        new_coords = original_coords + translations * scaling_factor
        outfile.write('%d %f %f %f\n' % (k, coords[0], coords[1], coords[2]))
    outfile.close()
    return True

disturb_my_model.__doc__ = DOC_COMMON

if __name__ == '__main__':
    from  gui.gui_defaults import imps
    disturb_my_model(
             imperfection_file_name = imps['z18'],
             nodes_file_name    = r'C:\Temp\z15_nodes.txt',
             output_file_name   = r'C:\Temp\z15_nodes_new.txt',
             H_model            = 500,
             H_measured         = 510,
             R_model            = 250,
             R_measured         = None,
             stretch_H          = False,
             z_offset_bot         = None,
             scaling_factor     = 10.,
             r_TOL              = 10.,
             num_closest_points = 5,
             power_parameter    = 2,
             num_sec_z          = 100)
