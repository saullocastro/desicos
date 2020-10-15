r"""
===============================================================
Apply Imperfections (:mod:`desicos.abaqus.apply_imperfections`)
===============================================================

.. currentmodule:: desicos.abaqus.apply_imperfections

Routines to apply geometric and thickness imperfections into the finite
element model.

"""
from random import sample

import numpy as np
from numpy import cos, sin, tan, arctan2, deg2rad

from desicos.logger import log
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
                             R_best_fit=None,
                             semi_angle=0.,
                             stretch_H=False,
                             z_offset_bot=None,
                             rotatedeg=0.,
                             scaling_factor=1.,
                             r_TOL=1.,
                             num_closest_points=5,
                             power_parameter=2,
                             use_theta_z_format=True,
                             ignore_bot_h=None,
                             ignore_top_h=None,
                             sample_size=None,
                             T=None):
    r"""Reads an imperfection file and calculates the nodal translations

    Parameters
    ----------
    imperfection_file_name : str
        Full path to the imperfection file.
    model_name : str
        Model name.
    part_name : str
        Part name.
    H_model : float
        Total height of the model where the imperfections will be applied to,
        considering also eventual resin rings.
    H_measured : float
        The total height of the measured test specimen, including eventual
        resin rings at the edges.
    R_model : float
        Radius **at the bottom edge** of the model where the imperfections
        will be applied to.
    R_best_fit : float, optional
        Best fit radius obtained with functions :func:`.best_fit_cylinder`
        or :func:`.best_fit_cone`.
    semi_angle : float, optional
        Cone semi-vertex angle in degrees, when applicable.
    stretch_H : bool, optional
        If the measured imperfection data should be stretched to the current
        model (which may happen when ``H_model!=H_measured``.
    z_offset_bot : float, optional
        It is common to have the measured data not covering the whole test
        specimen, and therefore it will be centralized, if a non-centralized
        position is desired this parameter can be used for the adjustment.
    rotatedeg : float, optional
        Rotation angle in degrees telling how much the imperfection pattern
        should be rotated about the `X_3` (or `Z`) axis.
    scaling_factor : float, optional
        A scaling factor that can be used to study the imperfection
        sensitivity.
    r_TOL : float, optional
        Percentage tolerance to ignore noisy data from the measurements.
    num_closest_points : int, optional
        See :func:`the inverse-weighted interpolation algorithm
        <.inv_weighted>`.
    power_parameter : float, optional
        See :func:`the inverse-weighted interpolation algorithm
        <.inv_weighted>`.
    use_theta_z_format : bool, optional
        If the new format `\theta, Z, imp` should be used instead of the old
        `X, Y, Z`.
    ignore_bot_h : None or float, optional
        Used to ignore nodes from the bottom resin ring.
    ignore_top_h : None or float, optional
        Used to ignore nodes from the top resin ring.
    sample_size : int, optional
        If the input file containing the measured data is too large it may be
        required to limit the sample size in order to avoid memory errors.
    T : None or np.ndarray, optional
        A transformation matrix (cf. :func:`.transf_matrix`) required when the
        mesh is not in the :ref:`default coordinate system <figure_conecyl>`.

    """
    import abaqus

    import desicos.abaqus.abaqus_functions as abaqus_functions

    mod = abaqus.mdb.models[model_name]
    part = mod.parts[part_name]
    part_nodes = np.array(part.nodes)
    coords = np.array([n.coordinates for n in part_nodes], dtype=FLOAT)

    if T is not None:
        tmp = np.vstack((coords.T, np.ones((1, coords.shape[0]))))
        coords = np.dot(T, tmp).T
        del tmp

    if ignore_bot_h is not None:
        if ignore_bot_h <= 0:
            ignore_bot_h = None
        else:
            mask = coords[:, 2] > ignore_bot_h
            coords = coords[mask]
            part_nodes = part_nodes[mask]

    if ignore_top_h is not None:
        if ignore_top_h <= 0:
            ignore_top_h = None
        else:
            mask = coords[:, 2] < (H_model - ignore_top_h)
            coords = coords[mask]
            part_nodes = part_nodes[mask]

    if use_theta_z_format:
        d, d, data = read_theta_z_imp(path=imperfection_file_name,
                                      H_measured=H_measured,
                                      stretch_H=stretch_H,
                                      z_offset_bot=z_offset_bot)
        if sample_size:
            num = data.shape[0]
            if sample_size < num:
                log('Using sample_size={0}'.format(sample_size), level=1)
                data = data[sample(range(num), int(sample_size)), :]

        if r_TOL:
            max_imp = R_model * r_TOL / 100.
            imp = data[:, 2]
            cond = np.any(np.array((imp > max_imp, imp < (-max_imp))), axis=0)
            log('Skipping {0} points'.format(len(imp[cond])))
            data = data[np.logical_not(cond), :]

        data3D = np.zeros((data.shape[0], 4), dtype=FLOAT)
        if rotatedeg:
            data[:, 0] += deg2rad(rotatedeg)
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

        dist, w0 = inv_weighted(data3D, coords,
                          ncp = num_closest_points,
                          power_parameter = power_parameter)

        thetas = arctan2(coords[:, 1], coords[:, 0])

        trans = np.zeros_like(coords)
        trans[:, 0] = w0*cos(alpharad)*cos(thetas)
        trans[:, 1] = w0*cos(alpharad)*sin(thetas)
        trans[:, 2] = w0*sin(alpharad)

    else:
        #NOTE perhaps remove this in the future, when the imperfection files
        #     are stored as theta, z, amplitude only
        nodes = np.array([[n.coordinates[0],
                           n.coordinates[1],
                           n.coordinates[2],
                           n.label] for n in part_nodes], dtype=FLOAT)

        # calling translate_nodes function
        trans = calc_nodal_translations(
                                imperfection_file_name,
                                nodes = nodes,
                                H_model = H_model,
                                H_measured = H_measured,
                                R_model = R_model,
                                R_best_fit = R_best_fit,
                                semi_angle = semi_angle,
                                stretch_H = stretch_H,
                                z_offset_bot = z_offset_bot,
                                rotatedeg = rotatedeg,
                                r_TOL = r_TOL,
                                num_closest_points = num_closest_points,
                                power_parameter = power_parameter,
                                sample_size = sample_size)
        trans = trans[:, :3]

    return trans


