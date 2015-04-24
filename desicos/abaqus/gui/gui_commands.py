import os
import subprocess
import shutil
from itertools import chain

import __main__

import numpy as np

import desicos.abaqus.abaqus_functions as abaqus_functions
import desicos.conecylDB as conecylDB
import desicos.abaqus.conecyl as conecyl
import desicos.abaqus.study as study
from desicos.abaqus.constants import TMP_DIR
from desicos.conecylDB import fetch, save

ccattrs = ['rbot','H','alphadeg','plyts',
'stack', 'numel_r', 'elem_type',
'separate_load_steps', 'displ_controlled',
'axial_displ', 'axial_load', 'axial_step',
'pressure_load', 'pressure_step',
#'Nxxtop', 'Nxxtop_vec',
'damping_factor1', 'minInc1', 'initialInc1', 'maxInc1', 'maxNumInc1',
'damping_factor2', 'minInc2', 'initialInc2', 'maxInc2', 'maxNumInc2',
'bc_fix_bottom_uR', 'bc_fix_bottom_v', 'bc_bottom_clamped',
'bc_fix_bottom_side_uR', 'bc_fix_bottom_side_v', 'bc_fix_bottom_side_u3',
'bc_fix_top_uR', 'bc_fix_top_v', 'bc_top_clamped',
'bc_fix_top_side_uR', 'bc_fix_top_side_v', 'bc_fix_top_side_u3',
'resin_add_BIR', 'resin_add_BOR', 'resin_add_TIR', 'resin_add_TOR',
'use_DLR_bc',
'resin_E', 'resin_nu', 'resin_numel',
'resin_bot_h', 'resin_bir_w1', 'resin_bir_w2', 'resin_bor_w1', 'resin_bor_w2',
'resin_top_h', 'resin_tir_w1', 'resin_tir_w2', 'resin_tor_w1', 'resin_tor_w2',
'laminapropKeys', 'allowables', 'timeInterval', 'stress_output']


def find_std_name(std_name):
    #
    #TODO: avoid using try and except... how to find if .stds exists inside
    #      __main__
    try:
        if std_name in __main__.stds.keys():
            pass
    except:
        __main__.stds = {}
    return std_name


def command_wrapper(cmd):
    # Decorator function to provide error tracebacks from commands
    def new_cmd(*args, **kwargs):
        try:
            cmd(*args, **kwargs)
        except Exception, e:
            import traceback
            traceback.print_exc()
            raise
    return new_cmd


@command_wrapper
def apply_imp_ms(
             std_name,
             imp_ms,
             imp_ms_stretch_H,
             imp_ms_scalings,
             imp_r_TOL,
             imp_ms_ncp,
             imp_ms_power_parameter,
             imp_ms_num_sec_z,
             imp_ms_theta_z_format,
             imp_ms_rotatedeg,
             ):
    std = __main__.stds[std_name]
    start = 0
    if std.calc_Pcr:
        start = 1
    # The nodal_translations stores the first search to save time
    # it starts with None
    nodal_translations = None
    for i, scaling_factor in enumerate(imp_ms_scalings):
        scaling_factor = scaling_factor[0]
        if scaling_factor:
            cc = std.ccs[i+start]
            msi = cc.impconf.add_msi(
                                     imp_ms=imp_ms,
                                     scaling_factor=scaling_factor,
                                     rotatedeg=imp_ms_rotatedeg,
                                    )
            cc.impconf.rebuild()
            msi.stretch_H = imp_ms_stretch_H
            msi.use_theta_z_format = imp_ms_theta_z_format
            msi.r_TOL = imp_r_TOL
            msi.ncp = imp_ms_ncp
            msi.power_parameter = imp_ms_power_parameter
            msi.num_sec_z = imp_ms_num_sec_z
            msi.nodal_translations = nodal_translations
            nodal_translations = msi.create()


