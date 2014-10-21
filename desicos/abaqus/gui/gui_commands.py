import os
import multiprocessing
import subprocess

import __main__

import numpy

import desicos.abaqus.utils as utils
import desicos.conecylDB as conecylDB
import desicos.abaqus.conecyl as conecyl
import desicos.abaqus.study as study
from desicos.abaqus.constants import TMP_DIR

ccattrs = ['r','h','alphadeg','plyts',
'stack', 'numel_r', 'elem_type',
'axial_displ', 'axial_include', 'separate_load_steps',
'artificial_damping1', 'artificial_damping2',
'damping_factor1', 'minInc1', 'initialInc1', 'maxInc1', 'maxNumInc1',
'damping_factor2', 'minInc2', 'initialInc2', 'maxInc2', 'maxNumInc2',
'botU1', 'botU2', 'botU3', 'botUR1', 'botUR2', 'botUR3',
'topU1', 'topU2', 'topU3', 'topUR1', 'topUR2', 'topUR3',
'laminapropKeys', 'allowables', 'time_points', 'request_stress_output']

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

def post():
    pass

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
             ):
    #
    std = __main__.stds[std_name]
    start = 0
    if std.calc_Pcr:
        start = 1
    # The nodal_translations stores the first search to save time
    # it starts with None
    nodal_translations = None
    for i,scaling_factor in enumerate(imp_ms_scalings):
        scaling_factor = scaling_factor[0]
        if scaling_factor:
            cc = std.ccs[i+start]
            msi = cc.impconf.add_msi(imp_ms, scaling_factor)
            cc.impconf.rebuild()
            msi.stretch_H = imp_ms_stretch_H
            msi.use_theta_z_format = imp_ms_theta_z_format
            msi.r_TOL = imp_r_TOL
            msi.ncp = imp_ms_ncp
            msi.power_parameter = imp_ms_power_parameter
            msi.num_sec_z = imp_ms_num_sec_z
            msi.nodal_translations = nodal_translations
            nodal_translations = msi.create()

def apply_imp_t(
             std_name,
             imp_thick,
             imp_num_sets,
             imp_t_stretch_H,
             imp_t_scalings,
             imp_t_ncp,
             imp_t_power_parameter,
             imp_t_num_sec_z,
             imp_t_theta_z_format):
    #
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

