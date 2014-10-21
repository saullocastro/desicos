import os
import shutil
import cPickle
import __main__

import numpy as np

import desicos.abaqus.utils as utils
import desicos.abaqus.utils.jobs as jobs
from desicos.abaqus.constants import DAHOME, TMP_DIR, NUM_LB_MODES
from desicos.abaqus.conecyl import ConeCyl

def estimate_P1(plcurve):
    [(x1,y1),(x2,y2),(x3,y3)] = plcurve[:3]
    [(x4,y4),(x5,y5),(x6,y6)] = plcurve[-3:]
    c1 = np.poly1d(np.polyfit([x1,x2,x3],[y1,y2,y3],1))
    c2 = np.poly1d(np.polyfit([x4,x5,x6],[y4,y5,y6],1))
    m1 = np.array([[c1.coeffs[0], -1], [c2.coeffs[0], -1]])
    m2 = np.array([[-c1.coeffs[1]], [-c2.coeffs[1]]])
    p1 = float(np.linalg.solve(m1, m2)[0])
    return p1

class Studies(object):

    def __init__(self):
        self.name = ''
        self.tmp_dir = TMP_DIR
        self.studies = []

    def save(self, path=''):
        for std in self.studies:
            for cc in std.ccs:
                cc.prepare_to_save()
        #
        if path == '':
            path = os.path.join(self.tmp_dir, self.name + '.studies')
        pfile = open(path, 'wb')
        cPickle.dump(self, file=pfile, protocol=cPickle.HIGHEST_PROTOCOL)
        pfile.close()

    def load(self, path=''):
        if path == '':
            path = os.path.join(self.tmp_dir, self.name + '.studies')
        pfile = open(path, 'rb')
        new_std = cPickle.load(pfile)
        pfile.close()
        return new_std

    def load_by_name(self, name):
        self.name = name
        self.load()

