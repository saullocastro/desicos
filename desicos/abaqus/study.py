"""
==========================================
Abaqus Study (:mod:`desicos.abaqus.study`)
==========================================

.. currentmodule:: desicos.abaqus.study

"""
import os
import shutil
import cPickle
import __main__

import numpy as np

from desicos.logger import *
from desicos.abaqus.constants import DAHOME, TMP_DIR, NUM_LB_MODES
from desicos.abaqus.conecyl import ConeCyl

class Study(object):
    """Study grouping many :class:`.ConeCyl` objects.

    The objective of this class is to save any study where different models
    are included in one ``.cae`` file. THe

    """
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
        self.study_dir = os.path.join(self.tmp_dir  , self.name)
        self.output_dir = os.path.join(self.study_dir, 'outputs')
        index = -1
        for cc in self.ccs:
            index += 1
            cc.index = index
            cc.study = self
            cc.tmp_dir = self.tmp_dir
            cc.study_dir = self.study_dir
            cc.output_dir = self.output_dir
            cc.rebuild()
        self.excel_name = os.path.join(self.study_dir,
                                       '{0}.xls'.format(self.name))

    def configure_folders(self):
        self.rebuild()
        log('configuring folders...')
        log(self.output_dir, level=1)
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    def save(self, path=''):
        """Save the current study

        Parameters
        ----------
        path : str, optional
            The study is saved into the ``self.tmp_dir`` folder if ``path`` is
            not given.

        """
        for cc in self.ccs:
            cc.prepare_to_save()
        if path=='':
            path = os.path.join(self.tmp_dir, self.name + '.study')
        with open(path, 'wb') as pfile:
            cPickle.dump(self, file=pfile, protocol=cPickle.HIGHEST_PROTOCOL)

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
        return self.load()

    def add_cc_from_DB(self, name):
        cc = ConeCyl()
        cc.from_DB(name)
        cc.index = len(self.ccs)
        self.ccs.append(cc)
        cc.rebuild(save_rebuild=False)
        return cc

    def add_cc(self, cc):
        self.ccs.append(cc)

    def write_inputs(self):
        for cc in self.ccs:
            cc.write_job(submit = False)
        self.create_run_file()
        os.chdir(self.tmp_dir)

    def create_models(self, write_input_files=True,
                      apply_msis=False, apply_tis=False):
        import desicos.abaqus.imperfections as imperfections

        self.rebuild()
        os.chdir(self.output_dir)
        if self.calc_Pcr and self.ccs[0].model_name[-3:] != '_lb':
            import copy
            cc_Pcr = copy.deepcopy(self.ccs[0])
            cc_Pcr.linear_buckling = True
            cc_Pcr.rename = False
            cc_Pcr.model_name = self.name + '_lb'
            self.ccs.insert(0, cc_Pcr)
            self.ccs[0].direct_ABD_input = False
            self.ccs[0].impconf = imperfections.ImpConf()
            self.ccs[0].impconf.conecyl = self.ccs[0]
        for cc in self.ccs:
            cc.create_model()
        if apply_msis:
            self.apply_msis()
        if apply_tis:
            self.apply_tis()
        if write_input_files:
            for cc in self.ccs:
                cc.write_job(submit = False)
        self.create_run_file()
        os.chdir(self.tmp_dir)

    def apply_msis(self):
        """Applies all geometric imperfections in this study

        It assumes the same :class:`.MSI` for all the :class:`ConeCyl` objects
        that are in the ``ccs`` container.

        """
        nodal_translations = None
        for cc in self.ccs:
            for msi in cc.impconf.msis:
                msi.nodal_translations = nodal_translations
                nodal_translations = msi.create()

    def apply_tis(self):
        """Applies all thickness imperfections in this study

        It assumes the same :class:`.TI` for all the :class:`ConeCyl` objects
        that are in the ``ccs`` container.

        """
        elems_t_dict = None
        t_set = None
        for cc in self.ccs:
            for ti in cc.impconf.tis:
                ti.elems_t_dict = elems_t_dict
                ti.t_set = t_set
                elems_t_dict, t_set = ti.create()

    def create_run_file(self):
        """Creates the run file which can be called from any Python

        The file is stored in the ``self.study_dir`` folder.

        """
        import desicos.abaqus.utils.jobs as jobs

        self.runnames = []
        for cc in self.ccs:
            self.runnames.append(cc.model_name)
        prefix = os.path.join(self.study_dir, 'run_' + self.name)
        self.run_file_name = prefix + '.py'
        tmpf = open(self.run_file_name, 'w')
        jobs.print_run_file(self.study_dir, self.runnames, tmpf)
        shutil.copy2(os.path.join(DAHOME, 'utils', 'job_stopper.py'),
                                  self.study_dir)
        tmpf.close()

    def open_excel(self):
        os.system(self.excel_name)

    def plot_forces(self, gui=False, put_in_Excel=True, open_Excel=False):
        import desicos.abaqus.utils as utils
        #print('I plot_forces study')
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
                names.append(cc.model_name)
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


    def plot_R1_forces(self, gui=False, put_in_Excel=True, open_Excel=False):
        import desicos.abaqus.utils as utils

        sheet_names = ['R1_curves','R1_curves_norm']
        x_labels = ['STH, mm', 'End-Shortening']
        y_labels = ['Reaction Load, kN' , 'Radial Reaction Load']
        for curve_num in range(2):
            curves = []
            names = []
            #counter=0
            for cc in self.ccs:
                ok = cc.read_outputs()
                #print('Reading '+str(counter))
                if not ok:
                    continue
                curve = cc.plot_R1_forces(gui=gui)[curve_num]
                curves.append(curve)
                names.append(cc.model_name)
                #counter=counter+1
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


    def plot_RF1U3_forces(self, gui=False, put_in_Excel=True, open_Excel=False):
        import desicos.abaqus.utils as utils

        sheet_names = ['RF1U3_curves','RF1U3_curves_norm']
        x_labels = ['STH, mm', 'End-Shortening']
        y_labels = ['Reaction Load, kN' , 'Radial Reaction Load']
        for curve_num in range(2):
            curves = []
            names = []
            #counter=0
            for cc in self.ccs:
                ok = cc.read_outputs()
                #print('Reading '+str(counter))
                if not ok:
                    continue
                curve = cc.plot_RF1U3_forces(gui=gui)[curve_num]
                curves.append(curve)
                names.append(cc.model_name)
                #counter=counter+1
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
              put_in_Excel = True,
              open_Excel = False,
              global_second = False):
        import desicos.abaqus.utils as utils
        import abaqus_functions

        for cc in self.ccs:
            cc.outputs_ok = cc.read_outputs()
        laminate_t = sum(t for t in self.ccs[0].plyts)
        session = __main__.session
        numcharts = 4

        if self.calc_Pcr == False:
            calc_Pcr = False
            numcharts = 2
            start = 0
        else:
            calc_Pcr = True
            pcr_kN = 0.001*self.ccs[0].zload[0]
            start = 1

        curves_dict = {}
        limit = len(self.ccs[start].impconf.imperfections)
        for i in range(limit):
            imp_ref = self.ccs[start].impconf.imperfections[i]
            if not any(cc.impconf.imperfections[i] for cc in self.ccs[start:]):
                warn("imperfection '{0}' is zero for all ConeCyl objects, skipping...".format(
                     imp_ref.name))
                continue
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
                            imp = cc.impconf.imperfections[i]
                            imp_xaxis = getattr(imp, imp.xaxis)
                            amplitude = imp.calc_amplitude()
                        else:
                            imp_xaxis = getattr(imp_ref, imp_ref.xaxis)
                            amplitude = 0.
                        #
                        curve.append((imp_xaxis, 0.001 * b_load))
                        curve_amp.append((amplitude, 0.001 * b_load))
                    elif not cc.outputs_ok:
                        warn('error in {0}.odb, skipping...'.format(
                             cc.model_name))

                #
                # sorting curves
                curve.sort(key = lambda x: x[0])
                curve_amp.sort(key = lambda x: x[0])
                #
                #
                yaxis_label = 'Reaction Load, kN'
                name = '{0}_imp_{1:02d}_KD_curve_{2}'.format(self.name, i, pre)
                curves_dict[name] = [xaxis_label, yaxis_label, curve]
                session.XYData( name = name, data = curve, xValuesLabel =
                        xaxis_label, yValuesLabel = yaxis_label, legendLabel
                        = imp_ref.name)
                name = '{0}_imp_{1:02d}_KD_curve_{2}_amplitude'.format(
                       self.name, i, pre)

                curves_dict[name] = ['Imperfection amplitude, mm',
                                       yaxis_label, curve_amp]
                session.XYData(name=name, data=curve_amp,
                        xValuesLabel='Imperfection amplitude, mm',
                        yValuesLabel=yaxis_label, legendLabel=imp_ref.name,)
                if calc_Pcr:
                    yaxis_label = 'Knock-Down Factor (P/Pcr)'
                    name = '{0}_imp_{1:02d}_norm_KD_curve_{2}'.format(
                           self.name, i, pre)
                    norm_curve = np.array(curve)
                    norm_curve[:,1] /= pcr_kN
                    curves_dict[name] = [xaxis_label, yaxis_label, norm_curve]
                    session.XYData(name=name, data=norm_curve,
                            xValuesLabel=xaxis_label,
                            yValuesLabel=yaxis_label,
                            legendLabel=imp_ref.name)
                    name = ('{0}_imp_{1:02d}_norm_KD_curve_{2}_amplitude'.
                            format(self.name, i, pre))
                    norm_curve_amp = np.array(curve_amp)
                    norm_curve_amp[:,0] /= laminate_t
                    norm_curve_amp[:,1] /= pcr_kN
                    curves_dict[name] = ['Imperfection amplitude / laminate thickness',
                                           yaxis_label,
                                           norm_curve_amp]
                    session.XYData(name=name, data=norm_curve_amp,
                xValuesLabel='Imperfection amplitude / laminate thickness',
                yValuesLabel=yaxis_label, legendLabel=imp_ref.name)
        if configure_session:
            abaqus_functions.configure_session(session=session)

        if put_in_Excel:
            sheet_name = 'kd_curves'
            keys = curves_dict.keys()
            keys.sort()
            book, sheet = utils.get_book_sheet(self.excel_name, sheet_name)
            for i, name in enumerate(keys):
                value = curves_dict[name]
                xaxis_label = value[0]
                yaxis_label = value[1]
                curve = value[2]
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