@command_wrapper
def apply_imp_t(
             std_name,
             imp_thick,
             imp_num_sets,
             imp_t_stretch_H,
             imp_t_scalings,
             imp_t_ncp,
             imp_t_power_parameter,
             imp_t_num_sec_z,
             imp_t_theta_z_format,
             imp_t_rotatedeg):
    std = __main__.stds[std_name]
    start = 0
    if std.calc_Pcr:
        start = 1
    # The nodal_translations stores the first search to save time
    # it starts with None
    elems_t = None
    t_set = None
    for i,scaling_factor in enumerate(imp_t_scalings):
        scaling_factor = scaling_factor[0]
        if scaling_factor:
            cc = std.ccs[i+start]
            ti = cc.impconf.add_ti(imp_thick, scaling_factor)
            cc.impconf.rebuild()
            ti.number_of_sets = imp_num_sets
            ti.stretch_H = imp_t_stretch_H
            ti.use_theta_z_format = imp_t_theta_z_format
            ti.ncp = imp_t_ncp
            ti.power_parameter = imp_t_power_parameter
            ti.num_sec_z = imp_t_num_sec_z
            ti.elems_t = elems_t
            ti.t_set = t_set
            elems_t, t_set = ti.create()


def create_study(**kwargs):
    # setting defaults
    pl_table = kwargs.get('pl_table')
    pload_step = kwargs.get('pload_step')
    d_table = kwargs.get('d_table')
    ax_table = kwargs.get('ax_table')
    lbmi_table = kwargs.get('lbmi_table')
    cut_table = kwargs.get('cut_table')
    ppi_enabled = kwargs.get('ppi_enabled')
    ppi_extra_height = kwargs.get('ppi_extra_height')
    ppi_table = kwargs.get('ppi_table')
    betadeg = kwargs.get('betadeg', 0.)
    omegadeg = kwargs.get('omegadeg', 0.)
    betadegs = kwargs.get('betadegs')
    omegadegs = kwargs.get('omegadegs')

    imp_num = {}
    imp_num['pl'] = kwargs.get('pl_num')
    imp_num['d'] = kwargs.get('d_num')
    imp_num['ax'] = kwargs.get('ax_num')
    imp_num['lbmi'] = kwargs.get('lbmi_num')
    imp_num['cut'] = kwargs.get('cut_num')
    imp_tables = {}
    imp_tables['pl'] = kwargs.get('pl_table')
    imp_tables['d'] = kwargs.get('d_table')
    imp_tables['ax'] = kwargs.get('ax_table')
    imp_tables['lbmi'] = kwargs.get('lbmi_table')
    imp_tables['cut'] = kwargs.get('cut_table')
    num_params = {}
    num_params['pl'] = 2
    num_params['d'] = 4
    num_params['ax'] = 2
    num_params['lbmi'] = 1
    num_params['cut'] = 3
    num_models = 1
    for k in ['pl','d','ax','lbmi','cut']:
        if imp_num[k] == 0:
            continue
        imp_table = imp_tables[k]
        num_models = max(num_models, len(imp_table)-(num_params[k]+1))
    #
    # Cleaning up input values
    #
    # laminate
    laminate = np.atleast_2d([i for i in kwargs.get('laminate') if i])
    kwargs['laminate'] = laminate
    kwargs['stack'] = [float(i) for i in laminate[:,2] if i != '']
    stack = kwargs['stack']
    kwargs['laminapropKeys'] = [i if i != '' else laminate[0,0]
                                for i in laminate[:len(stack),0]]
    kwargs['plyts'] = [float(i) if i != '' else float(laminate[0,1])
                       for i in laminate[:len(stack),1]]
    #TODO currently only one allowable is allowed for stress analysis
    kwargs['allowables'] = [kwargs['allowables'] for _ in stack]
    #allowablesKeys = [float(i) if i != '' else laminate[0,3] \
    #         for i in laminate[:len(stack),1]]
    #
    # load asymmetry
    #
    #TODO list comprehension for these guys below
    la = kwargs.get('la')
    if la == 0:
        betadegs = []
        omegadegs = []
    elif la == 1:
        betadegs  = [betadeg for i in range(num_models)]
        omegadegs = [omegadeg for i in range(num_models)]
    elif la == 2:
        if betadegs is not None:
            new_betadegs = []
            for betadeg in betadegs:
                if betadeg:
                    new_betadegs.append(betadeg[0])
            betadegs = new_betadegs
        else:
            betadegs = []
        if omegadegs is not None:
            new_omegadegs = []
            for omegadeg in omegadegs:
                if omegadeg:
                    new_omegadegs.append(omegadeg[0])
            omegadegs = new_omegadegs
        else:
            omegadegs = []
    num_models = max(num_models, len(betadegs), len(omegadegs))
    #
    # damping
    #
    if not kwargs['artificial_damping1']:
        kwargs['damping_factor1'] = None
    if not kwargs['artificial_damping2']:
        kwargs['damping_factor2'] = None
    #
    std_name = find_std_name(kwargs.get('std_name'))
    #
    dirname = os.path.join(TMP_DIR, std_name, 'outputs')
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    #
    #
    std = study.Study()
    __main__.stds[std_name] = std
    std.name = std_name
    std.rebuild()
    for cc in std.ccs:
        cc.rebuilt = False
        cc.created_model = False
    for i in range(1, num_models+1):
        cc = conecyl.ConeCyl()
        for attr in ccattrs:
            setattr(cc, attr, kwargs[attr])
        # adding load asymmetry
        i_model = i-1
        if i_model < len(betadegs):
            cc.betadeg = betadegs[i_model]
        if i_model < len(omegadegs):
            cc.omegadeg = omegadegs[i_model]
        # adding perturbation loads
        i_model = i + num_params['pl']
        if i_model < len(pl_table):
            for j in range(imp_num['pl']):
                theta   = pl_table[0][j]
                pt      = pl_table[1][j]
                pltotal = pl_table[i_model][j]
                cc.impconf.add_pload(theta, pt, pltotal, step=pload_step)
        # adding single buckles
        i_model = i + num_params['d']
        if i_model < len(d_table):
            for j in range(imp_num['d']):
                theta0 = d_table[0][j]
                z0     = d_table[1][j]
                a      = d_table[2][j]
                b      = d_table[3][j]
                wb     = d_table[i_model][j]
                cc.impconf.add_dimple(theta0, z0, a, b, wb)
        # adding axisymmetrics
        i_model = i + num_params['ax']
        if i_model < len(ax_table):
            for j in range(imp_num['ax']):
                z0 = ax_table[0][j]
                b  = ax_table[1][j]
                wb = ax_table[i_model][j]
                cc.impconf.add_axisymmetric(z0, b, wb)
        # adding linear buckling mode-shaped imperfections
        i_model = i + num_params['lbmi']
        if i_model < len(lbmi_table):
            for j in range(imp_num['lbmi']):
                mode = lbmi_table[0][j]
                scaling_factor = lbmi_table[i_model][j]
                cc.impconf.add_lbmi(mode, scaling_factor)
        # adding cutouts
        i_model = i + num_params['cut']
        if i_model < len(cut_table):
            for j in range(imp_num['cut']):
                theta = cut_table[0][j]
                pt    = cut_table[1][j]
                numel = cut_table[2][j]
                d     = cut_table[i_model][j]
                cc.create_cutout(theta, pt, d, numel)
        ## adding ply piece imperfection
        if ppi_enabled:
            info = []
            for row in ppi_table:
                if row is False:
                    continue # False may be appended if there is only one row
                keys = ['starting_position', 'rel_ang_offset', 'max_width', 'eccentricity']
                try:
                    info.append(dict((key, float(row[i])) for i, key in enumerate(keys) if row[i] != ''))
                except ValueError, e:
                    raise ValueError('Invalid non-numeric value in Ply Piece Imperfection table:' + e.message.split(':')[-1])
            cc.impconf.add_ppi(info, ppi_extra_height)
        std.add_cc(cc)
    std.create_models(write_input_files=False)
    #for i in range(pload_num):
    #    num_models = max(len(pl_table),len(d_table),len(cut_table))
    return