def translate_nodes_ABAQUS(imperfection_file_name,
                           model_name,
                           part_name,
                           H_model,
                           H_measured,
                           R_model,
                           R_best_fit=None,
                           semi_angle=0.,
                           stretch_H=False,
                           z_offset_bot=None,
                           rotatedeg=0.,
                           scaling_factor=1.,
                           r_TOL=1.,
                           num_closest_points=5,
                           power_parameter=2,
                           nodal_translations=None,
                           use_theta_z_format=False,
                           ignore_bot_h=None,
                           ignore_top_h=None,
                           sample_size=None,
                           T=None):
    r"""Translates the nodes in Abaqus based on imperfection data

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
        Total height of the model where the imperfections will be applied to,
        considering also eventual resin rings.
    H_measured : float
        The total height of the measured test specimen, including eventual
        resin rings at the edges.
    R_model : float
        The radius of the current model. In case of cones this should be the
        bottom radius.
    R_best_fit : float, optional
        Best fit radius obtained with functions :func:`.best_fit_cylinder`
        or :func:`.best_fit_cone`.
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
    z_offset_bot : float, optional
        This parameter allows the analyst to adjust the height of the measured
        data about the model, when the measured data is not available for the
        whole domain.
    rotatedeg : float, optional
        Rotation angle in degrees telling how much the imperfection pattern
        should be rotated about the `X_3` (or `Z`) axis.
    scaling_factor : float, optional
        The scaling factor that will multiply the calculated imperfection
        amplitude.
    r_TOL : float, optional
        Parameter to ignore noisy data in the imperfection file, the points
        with a radius higher than `r=r_{model} \times (1 + r_{TOL})` will not
        be considered in the interpolation.
    num_closest_points : int, optional
        See :func:`the inverse-weighted interpolation algorithm
        <.inv_weighted>`.
    power_parameter : int, optional
        See :func:`the inverse-weighted interpolation algorithm
        <.inv_weighted>`.
    nodal_translations : None or numpy.ndarray, optional
        An array containing the interpolated traslations, which is passed to
        avoid repeated calls to the interpolation functions.
    use_theta_z_format : bool, optional
        A boolean to indicate whether the imperfection file contains ``x, y,
        z`` positions or ``theta, z, amplitude``.
    ignore_bot_h : None or float, optional
        Used to ignore nodes from the bottom resin ring.
    ignore_top_h : None or float, optional
        Used to ignore nodes from the top resin ring.
    sample_size : int, optional
        If the input file containing the measured data is too large it may be
        required to limit the sample size in order to avoid memory errors.
    T : None or np.ndarray, optional
        A transformation matrix (cf. :func:`.transf_matrix`) required when the
        mesh is not in the :ref:`default coordinate system <figure_conecyl>`.

    Returns
    -------
    nodal_translations : numpy.ndarray
        A 2-D array containing the translations ``x, y, z`` for each column.

    Notes
    -----
    Despite the nodal traslations are returned all the nodes belonging to this
    model will already be translated.

    """
    from abaqus import mdb, session

    mod = mdb.models[model_name]
    part = mod.parts[part_name]

    part_nodes = np.array(part.nodes)
    coords = np.array([n.coordinates for n in part_nodes])

    if T is not None:
        tmp = np.vstack((coords.T, np.ones((1, coords.shape[0]))))
        coords = np.dot(T, tmp).T
        del tmp

    if ignore_bot_h is not None:
        if ignore_bot_h <= 0:
            ignore_bot_h = None
        else:
            log('Applying ignore_bot_h: ignoring nodes with z <= {0}'.format(
                ignore_bot_h))
            mask = coords[:, 2] > ignore_bot_h
            coords = coords[mask]
            part_nodes = part_nodes[mask]

    if ignore_top_h is not None:
        if ignore_top_h <= 0:
            ignore_top_h = None
        else:
            log('Applying ignore_top_h: ignoring nodes with z >= {0}'.format(
                H_model - ignore_top_h))
            mask = coords[:, 2] < (H_model - ignore_top_h)
            coords = coords[mask]
            part_nodes = part_nodes[mask]

    if use_theta_z_format:
        if nodal_translations is None:
            trans = calc_translations_ABAQUS(
                        imperfection_file_name = imperfection_file_name,
                        model_name = model_name,
                        part_name = part_name,
                        H_model = H_model,
                        H_measured = H_measured,
                        R_model = R_model,
                        R_best_fit = R_best_fit,
                        semi_angle = semi_angle,
                        stretch_H = stretch_H,
                        z_offset_bot = z_offset_bot,
                        rotatedeg = rotatedeg,
                        scaling_factor = scaling_factor,
                        r_TOL = r_TOL,
                        num_closest_points = num_closest_points,
                        power_parameter = power_parameter,
                        use_theta_z_format = use_theta_z_format,
                        ignore_bot_h = ignore_bot_h,
                        ignore_top_h = ignore_top_h,
                        sample_size = sample_size,
                        T = T)

        else:
            trans = nodal_translations

        # applying translations
        viewport = session.viewports[session.currentViewportName]
        log('Applying new nodal positions in ABAQUS CAE to model {0} ...'.
            format(model_name))
        log('    (using a scaling factor of {0})'.format(scaling_factor))

        new_coords = coords + trans*scaling_factor

        if T is not None:
            Tinv = np.zeros_like(T)
            Tinv[:3, :3] = T[:3, :3].T
            Tinv[:, 3] = -T[:, 3]
            tmp = np.vstack((new_coords.T, np.ones((1, new_coords.shape[0]))))
            new_coords = np.dot(Tinv, tmp).T
            del tmp

        meshNodeArray = part.nodes.sequenceFromLabels(
                            [n.label for n in part_nodes])
        new_coords = np.ascontiguousarray(new_coords)
        part.editNode(nodes=part_nodes.tolist(), coordinates=new_coords)

        log('Application of new nodal positions finished!')

        ra = mod.rootAssembly
        viewport.setValues(displayedObject=ra)
        ra.regenerate()

        return trans

    else:
        nodes = np.array([[n.coordinates[0],
                           n.coordinates[1],
                           n.coordinates[2],
                           n.label] for n in part_nodes], dtype=FLOAT)

        # calling translate_nodes function
        if nodal_translations is None:
            nodal_translations = calc_translations_ABAQUS(
                         imperfection_file_name = imperfection_file_name,
                         model_name = model_name,
                         part_name = part_name,
                         H_model = H_model,
                         H_measured = H_measured,
                         R_model = R_model,
                         R_best_fit = R_best_fit,
                         semi_angle = semi_angle,
                         stretch_H = stretch_H,
                         z_offset_bot = z_offset_bot,
                         rotatedeg = rotatedeg,
                         scaling_factor = scaling_factor,
                         r_TOL = r_TOL,
                         num_closest_points = num_closest_points,
                         power_parameter = power_parameter,
                         use_theta_z_format = use_theta_z_format,
                         ignore_bot_h = ignore_bot_h,
                         ignore_top_h = ignore_top_h,
                         sample_size = sample_size,
                         T = T)

        # applying translations
        viewport = session.viewports[session.currentViewportName]
        log('Applying new nodal positions in ABAQUS CAE for model {0} ...'.
            format(model_name))
        log('    (using a scaling factor of {0})'.format(scaling_factor))

        trans = nodal_translations

        new_coords = coords + trans*scaling_factor

        if T is not None:
            Tinv = np.zeros_like(T)
            Tinv[:3, :3] = T[:3, :3].T
            Tinv[:, 3] = -T[:, 3]
            tmp = np.vstack((new_coords.T, np.ones((1, new_coords.shape[0]))))
            new_coords = np.dot(Tinv, tmp).T
            del tmp

        meshNodeArray = part.nodes.sequenceFromLabels(
                            [n.label for n in part_nodes])
        new_coords = np.ascontiguousarray(new_coords)
        part.editNode(nodes=meshNodeArray, coordinates=new_coords)

        log('Application of new nodal positions finished!')
        # regenerating ra
        ra = mod.rootAssembly
        viewport.setValues(displayedObject=ra)
        ra.regenerate()

        return nodal_translations


