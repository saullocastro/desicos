import os
import __main__

import numpy
from abaqusGui import *

import testDB
import gui_defaults
reload(gui_defaults)
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
params = ['r', 'h', 'alphadeg','betadeg','omegadeg',
'betadegs','omegadegs','la','plyt',
'numel_r', 'elem_type',
'axial_displ', 'axial_include', 'separate_load_steps',
'artificial_damping1', 'artificial_damping2',
'damping_factor1', 'minInc1', 'initialInc1', 'maxInc1', 'maxNumInc1',
'damping_factor2', 'minInc2', 'initialInc2', 'maxInc2', 'maxNumInc2',
'botU1', 'botU2', 'botU3', 'botUR1', 'botUR2', 'botUR3',
'topU1', 'topU2', 'topU3', 'topUR1', 'topUR2', 'topUR3',
'use_job_stopper',
'laminate','stack',
'allowables', 'time_points', 'request_stress_output',
'pl_num', 'd_num', 'ax_num', 'lbmi_num', 'cut_num',
'pl_table', 'd_table', 'ax_table', 'lbmi_table', 'cut_table',
'std_name',
'allowablesKey','laminapropKey','ccKey',
'last_loaded',
'post_put_in_Excel', 'post_open_Excel',
'mult_cpus', 'imp_ms', 'imp_ms_theta_z_format',
'imp_t_theta_z_format', 'imp_thick',
'imp_ms_std', 'imp_t_std',
'imp_ms_stretch_H', 'imp_t_stretch_H',
'imp_ms_scalings', 'imp_t_scalings',
'imp_r_TOL', 'imp_ms_ncp', 'imp_t_ncp',
'imp_ms_power_parameter', 'imp_t_power_parameter',
'imp_ms_num_sec_z', 'imp_t_num_sec_z',
'imp_num_sets']
class TestForm(AFXForm):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, owner):

        # Construct the base class.
        #
        AFXForm.__init__(self, owner)
        self.__main__ = __main__
        # Command
        #
        #self.cmd = AFXGuiCommand(self, 'myCommand', 'myObject')
        #self.kw1 = AFXStringKeyword(self.cmd, 'kw1', TRUE)
        #self.kw2 = AFXIntKeyword(self.cmd, 'kw2', TRUE)
        #self.kw3 = AFXFloatKeyword(self.cmd, 'kw3', TRUE)
        TRUE_FALSE = 1
        self.cmd = AFXGuiCommand(self, 'create_study', 'gui_commands')
        #TODO use the getCommandString()of AFXGuiCommand for these two too...
        self.apply_imp_ms = AFXGuiCommand(self, 'apply_imp_ms', 'gui_commands')
        self.apply_imp_t  = AFXGuiCommand(self, 'apply_imp_t', 'gui_commands')
        #
        self.dummy = AFXGuiCommand(self,  'dummy', 'gui_commands')
        #

        #
        self.std_nameKw  = AFXStringKeyword(self.cmd, 'std_name' , TRUE)
        self.rKw         = AFXFloatKeyword( self.cmd, 'r'        , TRUE)
        self.hKw         = AFXFloatKeyword( self.cmd, 'h'        , TRUE)
        self.alphadegKw  = AFXFloatKeyword( self.cmd, 'alphadeg' , TRUE)
        self.laKw        = AFXIntKeyword(   self.cmd, 'la'       , TRUE)
        self.betadegKw   = AFXFloatKeyword( self.cmd, 'betadeg'  , TRUE)
        self.omegadegKw  = AFXFloatKeyword( self.cmd, 'omegadeg' , TRUE)
        self.laminateKw  = AFXTableKeyword( self.cmd, 'laminate' , TRUE, 0, -1, AFXTABLE_TYPE_STRING)
        self.stackKw     = AFXTableKeyword( self.dummy, 'stack'    , FALSE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.betadegsKw  = AFXTableKeyword( self.cmd, 'betadegs' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.omegadegsKw = AFXTableKeyword( self.cmd, 'omegadegs', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.plytKw      = AFXFloatKeyword( self.dummy, 'plyt'     , FALSE)
        self.elem_typeKw = AFXStringKeyword(self.cmd, 'elem_type', TRUE)
        self.numel_rKw   = AFXIntKeyword(   self.cmd, 'numel_r'  , TRUE)
        self.axial_displKw = AFXFloatKeyword(self.cmd, 'axial_displ', TRUE)
        self.axial_includeKw = AFXBoolKeyword(self.cmd, 'axial_include', TRUE_FALSE,TRUE)
        self.separate_load_stepsKw = AFXBoolKeyword(self.cmd, 'separate_load_steps', TRUE_FALSE,TRUE)
        self.artificial_damping1Kw = AFXBoolKeyword(self.cmd, 'artificial_damping1', TRUE_FALSE,TRUE)
        self.artificial_damping2Kw = AFXBoolKeyword(self.cmd, 'artificial_damping2', TRUE_FALSE,TRUE)
        self.damping_factor1Kw = AFXFloatKeyword( self.cmd, 'damping_factor1',TRUE)
        self.damping_factor2Kw = AFXFloatKeyword( self.cmd, 'damping_factor2',TRUE)
        self.minInc1Kw    = AFXFloatKeyword( self.cmd, 'minInc1',TRUE)
        self.minInc2Kw    = AFXFloatKeyword( self.cmd, 'minInc2',TRUE)
        self.initialInc1Kw = AFXFloatKeyword(self.cmd, 'initialInc1',TRUE)
        self.initialInc2Kw = AFXFloatKeyword(self.cmd, 'initialInc2',TRUE)
        self.maxInc1Kw    = AFXFloatKeyword( self.cmd, 'maxInc1',TRUE)
        self.maxInc2Kw    = AFXFloatKeyword( self.cmd, 'maxInc2',TRUE)
        self.maxNumInc1Kw = AFXFloatKeyword( self.cmd, 'maxNumInc1',TRUE)
        self.maxNumInc2Kw = AFXFloatKeyword( self.cmd, 'maxNumInc2',TRUE)
        self.use_job_stopperKw = AFXBoolKeyword(  self.cmd, 'use_job_stopper',TRUE_FALSE,TRUE)
        self.botU1Kw     = AFXBoolKeyword(  self.cmd, 'botU1',TRUE_FALSE,TRUE)
        self.botU2Kw     = AFXBoolKeyword(  self.cmd, 'botU2',TRUE_FALSE,TRUE)
        self.botU3Kw     = AFXBoolKeyword(  self.cmd, 'botU3',TRUE_FALSE,TRUE)
        self.botUR1Kw    = AFXBoolKeyword(  self.cmd, 'botUR1',TRUE_FALSE,TRUE)
        self.botUR2Kw    = AFXBoolKeyword(  self.cmd, 'botUR2',TRUE_FALSE,TRUE)
        self.botUR3Kw    = AFXBoolKeyword(  self.cmd, 'botUR3',TRUE_FALSE,TRUE)
        self.topU1Kw     = AFXBoolKeyword(  self.cmd, 'topU1',TRUE_FALSE,TRUE)
        self.topU2Kw     = AFXBoolKeyword(  self.cmd, 'topU2',TRUE_FALSE,TRUE)
        self.topU3Kw     = AFXBoolKeyword(  self.cmd, 'topU3',TRUE_FALSE,TRUE)
        self.topUR1Kw    = AFXBoolKeyword(  self.cmd, 'topUR1',TRUE_FALSE,TRUE)
        self.topUR2Kw    = AFXBoolKeyword(  self.cmd, 'topUR2',TRUE_FALSE,TRUE)
        self.topUR3Kw    = AFXBoolKeyword(  self.cmd, 'topUR3',TRUE_FALSE,TRUE)
        self.laminapropKw  = AFXTupleKeyword(self.dummy, 'laminaprop',FALSE)
        self.allowablesKw  = AFXTupleKeyword(self.cmd, 'allowables',TRUE)
        self.time_pointsKw = AFXIntKeyword( self.cmd, 'time_points',TRUE)
        self.request_stress_outputKw = AFXBoolKeyword(self.cmd,'request_stress_output', TRUE_FALSE,TRUE)
        self.pl_numKw    = AFXIntKeyword(   self.cmd, 'pl_num'   , TRUE)
        self.d_numKw    = AFXIntKeyword(   self.cmd, 'd_num'   , TRUE)
        self.ax_numKw    = AFXIntKeyword(   self.cmd, 'ax_num'   , TRUE)
        self.lbmi_numKw    = AFXIntKeyword(   self.cmd, 'lbmi_num'   , TRUE)
        self.cut_numKw   = AFXIntKeyword(   self.cmd, 'cut_num'  , TRUE)
        self.pl_tableKw  = AFXTableKeyword( self.cmd, 'pl_table' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.d_tableKw   = AFXTableKeyword( self.cmd, 'd_table' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.ax_tableKw  = AFXTableKeyword( self.cmd, 'ax_table' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.lbmi_tableKw  = AFXTableKeyword( self.cmd, 'lbmi_table' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.cut_tableKw = AFXTableKeyword( self.cmd, 'cut_table', TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        #
        #
        self.laminapropKeyKw = AFXStringKeyword(self.dummy, 'laminapropKey', FALSE)
        self.allowablesKeyKw = AFXStringKeyword(self.dummy, 'allowablesKey', FALSE)
        self.new_laminaprop_nameKw = AFXStringKeyword(self.dummy, 'new_laminaprop_name', FALSE)
        self.new_allowables_nameKw = AFXStringKeyword(self.dummy, 'new_allowables_name', FALSE)
        self.ccKeyKw = AFXStringKeyword(self.dummy, 'ccKey',FALSE)
        self.new_cc_nameKw   = AFXStringKeyword(self.dummy, 'new_cc_name'  , FALSE)
        self.last_loadedKw = AFXStringKeyword(self.dummy, 'last_loaded', FALSE)
        self.std_to_postKw = AFXStringKeyword(self.dummy, 'std_to_post', FALSE)
        self.model_to_postKw = AFXStringKeyword(self.dummy, 'model_to_post', FALSE)
        self.post_put_in_ExcelKw = AFXBoolKeyword(self.dummy, 'post_put_in_Excel', TRUE_FALSE, FALSE)
        self.post_open_ExcelKw = AFXBoolKeyword(self.dummy, 'post_open_Excel', TRUE_FALSE, FALSE)
        self.mult_cpusKw    = AFXBoolKeyword(self.dummy, 'mult_cpus', TRUE_FALSE, FALSE)
        #
        self.imp_ms_std_nameKw = AFXStringKeyword(self.apply_imp_ms, 'std_name' , TRUE)
        self.imp_ms_stdKw   = AFXBoolKeyword(self.dummy, 'imp_ms_std', TRUE_FALSE, TRUE)
        self.imp_msKw   = AFXStringKeyword(self.apply_imp_ms, 'imp_ms', TRUE)
        self.imp_ms_stretch_HKw = AFXBoolKeyword(self.apply_imp_ms, 'imp_ms_stretch_H', TRUE_FALSE, TRUE)
        self.imp_ms_scalingsKw  = AFXTableKeyword( self.apply_imp_ms, 'imp_ms_scalings' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.imp_r_TOLKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_r_TOL', TRUE)
        self.imp_ms_ncpKw = AFXIntKeyword(self.apply_imp_ms, 'imp_ms_ncp', TRUE)
        self.imp_ms_power_parameterKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_ms_power_parameter', TRUE)
        self.imp_ms_num_sec_zKw = AFXFloatKeyword(self.apply_imp_ms, 'imp_ms_num_sec_z', TRUE)
        self.imp_ms_theta_z_formatKw  = AFXBoolKeyword(self.apply_imp_ms, 'imp_ms_theta_z_format', TRUE_FALSE, TRUE)
        #
        self.imp_t_std_nameKw = AFXStringKeyword(self.apply_imp_t, 'std_name' , TRUE)
        self.imp_t_stdKw   = AFXBoolKeyword(self.dummy, 'imp_t_std', TRUE_FALSE, TRUE)
        self.imp_thickKw   = AFXStringKeyword(self.apply_imp_t, 'imp_thick', TRUE)
        self.imp_num_setsKw = AFXIntKeyword(self.apply_imp_t, 'imp_num_sets', TRUE)
        self.imp_t_stretch_HKw = AFXBoolKeyword(self.apply_imp_t, 'imp_t_stretch_H', TRUE_FALSE, TRUE)
        self.imp_t_scalingsKw  = AFXTableKeyword( self.apply_imp_t, 'imp_t_scalings' , TRUE, 0, -1, AFXTABLE_TYPE_FLOAT)
        self.imp_t_ncpKw = AFXIntKeyword(self.apply_imp_t, 'imp_t_ncp', TRUE)
        self.imp_t_power_parameterKw = AFXFloatKeyword(self.apply_imp_t, 'imp_t_power_parameter', TRUE)
        self.imp_t_num_sec_zKw = AFXFloatKeyword(self.apply_imp_t, 'imp_t_num_sec_z', TRUE)
        self.imp_t_theta_z_formatKw  = AFXBoolKeyword(self.apply_imp_t, 'imp_t_theta_z_format', TRUE_FALSE, TRUE)
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
        if params_from_gui.get('laminate',None)== None:
            laminapropKeys = [self.laminapropKeyKw.getValue()]
            plyts = [self.plytKw.getValue()]
            stack = [float(i)for i in self.stackKw.getValues().split(',')]
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

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
        sendCommand('if not os.path.isdir(r"%s"):\n' %path +\
                     '    os.makedirs(r"%s")' % path)
        sendCommand('os.chdir(r"%s")' % path)
        self.just_created_study = False
        reload(testDB)
        return testDB.TestDB(self)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def issueCommands(self):
        self.laKw.setValue(self.db.lasw.getCurrent())
        a = self.cmd.getCommandString()
        a = a.replace(', ,',',False,')
        a = a.replace(', ,',',False,')
        a = a.replace(',)',',False)')
        a = a.replace('(,False','(False,False')
        b =   'import gui_commands\n'    \
            + 'reload(gui_commands)\n' \
            + a
        #if not os.path.isdir(r'C:\Temp'):
        #    os.makedirs(r'C:\Temp')
        #cmdpath = r'c:\Temp\cmd.py'
        #cmdfile = open(cmdpath,'w')
        #cmdfile.write(b + '\n')
        #cmdfile.close()
        sendCommand(b, writeToReplay=False, writeToJournal=True)
        self.just_created_study = True
        self.loaded_study = True
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