def run_study(std_name, ncpus, use_job_stopper):
    args = ['abaqus', 'python']
    args.append(os.path.join(TMP_DIR, std_name,
                 'run_' + std_name + '.py'))
    args.append('cpus={0:d}'.format(ncpus))
    args.append('gui')
    if use_job_stopper:
        args.append('use_stopper')

    run_cmd = ' '.join(args)
    subprocess.Popen(run_cmd, shell=True)


def clean_output_folder(std_name):
    stds = __main__.stds
    if not std_name in stds.keys():
        print('Study has not been created!')
        print('')
        return
    std = stds[std_name]
    cwd = os.getcwd()
    os.chdir(std.output_dir)
    try:
        if os.name == 'nt':
            os.system('move *.gaps ..')
            os.system('del /q *.*')
            os.system('move ..\*.gaps .')
        else:
            os.system('mv *.gaps ..')
            os.system('rm *.*')
            os.system('mv ..\*.gaps .')
    except:
        pass
    os.chdir(cwd)


def save_study(std_name, params_from_gui):
    stds = __main__.stds
    if not std_name in stds.keys():
        print('Study has not been created!')
        print(' ')
        return
    std = stds[std_name]
    std.params_from_gui = params_from_gui
    std.save()
    if not os.path.isdir(TMP_DIR):
        os.makedirs(TMP_DIR)
    os.chdir(TMP_DIR)
    __main__.mdb.saveAs(pathName = std_name + '.cae')
    print(r'The DESICOS study has been saved to "{0}.study".'.format(
          os.path.join(std.tmp_dir, std_name)))
    print(' ')


