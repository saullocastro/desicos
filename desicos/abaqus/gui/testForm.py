import os

import numpy
from abaqusGui import *

import testDB
import gui_defaults
reload(gui_defaults)
from desicos.logger import error
from desicos.abaqus.constants import TMP_DIR

# Note: The above form of the import statement is used for the prototype
# application to allow the module to be reloaded while the application is
# still running. In a non-prototype application you would use the form:
# from myDB import MyDB

#TODO ploads or cutouts lists to conecylDB in order to read the default values
#     for

#TODO implement second dialog box that will confirm OK or BACK to the main DB
#TODO implement progress bar along the creation of all models
#TODO find a way to save the study object and all the cc objects to
#     allow a following post-processing step
###########################################################################
# Class definition
###########################################################################
params = ['rbot', 'H', 'alphadeg','betadeg','omegadeg',
'betadegs','omegadegs','la','plyt',
'numel_r', 'elem_type',
'separate_load_steps', 'displ_controlled',
'axial_displ', 'axial_load', 'axial_step', 'pload_step',
'pressure_load', 'pressure_step',
#'Nxxtop', 'Nxxtop_vec',
'artificial_damping1', 'artificial_damping2',
'damping_factor1', 'minInc1', 'initialInc1', 'maxInc1', 'maxNumInc1',
'damping_factor2', 'minInc2', 'initialInc2', 'maxInc2', 'maxNumInc2',
'bc_fix_bottom_uR', 'bc_fix_bottom_v', 'bc_bottom_clamped',
'bc_fix_top_uR', 'bc_fix_top_v', 'bc_top_clamped',
'resin_add_BIR', 'resin_add_BOR',
'resin_add_TIR', 'resin_add_TOR',
'resin_E', 'resin_nu', 'resin_numel',
'resin_bot_h', 'resin_bir_w1', 'resin_bir_w2', 'resin_bor_w1', 'resin_bor_w2',
'resin_top_h', 'resin_tir_w1', 'resin_tir_w2', 'resin_tor_w1', 'resin_tor_w2',
'use_job_stopper',
'laminate','stack',
'allowables', 'timeInterval', 'stress_output',
'pl_num', 'd_num', 'ax_num', 'lbmi_num', 'cut_num',
'pl_table', 'd_table', 'ax_table', 'lbmi_table', 'cut_table',
'std_name',
'allowablesKey','laminapropKey','ccKey',
'last_loaded',
'post_put_in_Excel', 'post_open_Excel', 'post_outpath',
'ncpus', 'imp_ms', 'imp_ms_theta_z_format',
'imp_t_theta_z_format', 'imp_thick',
'imp_ms_stretch_H', 'imp_t_stretch_H',
'imp_ms_scalings', 'imp_t_scalings',
'imp_r_TOL', 'imp_ms_ncp', 'imp_t_ncp',
'imp_ms_power_parameter', 'imp_t_power_parameter',
'imp_ms_num_sec_z', 'imp_t_num_sec_z',
'imp_ms_rotatedeg', 'imp_t_rotatedeg',
'imp_num_sets']


