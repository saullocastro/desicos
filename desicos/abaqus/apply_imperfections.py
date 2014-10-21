import __main__

import numpy as np
from numpy import cos, sin, tan, arctan2, deg2rad

from desicos.logger import *
from desicos.constants import FLOAT
from desicos.conecylDB.measured_imp_ms import calc_nodal_translations
from desicos.conecylDB.measured_imp_t import calc_elems_t
from desicos.conecylDB.read_write import read_theta_z_imp
from desicos.conecylDB.interpolate import inv_weighted
from desicos.abaqus.utils import vec_calc_elem_cg, index_within_linspace

def calc_translations_ABAQUS(imperfection_file_name,
                             model_name,
                             part_name,
                             H_model,
                             H_measured,
                             R_model,
                             R_measured = None,
                             semi_angle = 0.,
                             stretch_H = False,
                             z_offset_bot = None,
                             scaling_factor = 1.,
                             r_TOL = 1.,
                             num_closest_points = 5,
                             power_parameter = 2,
                             num_sec_z = 10,
                             use_theta_z_format = True):
    r"""Reads an imperfection file and calculates the nodal translations.

    """
    import desicos.abaqus.abaqus_functions as abaqus_functions
    mod = __main__.mdb.models[model_name]
    part = mod.parts[part_name]

    if use_theta_z_format:
        d, d, data = read_theta_z_imp(path=imperfection_file_name,
                                      H_measured=H_measured,
                                      stretch_H=stretch_H,
                                      z_offset_bot=z_offset_bot)

        data3D = np.zeros((data.shape[0], 4), dtype=FLOAT)
        z = data[:, 1]
        z *= H_model

        alpharad = deg2rad(semi_angle)
        tana = tan(alpharad)
        def r_local(z):
            return R_model - z*tana
        data3D[:, 0] = r_local(z)*cos(data[:, 0])
        data3D[:, 1] = r_local(z)*sin(data[:, 0])
        data3D[:, 2] = z
        data3D[:, 3] = data[:, 2]

        coords = np.array([n.coordinates for n in part.nodes], dtype=FLOAT)

        w0 = inv_weighted(data3D, coords,
                          num_sub = num_sec_z,
                          col = 2,
                          ncp = num_closest_points,
                          power_parameter = power_parameter)

        thetas = arctan2(coords[:, 1], coords[:, 0])

        trans = np.zeros_like(coords)
        trans[:, 0] = w0*cos(alpharad)*cos(thetas)
        trans[:, 1] = w0*cos(alpharad)*sin(thetas)
        trans[:, 2] = w0*sin(alpharad)

        return trans

    else:
        #NOTE perhaps remove this in the future, when the imperfection files
        #     are stored as theta, z, amplitude only
        nodes = np.array([[n.coordinates[0],
                           n.coordinates[1],
                           n.coordinates[2],
                           n.label] for n in part.nodes], dtype=FLOAT)

        # calling translate_nodes function
        trans = calc_nodal_translations(
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

        return trans


def translate_nodes_ABAQUS(imperfection_file_name,
                           model_name,
                           part_name,
                           H_model,
                           H_measured,
                           R_model,
                           R_measured = None,
                           semi_angle = 0.,
                           stretch_H = False,
                           z_offset_bot = None,
                           scaling_factor = 1.,
                           r_TOL = 1.,
                           num_closest_points = 5,
                           power_parameter = 2,
                           num_sec_z = 10,
                           nodal_translations = None,
                           use_theta_z_format = False):
    r"""
    Translates the nodes in Abaqus based on an imperfection from the database.

    The imperfection amplitude for each node is calculated using an inversed
    weight function (see :func:`desicos.conecylDB.interpolate.inv_weighted`).

    Parameters
    ----------
    imperfection_file_name : str
        The full path to the imperfection file, which must be a file with
        three columns containing the ``x, y, z`` coordinates when
        ``use_theta_z_format=False`` or containing ``x, theta, amplitude``
        when ``use_theta_z_format=True``.
    model_name : str
        Must be a valid key in the dictionary ``mdb.models``, in the
        interactive Python inside Abaqus.
    part_name : str
        Must be a valid key in the dictionary
        ``mdb.models[model_name].parts``, in the interactive Python inside
        Abaqus.
    H_model : float
        The height of the current cone/cylinder model.
    H_measured : float
        The height of the measured cone/cylinder model.
    R_model : float
        The radius of the current model. In case of cones this should be the
        bottom radius.
    R_measured : float, optional
        The radius of the measured model. In case of cones this should be the
        bottom radius.
    semi_angle : float, optional
        The cone semi-vertex angle (a null value indicates that a cylinder is
        beeing analyzed).
    stretch_H : float, optional
        A boolean indicating if the imperfection pattern should be stretched
        when applied to the model. The measurement systems usually cannot
        obtain data for the whole surface, making it an option to stretch the
        data to fit the whole surface. In case ``stretch_H=False`` the
        measured data of the extremities will be extruded up to the end of the
        domain.
    z_offset_bot : float or None, optional
        This parameter allows the analyst to adjust the height of the measured
        data about the model, when the measured data is not available for the
        whole domain.
    scaling_factor : float, optional
        The scaling factor that will multiply the calculated imperfection
        amplitude.
    r_TOL : float, optional
        Parameter to ignore noisy data in the imperfection file, the points
        with a radius higher than `r=r_{model} \times (1 + r_{TOL})` will not
        be considered in the interpolation.
    num_closest_points : int, optional
        Number of closest points that will be used in the inverse-weighted
        algorithm.
    power_parameter : int, optional
        Power parameter that will be used in the inverse-weighted algorithm.
    num_sec_z : int, optional
        Number of cross sections that will be used to classify the points
        spatially in the inverse-weighted algorithm.
    nodal_translations : None or numpy.ndarray, optional
        An array containing the interpolated traslations, which is passed to
        avoid repeated calls to the interpolation functions.
    use_theta_z_format : bool, optional
        A boolean to indicate whether the imperfection file contains ``x, y,
        z`` positions or ``theta, z, amplitude``.

    Returns
    -------
    nodal_translations : numpy.ndarray
        A 2-D array containing the translations ``x, y, z`` for each column.

    Notes
    -----
    Despite the nodal traslations are returned all the nodes belonging to this
    model will already be translated.


    """

    mod = __main__.mdb.models[model_name]
    part = mod.parts[part_name]

    coords = np.array([n.coordinates for n in part.nodes])

    if use_theta_z_format:
        if nodal_translations == None:
            trans = calc_translations_ABAQUS(imperfection_file_name,
                                             model_name,
                                             part_name,
                                             H_model,
                                             H_measured,
                                             R_model,
                                             R_measured,
                                             semi_angle,
                                             stretch_H,
                                             z_offset_bot,
                                             scaling_factor,
                                             r_TOL,
                                             num_closest_points,
                                             power_parameter,
                                             num_sec_z,
                                             use_theta_z_format)

        else:
            trans = nodal_translations

        # applying translations
        session = __main__.session
        viewport = session.viewports[session.currentViewportName]
        log('Applying new nodal positions in ABAQUS CAE to model {0} ...'.
            format(model_name))
        log('    (using a scaling factor of {0})'.format(scaling_factor))

        new_coords = coords + trans*scaling_factor
        part.editNode(nodes=part.nodes, coordinates=new_coords)

        log('Application of new nodal positions finished!')

        assembly = mod.rootAssembly
        viewport.setValues(displayedObject = assembly)
        assembly.regenerate()

        return trans

    else:
        nodes = np.array([[n.coordinates[0],
                           n.coordinates[1],
                           n.coordinates[2],
                           n.label] for n in part.nodes], dtype=FLOAT)

        # calling translate_nodes function
        if nodal_translations == None:
            nodal_translations = calc_translations_ABAQUS(
                                             imperfection_file_name,
                                             model_name,
                                             part_name,
                                             H_model,
                                             H_measured,
                                             R_model,
                                             R_measured,
                                             semi_angle,
                                             stretch_H,
                                             z_offset_bot,
                                             scaling_factor,
                                             r_TOL,
                                             num_closest_points,
                                             power_parameter,
                                             num_sec_z,
                                             use_theta_z_format)

        # applying translations
        session = __main__.session
        viewport = session.viewports[session.currentViewportName]
        log('Applying new nodal positions in ABAQUS CAE for model {0} ...'.
            format(model_name))
        log('    (using a scaling factor of {0})'.format(scaling_factor))

        trans = nodal_translations[:, :3]
        part.editNode(nodes=part.nodes,
                      coordinates=(coords + trans*scaling_factor))

        log('Application of new nodal positions finished!')
        # regenerating assembly
        assembly = mod.rootAssembly
        viewport.setValues(displayedObject=assembly)
        assembly.regenerate()

        return nodal_translations

def translate_nodes_ABAQUS_c0(m0, n0, c0, funcnum,
                              model_name,
                              part_name,
                              H_model,
                              semi_angle = 0.,
                              scaling_factor = 1.,
                              fem_meridian_bot2top = True):
    r"""
    Translates the nodes in Abaqus based on a Fourier Series.

    The Fourier Series can be a half-sine, half-cosine or a complete Fourier
    Series as detailed in :func:`desicos.conecylDB.fit_data.calc_c0`.

    Parameters
    ----------
    m0 : int
        Number of terms along the `x` coordinate.
    n0 : int
        Number of terms along the `\theta` coordinate.
    c0 : numpy.ndarray
        The coefficients that will give the imperfection pattern.
    funcnum : int
        The function type, as detailed in
        :func:`desicos.conecylDB.fit_data.calc_c0`.
    model_name : str
        Must be a valid key in the dictionary ``mdb.models``, in the
        interactive Python inside Abaqus.
    part_name : str
        Must be a valid key in the dictionary
        ``mdb.models[model_name].parts``, in the interactive Python inside
        Abaqus.
    H_model : float
        The height of the current cone/cylinder model.
    semi_angle : float, optional
        The cone semi-vertex angle (a null value indicates that a cylinder is
        beeing analyzed).
    scaling_factor : float, optional
        The scaling factor that will multiply ``c0`` when applying the
        imperfections.
    fem_meridian_bot2top : bool, optional
        A boolean indicating if the finite element has the `x` axis starting
        at the bottom or at the top.

    Returns
    -------
    nodal_translations : numpy.ndarray
        A 2-D array containing the translations ``x, y, z`` for each column.

    Notes
    -----
    Despite the nodal traslations are returned all the nodes belonging to this
    model will already be translated.

    """
    from desicos.conecylDB import fit_data

    log('Calculating imperfection amplitudes for model {0} ...\n\t'.
        format(model_name) +
        '(using a scaling factor of {0})'.format(scaling_factor))
    c0 = c0*scaling_factor
    mod = __main__.mdb.models[model_name]
    part = mod.parts[part_name]

    coords = np.array([n.coordinates for n in part.nodes])

    if fem_meridian_bot2top:
        xs_norm = (H_model-coords[:, 2])/H_model
    else:
        xs_norm = coords[:, 2]/H_model
    thetas = arctan2(coords[:, 1], coords[:, 0])

    alpharad = deg2rad(semi_angle)
    w0 = fit_data.fw0(m0, n0, c0, xs_norm, thetas, funcnum)
    nodal_translations = np.zeros_like(coords)
    nodal_translations[:, 0] = w0*cos(alpharad)*cos(thetas)
    nodal_translations[:, 1] = w0*cos(alpharad)*sin(thetas)
    nodal_translations[:, 2] = w0*sin(alpharad)

    log('Calculation of imperfection amplitudes finished!')

    # applying translations
    session = __main__.session
    viewport = session.viewports[session.currentViewportName]
    log('Applying new nodal positions in ABAQUS CAE to model {0} ...'.
        format(model_name))
    log('    (using a scaling factor of {0})'.format(scaling_factor))

    new_coords = coords + nodal_translations
    part.editNode(nodes=part.nodes, coordinates=new_coords)

    log('Application of new nodal positions finished!')

    assembly = mod.rootAssembly
    viewport.setValues(displayedObject = assembly)
    assembly.regenerate()

    return nodal_translations


def change_thickness_ABAQUS(imperfection_file_name,
                            model_name,
                            part_name,
                            stack,
                            t_model,
                            t_measured,
                            H_model,
                            H_measured,
                            R_model,
                            R_measured = None,
                            number_of_sets = None,
                            semi_angle = 0.,
                            stretch_H = False,
                            z_offset_bot = None,
                            scaling_factor = 1.,
                            num_closest_points = 5,
                            power_parameter = 2,
                            num_sec_z = 100,
                            elems_t = None,
                            t_set = None,
                            use_theta_z_format = False):

    mod = __main__.mdb.models[model_name]
    part = mod.parts[part_name]

    if use_theta_z_format:
        if elems_t == None or t_set == None:
            log('Reading coordinates for elements...')
            elements = vec_calc_elem_cg(part.elements)

            log('Coordinates for elements read!')
            d, d, data = read_theta_z_imp(path = imperfection_file_name,
                                          H_measured = H_measured,
                                          stretch_H = stretch_H,
                                          z_offset_bot = z_offset_bot)

            data3D = np.zeros((data.shape[0], 4), dtype=FLOAT)
            z = data[:, 1]
            z *= H_model

            alpharad = deg2rad(semi_angle)
            tana = tan(alpharad)
            def r_local(z):
                return R_model - z*tana
            data3D[:, 0] = r_local(z)*cos(data[:, 0])
            data3D[:, 1] = r_local(z)*sin(data[:, 0])
            data3D[:, 2] = z
            data3D[:, 3] = data[:, 2]

            ans = inv_weighted(data3D, elements[:, :3],
                               num_sub = num_sec_z,
                               col = 2,
                               ncp = num_closest_points,
                               power_parameter = power_parameter)

            t_set = set(ans)
            elems_t = np.zeros((elements.shape[0], 2), dtype=FLOAT)
            elems_t[:, 0] = elements[:, 3]
            elems_t[:, 1] = ans

        else:
            log('Thickness differences already calculated!')

    else:
        if elems_t == None or t_set == None:
            # reading elements data
            log('Reading coordinates for elements...')
            elements = vec_calc_elem_cg(part.elements)
            log('Coordinates for elements read!')
            # calling translate_nodes function
            elems_t, t_set = calc_elems_t(
                                imperfection_file_name,
                                nodes = elements,
                                t_model = t_model,
                                t_measured = t_measured,
                                H_model = H_model,
                                H_measured = H_measured,
                                R_model = R_model,
                                R_measured = R_measured,
                                semi_angle = semi_angle,
                                stretch_H = stretch_H,
                                z_offset_bot = z_offset_bot,
                                num_closest_points = num_closest_points,
                                power_parameter = power_parameter,
                                num_sec_z = num_sec_z)
        else:
            log('Thickness differences already calculated!')
    # creating sets
    t_list = []
    max_len_t_set = 100
    if len(t_set) >= max_len_t_set:
        number_of_sets = 10
        log('More than {0:d} different thicknesses measured!'.format(
            max_len_t_set))
        log('Forcing a number_of_sets = {0:d}'.format(number_of_sets))
    if number_of_sets == None or number_of_sets == 0:
        number_of_sets = len(t_set)
        t_list = list(t_set)
        t_list.sort()
    else:
        t_min = min(t_set)
        t_max = max(t_set)
        t_list = list(np.linspace(t_min, t_max, number_of_sets+1))

    # looking for the local_csys
    part_local_csys_datum = None
    for d in part.datum.values():
        if  'axis1' in d.__members__ \
        and 'axis2' in d.__members__:
            part_local_csys_datum = d
            break
    # grouping elements
    sets_ids = [[] for i in range(len(t_list))]
    for entry in elems_t:
        elem_id, t = entry
        index = index_within_linspace(t_list, t)
        sets_ids[index].append(int(elem_id))
    # putting elements in sets
    original_layup = part.compositeLayups['CompositePlate']
    plyts     = [ply.thickness for ply in original_layup.plies.values()]
    mat_names = [ply.material  for ply in original_layup.plies.values()]
    for i, set_ids in enumerate(sets_ids):
        if len(set_ids) == 0:
            # since t_set_norm * t_model <> t_set originally measured
            # there may be empty set_ids at the end
            continue
        elements = part.elements.sequenceFromLabels(labels=set_ids)
        sufix = 'measured_imp_t_{0:03d}'.format(i)
        set_name = 'Set_' + sufix
        log('Creating set ({0: 7d} elements): {1}'.format(
            len(set_ids), set_name))
        part.Set(name = set_name, elements = elements)
        region = part.sets[set_name]
        layup_name = 'CLayup_' + sufix
        t_diff = (float(t_list[i]) - t_model) * scaling_factor
        t_scaling_factor = (t_model + t_diff)/t_model
        abaqus_functions.create_composite_layup(
                    name = layup_name,
                    stack = stack,
                    plyts = plyts,
                    mat_names = mat_names,
                    part = part,
                    region = region,
                    part_local_csys_datum = part_local_csys_datum,
                    scaling_factor = t_scaling_factor)
    # suppress needed to put the new properties to the input file
    original_layup.suppress()

    return elems_t, t_set

if __name__=='__main__':
    cc = stds['desicos_study'].ccs[1]
    cc.created_model = False
    cc.create_model()
    coords = np.array([n.coordinates for n in cc.part.nodes])

    sf = 100

    path = r'C:\clones\desicos\desicos\conecylDB\files\dlr\degenhardt_2010_z20\degenhardt_2010_z20_msi_theta_z_imp.txt'
    H_measured = 510.
    H_model = 510.
    d, d, data = read_theta_z_imp(path=path,
                                  H_measured=H_measured,
                                  stretch_H=False,
                                  z_offset_bot=None)

    from random import sample
    log('init sample')
    data = np.array(sample(data, 10000))
    log('end sample')
    data = data[np.argsort(data[:, 0])]
    data = np.vstack((data[-3000:], data[:], data[:3000]))
    data[:, 0] /= data[:, 0].max()


    mesh = np.zeros((coords.shape[0], 2), dtype=FLOAT)
    mesh[:, 0] = arctan2(coords[:, 1], coords[:, 0])
    mesh[:, 1] = coords[:, 2]
    mesh_norm = mesh.copy()
    mesh_norm[:, 0] /= mesh_norm[:, 0].max()
    mesh_norm[:, 1] /= mesh_norm[:, 1].max()

    import desicos.conecylDB.interpolate
    reload(desicos.conecylDB.interpolate)
    ans = desicos.conecylDB.interpolate.inv_weighted(
            data, mesh_norm, num_sub=100, col=1, ncp=10, power_parameter=1.5)

    alpharad = np.deg2rad(0.)
    trans = np.zeros_like(coords)
    trans[:, 0] = ans*cos(mesh[:, 0])*cos(alpharad)
    trans[:, 1] = ans*sin(mesh[:, 0])*cos(alpharad)
    trans[:, 2] = ans*sin(alpharad)

    cc.part.editNode(nodes=cc.part.nodes,
                  coordinates=(coords + trans*100))