def load_study(std_name):
    std = study.Study()
    std.tmp_dir = TMP_DIR
    std.name = std_name
    std = std.load()
    std_name = find_std_name(std_name)
    __main__.stds[std_name] = std
    __main__.openMdb(pathName = std_name + '.cae')
    vpname = __main__.session.currentViewportName
    __main__.session.viewports[vpname].setValues(displayedObject = None)
    mdb = __main__.mdb
    if std.ccs[0].model_name in mdb.models.keys():
        mod = mdb.models[std.ccs[0].model_name]
        p = mod.parts['Shell']
        __main__.session.viewports[vpname].setValues(displayedObject = p)
        a = mod.rootAssembly
        a.regenerate()

    for cc in std.ccs:
        if not cc.model_name in mdb.models.keys():
            print('Could not load objects for model {0}!'.format(
                   cc.model_name))
            continue
        abaqus_functions.set_colors_ti(cc)


def get_new_key(which, key, value):
    # Given a DB key and value
    # Check whether value is already in the DB, if not add it
    # and return a key that can be used to reference to 'value'
    value = tuple(value) # Convert list to tuple, if needed
    existing = fetch(which)
    # Inverse mapping. Sorting keeps result reliable if there are duplicated values.
    inv_existing = dict((v, k) for k, v in sorted(existing.iteritems(), reverse=True))
    if key in existing and existing[key] == value:
        # Key already exists and with the correct value, reuse it
        return key
    if value in inv_existing:
        # There is already a name for this value in the DB, use it
        return str(inv_existing[value])
    # Find a new (not yet used) name and save in the DB
    new_key = key
    i = 1
    while new_key in existing:
        new_key = '{0}_{1:04d}'.format(key, i)
        i += 1
    save(which, new_key, value)
    return new_key