class Study(object):

    def __init__(self):
        self.name = ''
        self.tmp_dir = TMP_DIR
        self.ccs = [] # ccs --> conecyls - conecylinders
        self.runnames = []
        self.study_dir  = ''
        self.output_dir = ''
        self.run_file_name = ''
        self.params_from_gui = {}
        self.p1 = None
        self.calc_Pcr = True
        self.kd_curves = None

    def __getitem__(self, i):
        return self.ccs[i]

    def __setitem__(self, i, v):
        self.ccs[i] = v

    def rebuild(self):
        self.study_dir  = os.path.join(self.tmp_dir  , self.name)
        self.output_dir = os.path.join(self.study_dir, 'outputs')
        index = -1
        for cc in self.ccs:
            index += 1
            cc.index = index
            cc.study = self
            cc.tmp_dir = self.tmp_dir
            cc.study_dir = self.study_dir
            cc.output_dir = self.output_dir
        self.excel_name = os.path.join(self.study_dir, '%s.xls' %self.name)

    def get_ccs(self):
        '''The idea here was to use always get_ccs to give a list of valid ccs,
        but it is still not used...
        '''
        pass

    def reset_folders(self):
        pass

    def configure_folders(self):
        self.rebuild()
        print 'configuring folders...'
        print '\t' + self.output_dir
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    def save(self, path=''):
        for cc in self.ccs:
            cc.prepare_to_save()
        #
        if path == '':
            path = os.path.join(self.tmp_dir, self.name + '.study')
        pfile = open(path, 'wb')
        cPickle.dump(self, file=pfile, protocol=cPickle.HIGHEST_PROTOCOL)
        pfile.close()
        mdb = __main__.mdb
        for cc in self.ccs:
            if not cc.jobname in mdb.models.keys():
                print 'Could not load objects for model %s!' % cc.jobname
                continue
            cc.mod = mdb.models[ cc.jobname ]
            cc.part = cc.mod.parts['Cylinder']

    def load(self, path=''):
        if path == '':
            path = os.path.join(self.tmp_dir, self.name + '.study')
        pfile = open(path, 'rb')
        new_std = cPickle.load(pfile)
        pfile.close()
        return new_std

    def load_by_name(self, name):
        self.name = name
        self.rebuild()
        self.load()

    def add_cc_fromDB(self, name):
        cc = ConeCyl()
        cc.fromDB(name)
        cc.index = len(self.ccs)
        self.ccs.append(cc)
        self.rebuild()
        return cc

    def add_cc(self, cc):
        self.ccs.append(cc)

    def write_inputs(self):
        for cc in self.ccs:
            cc.write_job(submit = False)
        self.create_run_file()
        os.chdir(self.tmp_dir)

    def create_models(self, write_input_files=True,
                       apply_msis=False, apply_tis=False,
                       run_rsm=True):
        self.rebuild()
        os.chdir(self.output_dir)
        if self.calc_Pcr and self.ccs[0].jobname[-3:] <> '_lb':
            import copy
            cc_Pcr = copy.deepcopy(self.ccs[0])
            cc_Pcr.linear_buckling = True
            cc_Pcr.rename = False
            cc_Pcr.jobname = self.name + '_lb'
            self.ccs.insert(0, cc_Pcr)
            self.ccs[0].rsm = False
            self.ccs[0].direct_ABD_input = False
            #TODO move this to ImpConf class
            #TODO cutouts should be considered an imperfection inside
            #     ImpConf later on...
            #TODO this is not really necessary since in
            #     _create_mesh_load_BC.py the imperfections are not created
            #     if cc.linear_buckling = True
            self.ccs[0].cutouts = []
            self.ccs[0].impconf.imperfections = []
            self.ccs[0].impconf.axisymmetrics = []
            self.ccs[0].impconf.dimples = []
            self.ccs[0].impconf.lbmis = []
            self.ccs[0].impconf.ploads = []
            self.ccs[0].impconf.msis = []
            self.ccs[0].impconf.tis = []
        for cc in self.ccs:
            cc.create_model()
        if self.ccs[1].rsm and run_rsm:
            from conecyl._imperfections.rsm import run_LB_read_PDs
            print 'RSM - running Abaqus to calculate the linear buckling modes'
            self.ccs[0].write_job(submit = True)
            run_LB_read_PDs(self)
        if apply_msis: self.apply_msis()
        if apply_tis:  self.apply_tis()
        if write_input_files:
            for cc in self.ccs:
                cc.write_job(submit = False)
        self.create_run_file()
        os.chdir(self.tmp_dir)

    def apply_msis(self):
        '''Applies all msis in this study
            - assumes the same msi for all ccs
        '''
        nodal_translations = None
        for cc in self.ccs:
            for msi in cc.impconf.msis:
                msi.nodal_translations = nodal_translations
                nodal_translations = msi.create()

    def apply_tis(self):
        '''Applies all tis in this study
            - assumes the same ti for all ccs
        '''
        elems_t_dict = None
        t_set = None
        for cc in self.ccs:
            for ti in cc.impconf.tis:
                ti.elems_t_dict = elems_t_dict
                ti.t_set = t_set
                elems_t_dict, t_set = ti.create()

    def create_run_file(self):
        self.runnames = []
        for cc in self.ccs:
            self.runnames.append(cc.jobname)
        #
        prefix = os.path.join(self.study_dir, 'run_' + self.name)
        self.run_file_name = prefix + '.py'
        tmpf = open(self.run_file_name, 'w')
        jobs.print_waitForCompletion(self.study_dir, self.runnames, tmpf)
        shutil.copy2(os.path.join(DAHOME, 'utils', 'job_stopper.py'),
                                  self.study_dir)
        tmpf.close()

    def calc_p1(self, step_num = 2):
        #
        for i in range(len(self.ccs[0].impconf.imperfections)):
            imp = self.ccs[0].impconf.imperfections[i]
            tmp_PLc = []
            for cc in self.ccs:
                cc.read_axial_load_displ(self, step_num)
                imp = cc.impconf.imperfections[ i ]
                imp_xaxis = getattr(imp, imp.xaxis)
                tmp_PLc.append((imp_xaxis, max(cc.zload)))
            # estimated P1
            self.p1 = estimate_P1(tmp_PLc)
        return self.p1

    def save_curves(self):
        import save_curves
        save_curves.save_curves(self)

    def open_excel(self):
        os.system(self.excel_name)

    def plot_forces(self, gui=False, put_in_Excel=True, open_Excel=False):
        sheet_names = ['load_short_curves','load_short_curves_norm']
        x_labels = ['End-Shortening, mm', 'Normalized End-Shortening']
        y_labels = ['Reaction Load, kN' , 'Normalized Reaction Load']
        for curve_num in range(2):
            curves = []
            names = []
            for cc in self.ccs:
                ok = cc.read_outputs()
                if not ok:
                    continue
                curve = cc.plot_forces(gui=gui)[curve_num]
                curves.append(curve)
                names.append(cc.jobname)
            if put_in_Excel:
                sheet_name = sheet_names[curve_num]
                book, sheet = utils.get_book_sheet(self.excel_name, sheet_name)
                for i,curve in enumerate(curves):
                    sheet.write(0, 0 + i*2, names[i])
                    sheet.write(1, 0 + i*2, x_labels[curve_num])
                    sheet.write(1, 1 + i*2, y_labels[curve_num])
                    for j, xy in enumerate(curve):
                        sheet.write(j+2, 0 + i*2, xy[0])
                        sheet.write(j+2, 1 + i*2, xy[1])
                book.save(self.excel_name)
                del book
        if put_in_Excel and open_Excel:
            self.open_excel()

    def plot(self,
              configure_session = False,
              gui = False,
              put_in_Excel   = True,
              open_Excel     = False,
              global_second  = False):
        for cc in self.ccs:
            cc.outputs_ok = cc.read_outputs()
        laminate_t = sum(t for t in self.ccs[0].plyts)
        import abaqus_functions
        session = __main__.session
        numcharts = 4
        # preventing compatibility problems with older versions
        if getattr(self, 'calc_Pcr', 'NOTFOUND') <> 'NOTFOUND':
            if self.calc_Pcr == False:
                calc_Pcr = False
                numcharts = 2
                start = 0
            else:
                calc_Pcr = True
                pcr_kN = 0.001*self.ccs[0].zload[0]
                start = 1
        else:
            calc_Pcr = False
            numcharts = 2
        curves_dict = {}
        limit = len(self.ccs[start].impconf.imperfections)
        for i in range(limit):
            imp_ref = self.ccs[start].impconf.imperfections[i]
            xaxis_label = imp_ref.xaxis_label
            for pre in ['fb','gb']:
                curve = []
                curve_amp = []
                for cc in self.ccs[start:]:
                    #
                    if cc.check_completed() and cc.outputs_ok:
                        if pre == 'fb':
                            b_load = utils.find_fb_load(cc.zload)
                        else:
                            b_load = max(cc.zload)
                        if i < len(cc.impconf.imperfections):
                            imp = cc.impconf.imperfections[ i ]
                            imp_xaxis = getattr(imp, imp.xaxis)
                            amplitude = imp.amplitude
                        else:
                            imp_xaxis = getattr(imp_ref, imp_ref.xaxis)
                            amplitude = 0.
                        #
                        curve.append(   (imp_xaxis, 0.001 * b_load))
                        curve_amp.append((amplitude, 0.001 * b_load))
                    elif not cc.outputs_ok:
                        print 'WARNING - error in %s.odb, skipping...' % cc.jobname

                #
                # sorting curves
                curve.sort(key = lambda x: x[0])
                curve_amp.sort(key = lambda x: x[0])
                #
                #
                yaxis_label = 'Reaction Load, kN'
                name = '%s_imp_%02d_KD_curve_%s' % (self.name, i, pre)
                curves_dict[ name ] = [xaxis_label, yaxis_label, curve]
                session.XYData(\
                    name = name,
                    data = curve,
                    xValuesLabel = xaxis_label,
                    yValuesLabel = yaxis_label,
                    legendLabel  = imp_ref.name)
                name = '%s_imp_%02d_KD_curve_%s_amplitude' % (self.name, i, pre)

                curves_dict[ name ] = ['Imperfection amplitude, mm',
                                       yaxis_label, curve_amp]
                session.XYData(\
                    name = name,
                    data = curve_amp,
                    xValuesLabel = 'Imperfection amplitude, mm',
                    yValuesLabel = yaxis_label,
                    legendLabel  = imp_ref.name,)
                if calc_Pcr:
                    yaxis_label = 'Knock-Down Factor (P/Pcr)'
                    name = '%s_imp_%02d_norm_KD_curve_%s' % (self.name, i, pre)
                    norm_curve = np.array(curve)
                    norm_curve[:,1] /= pcr_kN
                    curves_dict[ name ] = [xaxis_label,
                                           yaxis_label,
                                           norm_curve]
                    session.XYData(\
                        name = name,
                        data = norm_curve,
                        xValuesLabel = xaxis_label,
                        yValuesLabel = yaxis_label,
                        legendLabel  = imp_ref.name)
                    name = '%s_imp_%02d_norm_KD_curve_%s_amplitude' % (self.name, i, pre)
                    norm_curve_amp = np.array(curve_amp)
                    norm_curve_amp[:,0] /= laminate_t
                    norm_curve_amp[:,1] /= pcr_kN
                    curves_dict[ name ] = ['Imperfection amplitude / laminate thickness',
                                           yaxis_label,
                                           norm_curve_amp]
                    session.XYData(\
                        name = name,
                        data = norm_curve_amp,
                        xValuesLabel = 'Imperfection amplitude / laminate thickness',
                        yValuesLabel = yaxis_label,
                        legendLabel  = imp_ref.name,)
        if configure_session:
            abaqus_functions.configure_session(session = session)

        if put_in_Excel:
            sheet_name = 'kd_curves'
            keys = curves_dict.keys()
            keys.sort()
            book, sheet = utils.get_book_sheet(self.excel_name, sheet_name)
            for i, name in enumerate(keys):
                value = curves_dict[ name ]
                xaxis_label = value[0]
                yaxis_label = value[1]
                curve       = value[2]
                sheet.write(0,0 + i*2, name)
                sheet.write(1,0 + i*2, xaxis_label)
                sheet.write(1,1 + i*2, yaxis_label)
                for j, xy in enumerate(curve):
                    sheet.write(j+2,0 + i*2,xy[0])
                    sheet.write(j+2,1 + i*2,xy[1])
                book.save(self.excel_name)
            del book
            if open_Excel:
                self.open_excel()
        self.kd_curves = curves_dict

    def plot_rsm(self):
        '''See Sosa et al., 2006. There are two plots: one in which, for each
        buckling mode, the reduction factor is increased; and in the other, for
        each reduction factor the buckling mode is increased
        '''
        session = __main__.session
        ener_refs = {}
        plot1_ccs = {}
        plot2_ccs = {}
        for cc in self.ccs[1:]:
            print cc.jobname
            cc.read_outputs()
            ener_total = cc.ener_total
            mode = cc.rsm_mode
            mode_str = '%02d' % mode
            rf   = cc.rsm_reduction_factor
            rf_str = '%06d' % rf
            if not mode_str in plot1_ccs.keys():
                ener_refs[mode_str] = ener_total
                plot1_ccs[mode_str] = {}
                plot1_ccs[mode_str]['x'] = [rf]
                plot1_ccs[mode_str]['y'] = [ener_total]
            else:
                plot1_ccs[mode_str]['x'].append(rf)
                plot1_ccs[mode_str]['y'].append(ener_total)
            if not rf_str in plot2_ccs.keys():
                ener_refs[rf_str]  = ener_total
                plot2_ccs[rf_str] = {}
                plot2_ccs[rf_str]['x'] = [mode]
                plot2_ccs[rf_str]['y'] = [ener_total]
            else:
                plot2_ccs[rf_str]['x'].append(mode)
                plot2_ccs[rf_str]['y'].append(ener_total)

        for mode_str in plot1_ccs.keys():
            rfs = plot1_ccs[mode_str]['x']
            ener_totals = plot1_ccs[mode_str]['y']
            xaxis_label = 'reduction factor'
            yaxis_label = 'Energy Density'
            name = 'RSM_mode_' + mode_str
            session.XYData(name = name,
                            data = zip(rfs,ener_totals),
                            xValuesLabel = xaxis_label,
                            yValuesLabel = yaxis_label,
                            legendLabel  = 'mode %02d' % int(mode_str))

        #KDF
        for mode_str in plot1_ccs.keys():
            rfs = plot1_ccs[mode_str]['x']
            ener_ref = ener_refs[mode_str]
            ener_totals = [ y/ener_ref for y in plot1_ccs[mode_str]['y'] ]
            xaxis_label = 'reduction factor'
            yaxis_label = 'Knock-Down Factor'
            name = 'RSM_KDF_mode_' + mode_str
            session.XYData(name = name,
                            data = zip(rfs,ener_totals),
                            xValuesLabel = xaxis_label,
                            yValuesLabel = yaxis_label,
                            legendLabel  = 'mode %02d' % int(mode_str))

        for rf_str in plot2_ccs.keys():
            modes = plot2_ccs[rf_str]['x']
            ener_ref = ener_refs[rf_str]
            ener_totals = plot2_ccs[rf_str]['y']
            xaxis_label = 'Mode i'
            yaxis_label = 'Energy Density'
            name = 'RSM_rf_' + rf_str
            session.XYData(name = name,
                           data = zip(modes,ener_totals),
                           xValuesLabel = xaxis_label,
                           yValuesLabel = yaxis_label,
                           legendLabel  = 'rf %06d' % int(rf_str))