class TestForm(AFXForm):
    """
    """
    def __init__(self, owner):

        # Construct the base class.
        #
        self.owner = owner
        AFXForm.__init__(self, owner)
        # Command
        #
        TRUE_FALSE = 1
        self.ID_DEL_OUT_FOLDER = 999
        FXMAPFUNC(self, SEL_COMMAND, self.ID_DEL_OUT_FOLDER,
                self.onCmdDelOutFolder)
        self.cmd = AFXGuiCommand(self, 'create_study', 'gui_commands')
        self.apply_imp_ms = AFXGuiCommand(self, 'apply_imp_ms', 'gui_commands')
        self.apply_imp_t = AFXGuiCommand(self, 'apply_imp_t', 'gui_commands')
        #
        self.dummy = AFXGuiCommand(self,  'dummy', 'gui_commands')
        #

        #
        self.std_nameKw = AFXStringKeyword(self.cmd, 'std_name', TRUE)
        self.rbotKw = AFXFloatKeyword(self.cmd, 'rbot', TRUE)
        self.HKw = AFXFloatKeyword(self.cmd, 'H', TRUE)
        self.alphadegKw = AFXFloatKeyword(self.cmd, 'alphadeg', TRUE)
        self.laKw = AFXIntKeyword(  self.cmd, 'la', TRUE)
        self.betadegKw = AFXFloatKeyword(self.cmd, 'betadeg', TRUE)
        self.omegadegKw = AFXFloatKeyword(self.cmd, 'omegadeg', TRUE)
        self.laminateKw = AFXTableKeyword(self.cmd, 'laminate', TRUE, 0, -1, AFXTABLE_TYPE_STRING)
        self.stackKw = AFXTableKeyword(self.dummy, 'stack', FALSE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.betadegsKw = AFXTableKeyword(self.cmd, 'betadegs', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.omegadegsKw = AFXTableKeyword(self.cmd, 'omegadegs', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.plytKw = AFXFloatKeyword(self.dummy, 'plyt', FALSE)
        self.elem_typeKw = AFXStringKeyword(self.cmd, 'elem_type', TRUE)
        self.numel_rKw = AFXIntKeyword(  self.cmd, 'numel_r', TRUE)

        self.separate_load_stepsKw = AFXBoolKeyword(self.cmd, 'separate_load_steps', TRUE_FALSE, TRUE)
        self.displ_controlledKw = AFXBoolKeyword(self.cmd, 'displ_controlled', TRUE_FALSE, TRUE)
        self.axial_displKw = AFXFloatKeyword(self.cmd, 'axial_displ', TRUE)
        self.axial_loadKw = AFXFloatKeyword(self.cmd, 'axial_load', TRUE)
        self.axial_stepKw = AFXIntKeyword(self.cmd, 'axial_step', TRUE)
        self.pressure_loadKw = AFXFloatKeyword(self.cmd, 'pressure_load', TRUE)
        self.pressure_stepKw = AFXIntKeyword(self.cmd, 'pressure_step', TRUE)
        self.pload_stepKw = AFXIntKeyword(self.cmd, 'pload_step', TRUE)

        self.artificial_damping1Kw = AFXBoolKeyword(self.cmd, 'artificial_damping1', TRUE_FALSE, TRUE)
        self.artificial_damping2Kw = AFXBoolKeyword(self.cmd, 'artificial_damping2', TRUE_FALSE, TRUE)
        self.damping_factor1Kw = AFXFloatKeyword(self.cmd, 'damping_factor1', TRUE)
        self.damping_factor2Kw = AFXFloatKeyword(self.cmd, 'damping_factor2', TRUE)
        self.minInc1Kw = AFXFloatKeyword(self.cmd, 'minInc1', TRUE)
        self.minInc2Kw = AFXFloatKeyword(self.cmd, 'minInc2', TRUE)
        self.initialInc1Kw = AFXFloatKeyword(self.cmd, 'initialInc1', TRUE)
        self.initialInc2Kw = AFXFloatKeyword(self.cmd, 'initialInc2', TRUE)
        self.maxInc1Kw = AFXFloatKeyword(self.cmd, 'maxInc1', TRUE)
        self.maxInc2Kw = AFXFloatKeyword(self.cmd, 'maxInc2', TRUE)
        self.maxNumInc1Kw = AFXFloatKeyword(self.cmd, 'maxNumInc1', TRUE)
        self.maxNumInc2Kw = AFXFloatKeyword(self.cmd, 'maxNumInc2', TRUE)
        self.ncpusKw = AFXIntKeyword(self.cmd, 'ncpus', TRUE)
        self.use_job_stopperKw = AFXBoolKeyword( self.dummy, 'use_job_stopper', TRUE_FALSE, TRUE)

        self.bc_fix_bottom_uRKw = AFXBoolKeyword(self.cmd, 'bc_fix_bottom_uR', TRUE_FALSE, TRUE)
        self.bc_fix_bottom_vKw = AFXBoolKeyword(self.cmd, 'bc_fix_bottom_v', TRUE_FALSE, TRUE)
        self.bc_bottom_clampedKw = AFXBoolKeyword(self.cmd, 'bc_bottom_clamped', TRUE_FALSE, TRUE)
        self.bc_fix_top_uRKw = AFXBoolKeyword(self.cmd, 'bc_fix_top_uR', TRUE_FALSE, TRUE)
        self.bc_fix_top_vKw = AFXBoolKeyword(self.cmd, 'bc_fix_top_v', TRUE_FALSE, TRUE)
        self.bc_top_clampedKw = AFXBoolKeyword(self.cmd, 'bc_top_clamped', TRUE_FALSE, TRUE)

        # resin rings
        self.resin_EKw = AFXFloatKeyword(self.cmd, 'resin_E', TRUE)
        self.resin_nuKw = AFXFloatKeyword(self.cmd, 'resin_nu', TRUE)
        self.resin_numelKw = AFXIntKeyword(self.cmd, 'resin_numel', TRUE)
        self.resin_add_BIRKw = AFXBoolKeyword(self.cmd, 'resin_add_BIR', TRUE_FALSE, TRUE)
        self.resin_add_BORKw = AFXBoolKeyword(self.cmd, 'resin_add_BOR', TRUE_FALSE, TRUE)
        self.resin_bot_hKw = AFXFloatKeyword(self.cmd, 'resin_bot_h', TRUE)
        self.resin_bir_w1Kw = AFXFloatKeyword(self.cmd, 'resin_bir_w1', TRUE)
        self.resin_bir_w2Kw = AFXFloatKeyword(self.cmd, 'resin_bir_w2', TRUE)
        self.resin_bor_w1Kw = AFXFloatKeyword(self.cmd, 'resin_bor_w1', TRUE)
        self.resin_bor_w2Kw = AFXFloatKeyword(self.cmd, 'resin_bor_w2', TRUE)
        self.resin_add_TIRKw = AFXBoolKeyword(self.cmd, 'resin_add_TIR', TRUE_FALSE, TRUE)
        self.resin_add_TORKw = AFXBoolKeyword(self.cmd, 'resin_add_TOR', TRUE_FALSE, TRUE)
        self.resin_top_hKw = AFXFloatKeyword(self.cmd, 'resin_top_h', TRUE)
        self.resin_tir_w1Kw = AFXFloatKeyword(self.cmd, 'resin_tir_w1', TRUE)
        self.resin_tir_w2Kw = AFXFloatKeyword(self.cmd, 'resin_tir_w2', TRUE)
        self.resin_tor_w1Kw = AFXFloatKeyword(self.cmd, 'resin_tor_w1', TRUE)
        self.resin_tor_w2Kw = AFXFloatKeyword(self.cmd, 'resin_tor_w2', TRUE)

        self.laminapropKw = AFXTupleKeyword(self.dummy, 'laminaprop',FALSE)
        self.allowablesKw = AFXTupleKeyword(self.cmd, 'allowables', TRUE)
        self.timeIntervalKw = AFXFloatKeyword(self.cmd, 'timeInterval', TRUE)
        self.stress_outputKw = AFXBoolKeyword(self.cmd,'stress_output', TRUE_FALSE, TRUE)
        self.pl_numKw = AFXIntKeyword(  self.cmd, 'pl_num', TRUE)
        self.d_numKw = AFXIntKeyword(  self.cmd, 'd_num', TRUE)
        self.ax_numKw = AFXIntKeyword(  self.cmd, 'ax_num', TRUE)
        self.lbmi_numKw = AFXIntKeyword(  self.cmd, 'lbmi_num', TRUE)
        self.cut_numKw = AFXIntKeyword(  self.cmd, 'cut_num', TRUE)
        self.pl_tableKw = AFXTableKeyword(self.cmd, 'pl_table', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.d_tableKw = AFXTableKeyword(self.cmd, 'd_table', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.ax_tableKw = AFXTableKeyword(self.cmd, 'ax_table', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.lbmi_tableKw = AFXTableKeyword(self.cmd, 'lbmi_table', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.cut_tableKw = AFXTableKeyword(self.cmd, 'cut_table', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        #
        #
        self.laminapropKeyKw = AFXStringKeyword(self.dummy, 'laminapropKey', FALSE)
        self.allowablesKeyKw = AFXStringKeyword(self.dummy, 'allowablesKey', FALSE)
        self.new_laminaprop_nameKw = AFXStringKeyword(self.dummy, 'new_laminaprop_name', FALSE)
        self.new_allowables_nameKw = AFXStringKeyword(self.dummy, 'new_allowables_name', FALSE)
        self.ccKeyKw = AFXStringKeyword(self.dummy, 'ccKey',FALSE)
        self.new_cc_nameKw = AFXStringKeyword(self.dummy, 'new_cc_name', FALSE)
        self.last_loadedKw = AFXStringKeyword(self.dummy, 'last_loaded', FALSE)
        self.std_to_postKw = AFXStringKeyword(self.dummy, 'std_to_post', FALSE)
        self.model_to_postKw = AFXStringKeyword(self.dummy, 'model_to_post', FALSE)
        self.post_put_in_ExcelKw = AFXBoolKeyword(self.dummy, 'post_put_in_Excel', TRUE_FALSE, FALSE)
        self.post_open_ExcelKw = AFXBoolKeyword(self.dummy, 'post_open_Excel', TRUE_FALSE, FALSE)
        self.post_outpathKw = AFXStringKeyword(self.dummy, 'post_outpath', FALSE)
        #
        self.imp_ms_std_nameKw = AFXStringKeyword(self.apply_imp_ms, 'std_name', TRUE)
        self.imp_msKw = AFXStringKeyword(self.apply_imp_ms, 'imp_ms', TRUE)
        self.imp_ms_stretch_HKw = AFXBoolKeyword(self.apply_imp_ms, 'imp_ms_stretch_H', TRUE_FALSE, TRUE)
        self.imp_ms_scalingsKw = AFXTableKeyword(self.apply_imp_ms, 'imp_ms_scalings', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.imp_r_TOLKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_r_TOL', TRUE)
        self.imp_ms_ncpKw = AFXIntKeyword(self.apply_imp_ms, 'imp_ms_ncp', TRUE)
        self.imp_ms_power_parameterKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_ms_power_parameter', TRUE)
        self.imp_ms_num_sec_zKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_ms_num_sec_z', TRUE)
        self.imp_ms_theta_z_formatKw = AFXBoolKeyword(self.apply_imp_ms, 'imp_ms_theta_z_format', TRUE_FALSE, TRUE)
        self.imp_ms_rotatedegKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_ms_rotatedeg', TRUE)
        #
        self.imp_t_std_nameKw = AFXStringKeyword(self.apply_imp_t, 'std_name', TRUE)
        self.imp_thickKw = AFXStringKeyword(self.apply_imp_t, 'imp_thick', TRUE)
        self.imp_num_setsKw = AFXIntKeyword(self.apply_imp_t, 'imp_num_sets', TRUE)
        self.imp_t_stretch_HKw = AFXBoolKeyword(self.apply_imp_t, 'imp_t_stretch_H', TRUE_FALSE, TRUE)
        self.imp_t_scalingsKw = AFXTableKeyword(self.apply_imp_t, 'imp_t_scalings', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.imp_t_ncpKw = AFXIntKeyword(self.apply_imp_t, 'imp_t_ncp', TRUE)
        self.imp_t_power_parameterKw = AFXFloatKeyword(self.apply_imp_t, 'imp_t_power_parameter', TRUE)
        self.imp_t_num_sec_zKw = AFXFloatKeyword(self.apply_imp_t, 'imp_t_num_sec_z', TRUE)
        self.imp_t_theta_z_formatKw = AFXBoolKeyword(self.apply_imp_t, 'imp_t_theta_z_format', TRUE_FALSE, TRUE)
        self.imp_t_rotatedegKw = AFXFloatKeyword(self.apply_imp_t, 'imp_t_rotatedeg', TRUE)
        self.loaded_study = False
        self.setDefault()


    def get_params_from_gui(self):
        params_from_gui = {}
        for param in params:
            paramKw = param + 'Kw'
            obj = getattr(self, paramKw)
            if obj.__class__.__name__.find('TableKeyword')> -1 \
            or obj.__class__.__name__.find('TupleKeyword')> -1:
                value = obj.getValues()
            else:
                value = obj.getValue()
            params_from_gui[param] = value
        return params_from_gui


    def read_params_from_gui(self, params_from_gui = {}):
        for param, value in params_from_gui.iteritems():
            paramKw = param + 'Kw'
            if getattr(self, paramKw, 'NOTFOUND')== 'NOTFOUND':
                continue
            obj = getattr(self, paramKw)
            if obj.__class__.__name__.find('TableKeyword')> -1 \
            or obj.__class__.__name__.find('TupleKeyword')> -1:
                obj.setValues(value)
            else:
                obj.setValue(value)
        #TODO
        # compatibility session
        # laminate from laminapropKeys, plyt, stack
        #
        if params_from_gui.get('laminate', None)==None:
            laminapropKeys = [self.laminapropKeyKw.getValue()]
            plyts = [self.plytKw.getValue()]
            stack = [float(i) for i in self.stackKw.getValues().split(',')]
            tmp = numpy.empty((40,3),dtype='|S50')
            tmp.fill('')
            tmp[:len(laminapropKeys),0] = laminapropKeys
            tmp[:len(plyts),1] = plyts
            tmp[:len(stack),2] = stack
            laminate = ','.join([str(tuple(i))for i in tmp])
            self.laminateKw.setValues(laminate)


    def setDefault(self,update_values=True, input_dict=None):
        using_defaults = False
        if input_dict == None:
            using_defaults = True
            input_dict = gui_defaults.defaults
        ignore_list = ['stack','laminate','ploads','laminaprop',
                        'allowables']
        for k, v in input_dict.iteritems():
            if k in ignore_list:
                continue
            if  (k == 'numel_r_linear' or k == 'numel_r_parabolic')\
            and using_defaults:
                if gui_defaults.defaults['elem_type'].find('S8')> -1:
                    v2 = gui_defaults.defaults['numel_r_parabolic']
                else:
                    v2 = gui_defaults.defaults['numel_r_linear']
                getattr(self, 'numel_rKw').setDefaultValue(v2)
                if update_values:
                    getattr(self, 'numel_rKw').setValueToDefault()
            else:
                if using_defaults:
                    v2 = gui_defaults.defaults[k]
                else:
                    v2 = v
                if isinstance(v2, unicode):
                    v2 = str(v2)
                attrname = k + 'Kw'
                if getattr(self, attrname, 'NotFound')<> 'NotFound':
                    getattr(self, attrname).setDefaultValue(v2)
                    if update_values:
                        getattr(self, attrname).setValueToDefault()


    def getFirstDialog(self):
        # Note: The style below is used for the prototype application to
        # allow the dialog to be reloaded while the application is
        # still running. In a non-prototype application you would use:
        #
        # return MyDB(self)

        # Reload the dialog module so that any changes to the dialog
        # are updated.
        #
        path = TMP_DIR
        sendCommand('import os')
        sendCommand('if not os.path.isdir(r"{0}"):\n'.format(path) +
                     '    os.makedirs(r"{0}")'.format(path))
        sendCommand('os.chdir(r"{0}")'.format(path))
        self.just_created_study = False
        reload(testDB)
        return testDB.TestDB(self)


    def issueCommands(self):
        self.laKw.setValue(self.db.lasw.getCurrent())
        a = self.cmd.getCommandString()
        a = a.replace(', ,',',False,')
        a = a.replace(', ,',',False,')
        a = a.replace(',)',',False)')
        a = a.replace('(,False','(False,False')
        b = ('import gui_commands\n'
             + 'reload(gui_commands)\n'
             + a)
        #if not os.path.isdir(r'C:\Temp'):
        #    os.makedirs(r'C:\Temp')
        #cmdpath = r'c:\Temp\cmd.py'
        #cmdfile = open(cmdpath,'w')
        #cmdfile.write(b + '\n')
        #cmdfile.close()
        with open(TMP_DIR + os.sep + 'tmpGUIcmd.py', 'w') as f:
            f.write(b)
        try:
            sendCommand(r'execfile(r"{0}\tmpGUIcmd.py")'.format(TMP_DIR),
                        writeToReplay=False, writeToJournal=True)
        except Exception as e:
            msg = r'ERROR: For debugging purposes run: execfile(r"{0}\tmpGUIcmd.py")'.format(TMP_DIR)
            sendCommand(r"""print(r'{0}')""".format(msg))
            raise RuntimeError(str(e) + '\n' + msg)
        self.just_created_study = True
        self.loaded_study = True
        outpath = os.path.join(TMP_DIR, self.std_nameKw.getValue())
        os.chdir(outpath)
        self.deactivateIfNeeded()
        return TRUE
        # Since this is a prototype application, just write the command to
        # the Message Area so it can be visually verified. If you have
        # defined a "real" command, then you can comment out this method to
        # have the command issued to the kernel.
        #
        # In a non-prototype application you normally do not need to write
        # the issueCommands()method.
        #
        #cmds = self.getCommandString()
        #getAFXApp().getAFXMainWindow().writeToMessageArea('TEST ' + cmds)
        #self.deactivateIfNeeded()
        #return TRUE


    def onCmdDelOutFolder(self, form, sender, sel, ptr):
        if sender.getPressedButtonId() == AFXDialog.ID_CLICKED_YES:
            std_name = self.std_to_postKw.getValue()
            command = ('import gui_commands\n' +
                       'reload(gui_commands)\n' +
                       'gui_commands.clean_output_folder("{0}")\n'.format(
                           std_name))
            sendCommand(command)
            path = os.path.join(TMP_DIR, std_name, 'outputs')
            if len(os.listdir(path)) == 0:
                text = 'Folder {0} has been cleaned!'.format(path)
            else:
                text = 'Some files in {0} cannot be removed!'.format(path)
            showAFXInformationDialog(self.db, text)
        else:
            pass