def reconstruct_params_from_gui(std):
    # First cc is often a linear one, so use the last cc as 'template'
    # XX - it is assumed that all other ccs use the same parameters
    cc = std.ccs[-1]
    params = {}
    for attr in ccattrs:
        if attr in ('laminapropKeys', 'allowables', 'stack', 'plyts',
                    'damping_factor1', 'damping_factor2'):
            continue
        value = getattr(cc, attr)
        params[attr] = value

    # Set artificial_dampingX and damping_factorX manually
    damping_attrs = [('damping_factor1', 'artificial_damping1'),
                     ('damping_factor2', 'artificial_damping2')]
    for damp_attr, art_attr in damping_attrs:
        value = getattr(cc, damp_attr)
        params[damp_attr] = value if (value is not None) else 0.
        params[art_attr] = value is not None

    # Prevent the GUI from complaining about unset parameters
    for attr in ('axial_load', 'axial_displ', 'pressure_load'):
        if params[attr] is None:
            params[attr] = 0

    # Set laminate properties
    if not (len(cc.laminaprops) == len(cc.stack) == len(cc.plyts) ==
            len(cc.laminapropKeys)):
        raise ValueError('Loaded ConeCyl object has inconsistent stack length!')
    laminapropKeys = []
    for key, value in zip(cc.laminapropKeys, cc.laminaprops):
        laminapropKeys.append(get_new_key('laminaprops', key, value))
    params['laminapropKey'] = laminapropKeys[0]
    # allowableKey is not saved, so reuse laminapropKey for the name
    # TODO: Per-ply allowables
    params['allowablesKey'] = get_new_key('allowables',
                cc.laminapropKeys[0], cc.allowables[0])

    # Construct laminate table
    # import here to avoid circular reference
    from testDB import NUM_PLIES, MAX_MODELS
    tmp = np.empty((NUM_PLIES, 3), dtype='|S50')
    tmp.fill('')
    tmp[:len(laminapropKeys),0] = laminapropKeys
    tmp[:len(cc.plyts),1] = cc.plyts
    tmp[:len(cc.stack),2] = cc.stack
    params['laminate'] = ','.join(['('+','.join(i)+')' for i in tmp])

    # Apply perturbation loads
    # TODO: other imperfections
    all_ploads = list(chain.from_iterable(cci.impconf.ploads for cci in std.ccs))
    all_ploads = map(lambda pl: (pl.thetadeg, pl.pt), all_ploads)
    # Filter duplicates, to obtain a list of unique pload parameter combinations
    seen = set()
    all_ploads = [x for x in all_ploads if not (x in seen or seen.add(x))]
    params['pl_num'] = len(all_ploads)
    nonlinear_ccs = filter(lambda cci: not cci.linear_buckling, std.ccs)
    # TODO: unduplicate magic numbers (here, in create_study and in testDB)
    # It'll only get worse when adding other imperfections as well
    if params['pl_num'] > 32:
        raise ValueError('Too many different perturbation load parameters')
    if len(nonlinear_ccs) > MAX_MODELS:
        raise ValueError('Too many different models')
    tmp = np.empty((len(nonlinear_ccs) + 3, 32), dtype='|S50')
    tmp.fill('')
    tmp[0,:len(all_ploads)] = [thetadeg for thetadeg, pt in all_ploads]
    tmp[1,:len(all_ploads)] = [pt for thetadeg, pt in all_ploads]
    for row, cci in enumerate(nonlinear_ccs, start=3):
        for pl in cci.impconf.ploads:
            assert (pl.thetadeg, pl.pt) in all_ploads
            tmp[row,all_ploads.index((pl.thetadeg, pl.pt))] = pl.pltotal
    params['pl_table'] = ','.join(['('+','.join(i)+')' for i in tmp])

    # Apply PPI
    ppi = cc.impconf.ppi
    if ppi is not None:
        params['ppi_enabled'] = True
        params['ppi_extra_height'] = ppi.extra_height
        tmp = np.empty((len(ppi.info), 4), dtype='|S50')
        keys = ['starting_position', 'rel_ang_offset', 'max_width', 'eccentricity']
        for i, info_dict in enumerate(ppi.info):
            tmp[i,:] = [str(info_dict.get(key, '')) for key in keys]
        params['ppi_table'] = ','.join(['('+','.join(i)+')' for i in tmp])
    else:
        params['ppi_table'] = ''

    params['std_name'] = std.name
    std.params_from_gui = params


def load_study_gui(std_name, form):
    std = study.Study()
    std.tmp_dir = TMP_DIR
    std.name = std_name
    std = std.load()
    saved_from_gui = len(std.params_from_gui) != 0
    if not saved_from_gui:
        reconstruct_params_from_gui(std)
        form.setDefault()
    form.read_params_from_gui(std.params_from_gui)
    return saved_from_gui