def translate_nodes_ABAQUS_c0(m0, n0, c0, funcnum,
                              model_name,
                              part_name,
                              H_model,
                              semi_angle=0.,
                              scaling_factor=1.,
                              fem_meridian_bot2top=True,
                              ignore_bot_h=None,
                              ignore_top_h=None,
                              T=None):
    r"""Translates the nodes in Abaqus based on a Fourier series

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
        Total height of the model where the imperfections will be applied to,
        considering also eventual resin rings.
    semi_angle : float, optional
        The cone semi-vertex angle (a null value indicates that a cylinder is
        beeing analyzed).
    scaling_factor : float, optional
        The scaling factor that will multiply ``c0`` when applying the
        imperfections.
    fem_meridian_bot2top : bool, optional
        A boolean indicating if the finite element has the `x` axis starting
        at the bottom or at the top.
    ignore_bot_h : None or float, optional
        Used to ignore nodes from the bottom resin ring.
    ignore_top_h : None or float, optional
        Used to ignore nodes from the top resin ring.
    T : None or np.ndarray, optional
        A transformation matrix (cf. :func:`.transf_matrix`) required when the
        mesh is not in the :ref:`default coordinate system <figure_conecyl>`.

    Returns
    -------
    nodal_translations : numpy.ndarray
        A 2-D array containing the translations ``x, y, z`` for each column.

    Notes
    -----
    Despite the nodal traslations are returned all the nodes belonging to this
    model will be already translated.

    """
    from abaqus import mdb, session

    from desicos.conecylDB import fit_data

    log('Calculating imperfection amplitudes for model {0} ...\n\t'.
        format(model_name) +
        '(using a scaling factor of {0})'.format(scaling_factor))
    c0 = c0*scaling_factor
    mod = mdb.models[model_name]
    part = mod.parts[part_name]

    part_nodes = np.array(part.nodes)
    coords = np.array([n.coordinates for n in part_nodes])

    if T is not None:
        tmp = np.vstack((coords.T, np.ones((1, coords.shape[0]))))
        coords = np.dot(T, tmp).T
        del tmp

    if ignore_bot_h is not None:
        if ignore_bot_h <= 0:
            ignore_bot_h = None
        else:
            log('Applying ignore_bot_h: ignoring nodes with z <= {0}'.format(
                ignore_bot_h))
            mask = coords[:, 2] > ignore_bot_h
            coords = coords[mask]
            part_nodes = part_nodes[mask]

    if ignore_top_h is not None:
        if ignore_top_h <= 0:
            ignore_top_h = None
        else:
            log('Applying ignore_top_h: ignoring nodes with z >= {0}'.format(
                H_model - ignore_top_h))
            mask = coords[:, 2] < (H_model - ignore_top_h)
            coords = coords[mask]
            part_nodes = part_nodes[mask]

    if ignore_bot_h is None:
        ignore_bot_h = 0
    if ignore_top_h is None:
        ignore_top_h = 0
    H_eff = H_model - (ignore_bot_h + ignore_top_h)
    if fem_meridian_bot2top:
        xs_norm = (coords[:, 2]-ignore_bot_h)/H_eff
    else:
        xs_norm = (H_eff-(coords[:, 2]-ignore_bot_h))/H_eff

    thetas = arctan2(coords[:, 1], coords[:, 0])

    alpharad = deg2rad(semi_angle)
    w0 = fit_data.fw0(m0, n0, c0, xs_norm, thetas, funcnum)
    nodal_translations = np.zeros_like(coords)
    nodal_translations[:, 0] = w0*cos(alpharad)*cos(thetas)
    nodal_translations[:, 1] = w0*cos(alpharad)*sin(thetas)
    nodal_translations[:, 2] = w0*sin(alpharad)

    log('Calculation of imperfection amplitudes finished!')

    # applying translations
    viewport = session.viewports[session.currentViewportName]
    log('Applying new nodal positions in ABAQUS CAE to model {0} ...'.
        format(model_name))
    log('    (using a scaling factor of {0})'.format(scaling_factor))

    new_coords = coords + nodal_translations

    if T is not None:
        Tinv = np.zeros_like(T)
        Tinv[:3, :3] = T[:3, :3].T
        Tinv[:, 3] = -T[:, 3]
        tmp = np.vstack((new_coords.T, np.ones((1, new_coords.shape[0]))))
        new_coords = np.dot(Tinv, tmp).T
        del tmp

    meshNodeArray = part.nodes.sequenceFromLabels(
                        [n.label for n in part_nodes])
    new_coords = np.ascontiguousarray(new_coords)
    part.editNode(nodes=meshNodeArray, coordinates=new_coords)

    log('Application of new nodal positions finished!')

    ra = mod.rootAssembly
    viewport.setValues(displayedObject=ra)
    ra.regenerate()

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
                            R_best_fit = None,
                            number_of_sets = None,
                            semi_angle = 0.,
                            stretch_H = False,
                            z_offset_bot = None,
                            scaling_factor = 1.,
                            num_closest_points = 5,
                            power_parameter = 2,
                            elems_t = None,
                            t_set = None,
                            use_theta_z_format = False):
    r"""Applies a given thickness imperfection to the finite element model

    Assumes that a percentage variation of the laminate thickness can be
    represented by the same percentage veriation of each ply, i.e., each
    ply thickness is varied in order to reflect a given measured thickness
    imperfection field.

    Parameters
    ----------

    imperfection_file_name : str
        Full path to the imperfection file.
    model_name : str
        Model name.
    part_name : str
        Part name.
    stack : list
        The stacking sequence of the current model with each angle given in
        degrees.
    t_model : float
        The nominal shell thickness of the current model.
    t_measured : float
        The nominal thickness of the measured specimen.
    H_model : float
        Total height of the model where the imperfections will be applied to,
        considering also eventual resin rings.
    H_measured : float
        The total height of the measured test specimen, including eventual
        resin rings at the edges.
    R_model : float
        Radius **at the bottom edge** of the model where the imperfections
        will be applied to.
    R_best_fit : float, optional
        Best fit radius obtained with functions :func:`.best_fit_cylinder`
        or :func:`.best_fit_cone`.
    number_of_sets : int, optional
        Defines in how many levels the thicknesses should be divided. If
        ``None`` it will be based on the input file, and if the threshold
        of ``100`` is exceeded, ``10`` sections are used.
    semi_angle : float, optional
        Cone semi-vertex angle in degrees, when applicable.
    stretch_H : bool, optional
        If the measured imperfection data should be stretched to the current
        model (which may happen when ``H_model!=H_measured``.
    z_offset_bot : float, optional
        It is common to have the measured data not covering the whole test
        specimen, and therefore it will be centralized, if a non-centralized
        position is desired this parameter can be used for the adjustment.
    scaling_factor : float, optional
        A scaling factor that can be used to study the imperfection
        sensitivity.
    num_closest_points : int, optional
        See :func:`the inverse-weighted interpolation algorithm
        <.inv_weighted>`.
    power_parameter : float, optional
        See :func:`the inverse-weighted interpolation algorithm
        <.inv_weighted>`.
    elems_t : np.ndarray, optional
        Interpolated thickness for each element. Can be used to avoid the same
        interpolation to be performed twice.
    t_set : set, optional
        A ``set`` object containing the unique thicknesses that will be used
        to create the new properties.
    use_theta_z_format : bool, optional
        If the new format `\theta, Z, imp` should be used instead of the old
        `X, Y, Z`.

    """
    from abaqus import mdb

    import desicos.abaqus.abaqus_functions as abaqus_functions

    mod = mdb.models[model_name]
    part = mod.parts[part_name]
    part_cyl_csys = part.features['part_cyl_csys']
    part_cyl_csys = part.datums[part_cyl_csys.id]

    if use_theta_z_format:
        if elems_t is None or t_set is None:
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

            dist, ans = inv_weighted(data3D, elements[:, :3],
                               ncp = num_closest_points,
                               power_parameter = power_parameter)

            t_set = set(ans)
            t_set.discard(0.) #TODO why inv_weighted returns an array with 0.
            elems_t = np.zeros((elements.shape[0], 2), dtype=FLOAT)
            elems_t[:, 0] = elements[:, 3]
            elems_t[:, 1] = ans

        else:
            log('Thickness differences already calculated!')

    else:
        if elems_t is None or t_set is None:
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
                                R_best_fit = R_best_fit,
                                semi_angle = semi_angle,
                                stretch_H = stretch_H,
                                z_offset_bot = z_offset_bot,
                                num_closest_points = num_closest_points,
                                power_parameter = power_parameter
                                )
        else:
            log('Thickness differences already calculated!')
    # creating sets
    t_list = []
    max_len_t_set = 100
    if len(t_set) >= max_len_t_set and number_of_sets in (None, 0):
        number_of_sets = 10
        log('More than {0:d} different thicknesses measured!'.format(
            max_len_t_set))
        log('Forcing a number_of_sets = {0:d}'.format(number_of_sets))
    if number_of_sets is None or number_of_sets == 0:
        number_of_sets = len(t_set)
        t_list = list(t_set)
        t_list.sort()
    else:
        t_min = min(t_set)
        t_max = max(t_set)
        t_list = list(np.linspace(t_min, t_max, number_of_sets+1))

    # grouping elements
    sets_ids = [[] for i in range(len(t_list))]
    for entry in elems_t:
        elem_id, t = entry
        index = index_within_linspace(t_list, t)
        sets_ids[index].append(int(elem_id))
    # putting elements in sets
    original_layup = part.compositeLayups['CompositePlate']
    for i, set_ids in enumerate(sets_ids):
        if len(set_ids) == 0:
            # since t_set_norm * t_model <> t_set originally measured
            # there may be empty set_ids at the end
            continue
        elements = part.elements.sequenceFromLabels(labels=set_ids)
        suffix = 'measured_imp_t_{0:03d}'.format(i)
        set_name = 'Set_' + suffix
        log('Creating set ({0: 7d} elements): {1}'.format(
            len(set_ids), set_name))
        part.Set(name = set_name, elements = elements)
        region = part.sets[set_name]
        layup_name = 'CLayup_' + suffix
        t_diff = (float(t_list[i]) - t_model) * scaling_factor
        t_scaling_factor = (t_model + t_diff)/t_model

        def modify_ply(index, kwargs):
            kwargs['thickness'] *= t_scaling_factor
            kwargs['region'] = region
            return kwargs

        layup = part.CompositeLayup(name=layup_name,
                                    objectToCopy=original_layup)
        layup.resume()
        abaqus_functions.modify_composite_layup(part=part,
            layup_name=layup_name, modify_func=modify_ply)
    # suppress needed to put the new properties to the input file
    original_layup.suppress()

    return elems_t, t_set