def create_study(\
             std_name,
             r,
             h,
             alphadeg,
             la,
             laminate,
             elem_type,
             numel_r,
             axial_displ,
             axial_include,
             separate_load_steps,
             artificial_damping1,
             artificial_damping2,
             damping_factor1,
             damping_factor2,
             minInc1,
             minInc2,
             initialInc1,
             initialInc2,
             maxInc1,
             maxInc2,
             maxNumInc1,
             maxNumInc2,
             botU1,
             botU2,
             botU3,
             botUR1,
             botUR2,
             botUR3,
             topU1,
             topU2,
             topU3,
             topUR1,
             topUR2,
             topUR3,
             time_points,
             request_stress_output,
             pl_num,
             d_num,
             ax_num,
             lbmi_num,
             cut_num,
             use_job_stopper,
             allowables=None,
             pl_table=None,
             d_table=None,
             ax_table=None,
             lbmi_table=None,
             cut_table=None,
             betadeg=0.,
             omegadeg=0.,
             betadegs=None,
             omegadegs=None):

    imp_num = {}
    imp_num['pl']  = pl_num
    imp_num['d']   = d_num
    imp_num['ax']  = ax_num
    imp_num['lbmi']  = lbmi_num
    imp_num['cut'] = cut_num
    imp_tables = {}
    imp_tables['pl']  = pl_table
    imp_tables['d']   = d_table
    imp_tables['ax']  = ax_table
    imp_tables['lbmi']  = lbmi_table
    imp_tables['cut'] = cut_table
    num_params = {}
    num_params['pl']  = 2
    num_params['d']   = 4
    num_params['ax']  = 2
    num_params['lbmi']  = 1
    num_params['cut'] = 3
    num_models = 1
    for k in ['pl','d','ax','lbmi','cut']:
        if imp_num[k] == 0:
            continue
        imp_table = imp_tables[ k ]
        num_models = max(num_models, len(imp_table)-(num_params[k]+1))
    #
    # Cleaning up input values
    #
    # laminate
    laminate = numpy.array(laminate)
    stack = [float(i) for i in laminate[:,2] if i <> '']
    laminapropKeys = [i if i<>'' else laminate[0,0] \
                      for i in laminate[:len(stack),0]]
    plyts = [float(i) if i<>'' else float(laminate[0,1]) \
             for i in laminate[:len(stack),1]]
    #TODO currently only one allowable is allowed for stress analysis
    #allowablesKeys = [float(i) if i<>'' else laminate[0,3] \
    #         for i in laminate[:len(stack),1]]
    #
    # load asymmetry
    #
    #TODO list comprehension for these guys below
    if la == 0:
        betadegs = []
        omegadegs = []
    elif la == 1:
        betadegs  = [betadeg for i in range(num_models)]
        omegadegs = [omegadeg for i in range(num_models)]
    elif la == 2:
        if betadegs <> None:
            new_betadegs = []
            for betadeg in betadegs:
                if betadeg:
                    new_betadegs.append(betadeg[0])
            betadegs = new_betadegs
        else:
            betadegs = []
        if omegadegs <> None:
            new_omegadegs = []
            for omegadeg in omegadegs:
                if omegadeg:
                    new_omegadegs.append(omegadeg[0])
            omegadegs = new_omegadegs
        else:
            omegadegs = []
    num_models = max(num_models, len(betadegs), len(omegadegs))
    #
    std_name = find_std_name(std_name)
    #
    dirname = os.path.join(TMP_DIR, std_name, 'outputs')
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
    #
    #
    std = study.Study()
    std.use_job_stopper = use_job_stopper
    __main__.stds[ std_name ] = std
    std.name = std_name
    std.rebuild()
    for cc in std.ccs:
        cc.rebuilt = False
        cc.created_model = False
    locals_once = locals()
    for i in range(1,num_models+1):
        cc = conecyl.ConeCyl()
        for attr in ccattrs:
            setattr(cc, attr, locals_once[attr])
        # adding load asymmetry
        i_model = i-1
        if i_model < len(betadegs):
            cc.betadeg = betadegs[ i_model ]
        if i_model < len(omegadegs):
            cc.omegadeg = omegadegs[ i_model ]
        # adding perturbation loads
        i_model = i + num_params['pl']
        if i_model < len(pl_table):
            for j in range(imp_num['pl']):
                theta   = pl_table[0][j]
                pt      = pl_table[1][j]
                pltotal = pl_table[ i_model ][j]
                cc.impconf.add_pload(theta, pt, pltotal)
        # adding single buckles
        i_model = i + num_params['d']
        if i_model < len(d_table):
            for j in range(imp_num['d']):
                theta0 = d_table[0][j]
                z0     = d_table[1][j]
                a      = d_table[2][j]
                b      = d_table[3][j]
                wb     = d_table[ i_model ][j]
                cc.impconf.add_dimple(theta0, z0, a, b, wb)
        # adding axisymmetrics
        i_model = i + num_params['ax']
        if i_model < len(ax_table):
            for j in range(imp_num['ax']):
                z0 = ax_table[0][j]
                b  = ax_table[1][j]
                wb = ax_table[ i_model ][j]
                cc.impconf.add_axisymmetric(z0, b, wb)
        # adding linear buckling mode-shaped imperfections
        i_model = i + num_params['lbmi']
        if i_model < len(lbmi_table):
            for j in range(imp_num['lbmi']):
                mode = lbmi_table[0][j]
                scaling_factor = lbmi_table[ i_model ][j]
                cc.impconf.add_lbmi(mode, scaling_factor)
        # adding cutouts
        i_model = i + num_params['cut']
        if i_model < len(cut_table):
            for j in range(imp_num['cut']):
                theta = cut_table[0][j]
                pt    = cut_table[1][j]
                numel = cut_table[2][j]
                d     = cut_table[ i_model ][j]
                cc.create_cutout(theta, pt, d, numel)
        cc.rename = False
        cc.jobname = std.name + '_model_%02d' % i
        std.add_cc(cc)
    std.create_models(write_input_files=False)
    #for i in range(pload_num):
    #    num_models = max(len(pl_table),len(d_table),len(cut_table))
    return

def run_study(std_name, mult_cpus, use_job_stopper):
    cpu_num = multiprocessing.cpu_count()
    args = ['abaqus', 'python']
    args.append(os.path.join(TMP_DIR, std_name,
                 'run_' + std_name + '.py'))
    if mult_cpus:
        args.append('cpus=%d' % cpu_num)
    args.append('gui')
    if use_job_stopper:
        args.append('use_stopper')

    run_cmd = ' '.join(args)
    subprocess.Popen(run_cmd, shell=True)


def save_study(std_name, params_from_gui):
    stds = __main__.stds
    if not std_name in stds.keys():
        print 'Study has not been created!'
        print ' '
        return
    std = stds[ std_name ]
    std.params_from_gui = params_from_gui
    std.save()
    if not os.path.isdir(TMP_DIR):
        os.makedirs(TMP_DIR)
    os.chdir(TMP_DIR)
    __main__.mdb.saveAs(pathName = std_name + '.cae')
    print r'The DESICOS study has been saved to "%s.study".' \
          % os.path.join(std.tmp_dir, std_name)
    print ' '

def load_study(std_name):
    std = study.Study()
    std.tmp_dir = TMP_DIR
    std.name = std_name
    std = std.load()
    std_name = find_std_name(std_name)
    __main__.stds[ std_name ] = std
    __main__.openMdb(pathName = std_name + '.cae')
    vpname = __main__.session.currentViewportName
    __main__.session.viewports[ vpname ].setValues(displayedObject = None)
    mdb = __main__.mdb
    mod = mdb.models[ std_name + '_model_01']
    p = mod.parts['Cylinder']
    __main__.session.viewports[ vpname ].setValues(displayedObject = p)
    a = mod.rootAssembly
    a.regenerate()
    #
    for cc in std.ccs:
        if not cc.jobname in mdb.models.keys():
            print 'Could not load objects for model %s!' % cc.jobname
            continue
        cc.mod  = mdb.models[ cc.jobname ]
        cc.part = cc.mod.parts['Cylinder']
        utils.set_colors_ti(cc)

def load_study_gui(std_name, form):
    std = study.Study()
    std.tmp_dir = TMP_DIR
    std.name = std_name
    std = std.load()
    form.read_params_from_gui(std.params_from_gui)