if __name__ == '__main__':
    cc = stds['desicos_study'].ccs[1]
    cc.created_model = False
    cc.create_model()
    part_nodes = mdb.models[cc.model_name].parts[cc.part_name_shell].nodes
    coords = np.array([n.coordinates for n in part_nodes])

    sf = 100

    path = r'C:\clones\desicos\desicos\conecylDB\files\dlr\degenhardt_2010_z20\degenhardt_2010_z20_msi_theta_z_imp.txt'
    H_measured = 510.
    H_model = 510.
    d, d, data = read_theta_z_imp(path=path,
                                  H_measured=H_measured,
                                  stretch_H=False,
                                  z_offset_bot=None)

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
    dist, ans = desicos.conecylDB.interpolate.inv_weighted(
            data, mesh_norm, ncp=10, power_parameter=1.5)

    alpharad = deg2rad(0.)
    trans = np.zeros_like(coords)
    trans[:, 0] = ans*cos(mesh[:, 0])*cos(alpharad)
    trans[:, 1] = ans*sin(mesh[:, 0])*cos(alpharad)
    trans[:, 2] = ans*sin(alpharad)

    meshNodeArray = part.nodes.sequenceFromLabels(
                        [n.label for n in part_nodes])
    cc.part.editNode(nodes=meshNodeArray,
                  coordinates=(coords + trans*100))
