import json
import os
import ast

import numpy as np

from uti import webBrowser
from abaqusGui import *

import gui_commands
import gui_plot
from desicos import __version__ as version
import desicos.conecylDB as conecylDB
from desicos.conecylDB import fetch
from desicos.abaqus.utils import remove_special_characters as rsc
from desicos.abaqus.constants import *

NUM_PLIES = 40


def cc_form2dict(db, form):
    tmp = form.laminateKw.getValueAsString()
    laminate = np.array(ast.literal_eval(tmp))
    cc = {}
    if ''.join(laminate.flatten()):
        cc['laminapropKeys'] = [i for i in laminate[:, 0] if i<>'']
        cc['plyts'] = [float(i) for i in laminate[:, 1] if i<>'']
        cc['stack'] = [float(i) for i in laminate[:, 2] if i<>'']
    others = ['rbot', 'H', 'alphadeg', 'elem_type', 'betadeg', 'omegadeg',
              'numel_r', 'axial_displ']
    for k in others:
        cc[k] = getattr(form, k+'Kw').getValue()
    return cc


def cc_dict2form(ccname, cc, db, form):
    # clearing laminateKw
    maxRow = db.laminateTable.getNumRows()
    db.laminateTable.clearContents(1, 1, maxRow-1, 1, False)
    #
    form.rbotKw.setValue(cc['rbot'])
    form.HKw.setValue(cc['H'])
    form.alphadegKw.setValue(cc.get('alphadeg', 0.))
    laminapropKeys = cc.get('laminapropKeys', [cc.get('laminapropKey')])
    if isinstance(laminapropKeys, str):
        laminapropKeys = [laminapropKeys]
    plyts = cc.get('plyts', [cc.get('plyt')])
    stack = cc.get('stack',[])
    tmp = np.empty((NUM_PLIES, 3), dtype='|S50')
    #TODO necessary strange solution to force update
    tmp.fill('TODOTODOTODO')
    tmp[:len(laminapropKeys), 0] = laminapropKeys
    tmp[:len(plyts), 1] = plyts
    tmp[:len(stack), 2] = stack
    laminate = ','.join([str(tuple(i)) for i in tmp])
    form.laminateKw.setValues(laminate)
    laminate = laminate.replace('TODOTODOTODO', '')
    form.laminateKw.setValues(laminate)
    # clearing pl_tableKw
    maxRow = db.imp_tables['pl'].getNumRows()
    valuesStr = ''
    for i in range(1, maxRow):
        valuesStr += ', '
    valuesStr += ''
    db.imp_tables['pl'].clearContents(1, 1, maxRow-1, 1, False)
    form.pl_tableKw.setValues(valuesStr)
    # setting new pl_tableKw
    if 'ploads' in cc.keys():
        valuesStr = '0.0,0.5,,'
        for i in range(len(cc['ploads'])):
            pload = cc['ploads'][i]
            valuesStr += '%2.1f,' % pload
        valuesStr += 'end'
        valuesStr = valuesStr.replace(',end', '')
        form.pl_tableKw.setValues(valuesStr)
        form.pl_numKw.setValue(1)
    else:
        valuesStr = '0.0,0.5,,0.0'
        form.pl_tableKw.setValues(valuesStr)
    form.ccKeyKw.setValue('conecyl loaded!')
    form.last_loadedKw.setValue(ccname)
    input_dict = cc
    form.setDefault(update_values=True, input_dict = cc)
    db.update_database(update_all=True)


def message(string):
    sendCommand("print(r'%s')" % string)


###########################################################################
# Class definition
###########################################################################


class TestDB(AFXDataDialog):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, form):
        #
        # Init
        #
        self.form = form
        self.form.db = self
        #
        max_models = 40
        self.logcount = 10000
        self.lamMatrix = {'A':None, 'B':None, 'D':None}
        #
        #
        #
        title = 'DESICOS GUI Version {0}'.format(version)
        AFXDataDialog.__init__(self, form, title, 0)
        self.appendActionButton('Create Study', self, self.ID_CLICKED_APPLY)
        self.appendActionButton('Apply defaults', self, self.ID_CLICKED_DEFAULTS)
        self.appendActionButton('Close', self, self.ID_CLICKED_CANCEL)
        #
        # Main Vertical Frame
        #
        mainVF = FXVerticalFrame(self, LAYOUT_FILL_Y, LAYOUT_FILL_X)
        #
        # Always visible widgets
        #
        mainHF = FXHorizontalFrame(mainVF, LAYOUT_CENTER_Y)
        AFXTextField(mainHF, 30, 'Study name (without spaces):', form.std_nameKw,
                     opts=LAYOUT_LEFT)
        mainHF = FXHorizontalFrame(mainVF, LAYOUT_CENTER_Y)
        tmp = AFXTextField(mainHF, 30, 'Last loaded conecyl:',
                                    form.last_loadedKw)
        tmp.setEditable(False)
        self.ccs_CB = AFXComboBox(mainHF, 0, 10, 'Select from database:', form.ccKeyKw)
        self.new_cc_name = AFXTextField(mainHF, 20, 'New:', form.new_cc_nameKw)
        self.save_cc_button = FXButton(mainHF, 'Save')
        self.del_cc_button = FXButton(mainHF, 'Delete')
        #
        #
        # Tabs
        #
        mainTabBook = FXTabBook(mainVF, None, 0, LAYOUT_FILL_X)
        #
        # Tabs / Load / Save Study
        #
        FXTabItem(mainTabBook, 'Load / Save Study')
        loadFrame = FXHorizontalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        loadVF = FXVerticalFrame(loadFrame, LAYOUT_FILL_X|LAYOUT_FILL_Y)
        FXLabel(loadVF, '')
        FXLabel(loadVF, '')
        self.std_to_load = AFXComboBox(loadVF, 0, 10, 'Select study to load:',
                                       form.std_to_postKw)
        FXLabel(loadVF, '')
        FXLabel(loadVF, '')
        loadHF1 = FXHorizontalFrame(loadVF)
        self.load_std = FXButton(loadHF1, 'Load Study')
        self.save_std = FXButton(loadHF1, 'Save Study')
        FXLabel(loadVF, '')
        FXLabel(loadVF, '')
        FXLabel(loadVF, 'NOTE: If you updated you Abaqus version, please open the .cae file in Abaqus before loading with the Plug-In')
        FXLabel(loadVF, '')
        FXLabel(loadVF, '')
        FXHorizontalSeparator(loadVF)
        #
        # Tabs / Geometry
        #
        FXTabItem(mainTabBook, 'Geometry')
        geomFrame = FXHorizontalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'geometry.png')
        icon = afxCreatePNGIcon(pngpath)
        FXLabel(geomFrame, '', icon)
        geomVF = FXVerticalFrame(geomFrame)
        geomVA = AFXVerticalAligner(geomVF)
        FXLabel(geomVA, 'Define geometry:')
        AFXTextField(geomVA, 8, 'R:', form.rbotKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(geomVA, 8, 'H:', form.HKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(geomVA, 8, 'alpha in degrees:',
                     form.alphadegKw, opts=AFXTEXTFIELD_FLOAT)
        FXLabel(geomVF, 'OBS:')
        FXLabel(geomVF, '       - For cylinders keep alpha = 0')
        FXLabel(geomVF, '       - H includes the resin rings')
        #
        # Tabs / Model
        #
        FXTabItem(mainTabBook, 'Model')
        modelFrame = FXHorizontalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        modelBook = FXTabBook(modelFrame, None, 0,
                              TABBOOK_LEFTTABS|LAYOUT_FILL_X)
        #
        # Tabs / Model / Material
        #
        FXTabItem(modelBook, 'Material', None, TAB_LEFT)
        matFrame = FXVerticalFrame(modelBook, LAYOUT_FILL_X|LAYOUT_FILL_Y)
        FXLabel(matFrame, 'Lamina / isotropic elastic properties')
        matHF = FXHorizontalFrame(matFrame)
        self.laminaprops_CB = AFXComboBox(matHF, 0, 5, 'Select from database:', form.laminapropKeyKw)
        self.new_laminaprop_name = AFXTextField(matHF, 30, 'New:', form.new_laminaprop_nameKw)
        self.new_laminaprop_name.disable()
        self.save_laminaprop_button = FXButton(matHF, 'Save')
        self.del_laminaprop_button = FXButton(matHF, 'Delete')
        matHF1 = FXHorizontalFrame(matFrame)
        AFXTextField(matHF1, 8, 'E11' , form.laminapropKw, 1, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF1, 8, 'E22' , form.laminapropKw, 2, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF1, 8, 'nu12', form.laminapropKw, 3, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF1, 8, 'G12' , form.laminapropKw, 4, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF1, 8, 'G13' , form.laminapropKw, 5, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF1, 8, 'G23' , form.laminapropKw, 6, opts=AFXTEXTFIELD_FLOAT)
        FXLabel(matFrame, '')
        FXLabel(matFrame, 'For isotropic, define E22=E11 and let G12, G13 and G23 as blank fields')
        FXLabel(matFrame, '')
        FXHorizontalSeparator(matFrame)
        FXLabel(matFrame, 'Material allowables (composite only...)')
        matHF = FXHorizontalFrame(matFrame)
        self.allowables_CB = AFXComboBox(matHF, 0, 5, 'Select from database:', form.allowablesKeyKw)
        self.new_allowables_name = AFXTextField(matHF, 30, 'New:', form.new_allowables_nameKw)
        self.new_allowables_name.disable()
        self.save_allowables_button = FXButton(matHF, 'Save')
        self.del_allowables_button = FXButton(matHF, 'Delete')
        matHF2 = FXHorizontalFrame(matFrame)
        AFXTextField(matHF2, 8, 'S11t', form.allowablesKw, 1, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF2, 8, 'S11c', form.allowablesKw, 2, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF2, 8, 'S22t', form.allowablesKw, 3, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF2, 8, 'S22c', form.allowablesKw, 4, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF2, 8, 'S12' , form.allowablesKw, 5, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(matHF2, 8, 'S13' , form.allowablesKw, 6, opts=AFXTEXTFIELD_FLOAT)
        #
        # Tabs / Model / Laminate
        #
        FXTabItem(modelBook, 'Laminate', None, TAB_LEFT)
        lamFrame = FXHorizontalFrame(modelBook, FRAME_RAISED|FRAME_SUNKEN)
        lamVF = FXVerticalFrame(lamFrame)
        lamRadioGB = FXGroupBox(lamVF, 'Define laminate using', FRAME_GROOVE)
        FXLabel(lamVF, 'ply 01 material and thickness will be\n'+\
                      'used for other plies if they are not \n'+\
                      'especified individually')
        sw = FXSwitcher(lamFrame)
        self.lamRB = {}
        self.lamRB['stack'] = FXRadioButton(lamRadioGB, 'stacking sequence', sw,
                                            FXSwitcher.ID_OPEN_FIRST)
        #TODO
        #self.lamRB['ABD'  ] = FXRadioButton(lamRadioGB, 'A, B, D matrices', sw,
        #                                    FXSwitcher.ID_OPEN_FIRST+1)
        # Tabs / Model / Laminate / stack
        laminateTable = AFXTable(sw, 21, 4, NUM_PLIES+1, 4,
            form.laminateKw, 0,
            opts=AFXTABLE_EDITABLE|AFXTABLE_TYPE_FLOAT|AFXTABLE_STYLE_DEFAULT)
        laminateTable.setLeadingRows(1)
        laminateTable.setLeadingColumns(1)
        laminateTable.setLeadingColumnLabels('\t'.join(['ply %02d'%i for i in xrange(1, 41)]))
        laminateTable.setColumnWidth(1, 300)
        laminateTable.setColumnWidth(2, 75)
        laminateTable.setColumnWidth(3, 75)
        laminateTable.setLeadingRowLabels('material\tthickness\tangle')
        laminateTable.setColumnType(1, AFXTable.LIST)
        self.laminateTable = laminateTable
        # Tabs / Model / Laminate / ABD
        #TODO activate direct input of ABD matrix
        if False:
            lamMatrix = FXMatrix(sw, 2, opts=MATRIX_BY_COLUMNS)
            for lam in self.lamMatrix.keys():
                table = AFXTable(lamMatrix, 5, 4, 5, 4,
                    opts=AFXTABLE_EDITABLE|AFXTABLE_STYLE_DEFAULT)
                table.setLeadingRows(2)
                table.setItemSpan(0, 0, 2, 1)
                table.setItemSpan(0, 1, 1, 3)
                table.setLeadingColumns(1)
                table.setLeadingRowLabels(lam + ' matrix', 0)
                table.setLeadingRowLabels('1\t2\t3', 1)
                table.showHorizontalGrid(True)
                table.showVerticalGrid(True)
                self.lamMatrix[ lam ] = table
        #
        # Tabs / Model / Mesh
        #
        FXTabItem(modelBook, 'Mesh', None, TAB_LEFT)
        meshFrame = FXHorizontalFrame(modelBook, FRAME_RAISED|FRAME_SUNKEN)
        meshCB = AFXComboBox(meshFrame, 0, 4, 'Element Type:', form.elem_typeKw)
        meshCB.appendItem('S4R' , 1)
        meshCB.appendItem('S4R5', 1)
        meshCB.appendItem('S8R' , 1)
        meshCB.appendItem('S8R5', 1)
        self.meshCB = meshCB
        meshVA = AFXVerticalAligner(meshFrame)
        AFXTextField(meshVA, 5, 'Number of elements along the circumference:',
                     form.numel_rKw, opts=AFXTEXTFIELD_INTEGER)
        msg = 'Define in Geometric Imperfections/Cutouts'
        numel_cutout = AFXTextField(meshVA, len(msg),
                         'Number of elements around cutouts:')
        numel_cutout.setText(msg)
        numel_cutout.setEditable(False)
        #
        # Tabs / Model / Boundary Conditions
        #
        FXTabItem(modelBook, 'Boundary Conditions', None, TAB_LEFT)
        bcFrame = FXHorizontalFrame(modelBook, FRAME_RAISED|FRAME_SUNKEN)
        bcHA = FXHorizontalFrame(bcFrame)
        bcVAfig = FXVerticalFrame(bcHA)
        FXVerticalSeparator(bcHA)
        bcVAbot = FXVerticalFrame(bcHA)
        FXVerticalSeparator(bcHA)
        bcVAtop = FXVerticalFrame(bcHA)
        bcVAfig_VA = AFXVerticalAligner(bcVAfig)
        AFXTextField(bcVAfig_VA, 8, 'Resin Elastic Modulus:' , form.resin_EKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAfig_VA, 8, 'Resin Poisson`s ratio:', form.resin_nuKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAfig_VA, 8, 'Elements along the resin edge:', form.resin_numelKw, opts=AFXTEXTFIELD_INTEGER)
        FXHorizontalSeparator(bcVAfig)
        # bottom edge
        FXLabel(bcVAbot, 'Bottom Edge')
        FXLabel(bcVAbot, '')
        FXLabel(bcVAbot, '')
        FXCheckButton(bcVAbot, 'Fix Radial Displ.' , form.bc_fix_bottom_uRKw)
        FXCheckButton(bcVAbot, 'Fix Circumferential Displ.' , form.bc_fix_bottom_vKw)
        FXCheckButton(bcVAbot, 'Clamp Shell Edge' , form.bc_bottom_clampedKw)
        FXLabel(bcVAbot, '')
        FXLabel(bcVAbot, '')
        FXLabel(bcVAbot, '')
        FXCheckButton(bcVAbot, 'Inner Resin Ring Bottom', form.resin_add_BIRKw)
        FXCheckButton(bcVAbot, 'Outer Resin Ring Bottom', form.resin_add_BORKw)
        FXLabel(bcVAbot, '')
        FXLabel(bcVAbot, '')
        bcVAbot_VA = AFXVerticalAligner(bcVAbot)
        AFXTextField(bcVAbot_VA, 5, 'resin_bot_h:' , form.resin_bot_hKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAbot_VA, 5, 'resin_bir_w1:', form.resin_bir_w1Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAbot_VA, 5, 'resin_bir_w2:', form.resin_bir_w2Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAbot_VA, 5, 'resin_bor_w1:', form.resin_bor_w1Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAbot_VA, 5, 'resin_bor_w2:', form.resin_bor_w2Kw, opts=AFXTEXTFIELD_FLOAT)
        # top edge
        FXLabel(bcVAtop, 'Top Edge')
        FXLabel(bcVAtop, '')
        FXLabel(bcVAtop, '')
        FXCheckButton(bcVAtop, 'Fix Radial Displ.' , form.bc_fix_top_uRKw)
        FXCheckButton(bcVAtop, 'Fix Circumferential Displ.' , form.bc_fix_top_vKw)
        FXCheckButton(bcVAtop, 'Clamp Shell Edge' , form.bc_top_clampedKw)
        FXLabel(bcVAtop, '')
        FXLabel(bcVAtop, '')
        FXLabel(bcVAtop, '')
        FXCheckButton(bcVAtop, 'Inner Resin Ring Top' , form.resin_add_TIRKw)
        FXCheckButton(bcVAtop, 'Outer Resin Ring Top' , form.resin_add_TORKw)
        FXLabel(bcVAtop, '')
        FXLabel(bcVAtop, '')
        bcVAtop_VA = AFXVerticalAligner(bcVAtop)
        AFXTextField(bcVAtop_VA, 5, 'resin_top_h:' , form.resin_top_hKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAtop_VA, 5, 'resin_tir_w1:', form.resin_tir_w1Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAtop_VA, 5, 'resin_tir_w2:', form.resin_tir_w2Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAtop_VA, 5, 'resin_tor_w1:', form.resin_tor_w1Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(bcVAtop_VA, 5, 'resin_tor_w2:', form.resin_tor_w2Kw, opts=AFXTEXTFIELD_FLOAT)
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'resin_rings.png')
        icon = afxCreatePNGIcon(pngpath)
        FXLabel(bcVAfig, '')
        FXLabel(bcVAfig, '')
        FXLabel(bcVAfig, '', icon)
        #
        # Tabs / Model / Load Steps
        #
        FXTabItem(modelBook, 'Load Steps', None, TAB_LEFT)
        nlHF = FXHorizontalFrame(modelBook, opts=FRAME_RAISED|FRAME_SUNKEN)
        # general parameters
        nlVFc= FXVerticalFrame(nlHF)
        FXLabel(nlVFc, '')
        FXLabel(nlVFc, 'Load Definitions')
        FXLabel(nlVFc, '')
        FXCheckButton(nlVFc, 'Displacement controlled', form.displ_controlledKw)
        FXCheckButton(nlVFc, 'Use two load steps:', form.separate_load_stepsKw)
        self.axial_displ = AFXTextField(nlVFc, 8, 'Axial displacement:', form.axial_displKw, AFXTEXTFIELD_FLOAT)
        self.axial_load = AFXTextField(nlVFc, 8, 'Axial compressive\nload:', form.axial_loadKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(nlVFc, 8, 'Pressure load:\n  (positive outwards)', form.pressure_loadKw, opts=AFXTEXTFIELD_FLOAT)
        FXHorizontalSeparator(nlVFc)
        FXLabel(nlVFc, '')
        FXLabel(nlVFc, 'Step Number for Each Load')
        FXLabel(nlVFc, '')
        self.axial_step = AFXTextField(nlVFc, 8, 'Axial loads:', form.axial_stepKw, opts=AFXTEXTFIELD_INTEGER)
        AFXTextField(nlVFc, 8, 'Perturbation loads:', form.pload_stepKw, opts=AFXTEXTFIELD_INTEGER)
        AFXTextField(nlVFc, 8, 'Pressure load:', form.pressure_stepKw, opts=AFXTEXTFIELD_INTEGER)
        # perturbation load step
        FXVerticalSeparator(nlHF)
        nlVF1 = FXVerticalFrame(nlHF)
        FXLabel(nlVF1, '')
        FXLabel(nlVF1, 'Step with constant loads (step 1)')
        FXLabel(nlVF1, '')
        self.art_damp1 = FXCheckButton(nlVF1, 'Artificial Damping', form.artificial_damping1Kw)
        FXLabel(nlVF1, '')
        self.damp_factor1 = AFXTextField(nlVF1, 8, 'Damping Factor:', form.damping_factor1Kw, opts=AFXTEXTFIELD_FLOAT)
        nlVA = AFXVerticalAligner(nlVF1)
        self.minInc1 = AFXTextField(nlVA, 8, 'Minimum increment size:', form.minInc1Kw, opts=AFXTEXTFIELD_FLOAT)
        self.initialInc1 = AFXTextField(nlVA, 8, 'Initial increment size:', form.initialInc1Kw, opts=AFXTEXTFIELD_FLOAT)
        self.maxInc1 = AFXTextField(nlVA, 8, 'Maximum increment size:', form.maxInc1Kw, opts=AFXTEXTFIELD_FLOAT)
        self.maxNumInc1 = AFXTextField(nlVA, 8, 'Maximum number of increments:', form.maxNumInc1Kw, opts=AFXTEXTFIELD_FLOAT)
        # axial compression step
        FXVerticalSeparator(nlHF)
        nlVF2 = FXVerticalFrame(nlHF)
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'axial2.png')
        icon = afxCreatePNGIcon(pngpath)
        FXLabel(nlVF2, '')
        FXLabel(nlVF2, 'Step with incremented loads (step 2)', icon)
        FXLabel(nlVF2, '')
        FXCheckButton(nlVF2, 'Artificial Damping', form.artificial_damping2Kw)
        FXLabel(nlVF2, '')
        AFXTextField(nlVF2, 8, 'Damping Factor:', form.damping_factor2Kw, opts=AFXTEXTFIELD_FLOAT)
        nlVA = AFXVerticalAligner(nlVF2)
        AFXTextField(nlVA, 8, 'Minimum increment size:', form.minInc2Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(nlVA, 8, 'Initial increment size:', form.initialInc2Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(nlVA, 8, 'Maximum increment size:', form.maxInc2Kw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(nlVA, 8, 'Maximum number of increments:', form.maxNumInc2Kw, opts=AFXTEXTFIELD_FLOAT)
        #
        # Tabs / Model / Output Requests
        #
        FXTabItem(modelBook, 'Output Requests', None, TAB_LEFT)
        outputFrame = FXVerticalFrame(modelBook, FRAME_RAISED|FRAME_SUNKEN)
        FXLabel(outputFrame, 'Field Outputs')
        AFXTextField(outputFrame, 8, 'Print at every time interval',
                     form.timeIntervalKw, opts=AFXTEXTFIELD_FLOAT)
        FXCheckButton(outputFrame, 'Request stress outputs',
                     form.stress_outputKw)
        #FXHorizontalSeparator(outputFrame)
        #FXLabel(outputFrame, 'History Outputs')
        #FXCheckButton(outputFrame, 'Load shortening curve').setCheck(True)
        #FXCheckButton(outputFrame,
        #                 'Displacements at the PL points').setCheck(True)
        #
        # Tabs / Geometric Imperfections
        #
        FXTabItem(mainTabBook, 'Geometric Imperfections')
        impFrame = FXHorizontalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        impBook = FXTabBook(impFrame, None, 0, TABBOOK_LEFTTABS|LAYOUT_FILL_X)
        #
        self.imp_current_num = {}
        self.imp_tables = {}
        self.imp_spinners = {}
        self.imp_num_params = {}
        self.imp_maxModels = {}
        rowLabels = {}
        rowLabels2 = {}
        colWidths = {}
        visibleCols = {}
        labelTabs = {}
        labelSpinners = {}
        pngs = {}
        imp_numKw = {}
        self.imp_tableKw = {}
        #
        # Tabs / Geometric Imperfections / Perturbation Loads / Dimples / Cutouts /
        # Mid-Surface Imperfections / Thickness Imperfections
        #
        labelTabs['pl'] = 'Perturbation Loads'
        labelTabs['d'] = 'Dimples'
        labelTabs['ax'] = 'Axisymmetric'
        labelTabs['lbmi'] = 'Linear Buckling Modes'
        labelTabs['cut'] = 'Cutouts'
        colWidths['pl'] = 45
        colWidths['d'] = 40
        colWidths['ax'] = 50
        colWidths['lbmi'] = 65
        colWidths['cut'] = 60
        visibleCols['pl'] = 5
        visibleCols['d'] = 6
        visibleCols['ax'] = 5
        visibleCols['lbmi'] = 4
        visibleCols['cut'] = 5
        labelSpinners['pl'] = 'Number of perturbation loads:'
        labelSpinners['d'] = 'Number of single buckles'
        labelSpinners['ax'] = 'Number of axisymmetrics'
        labelSpinners['lbmi'] = 'Number of buckling modes to combine:'
        labelSpinners['cut'] = 'Number of cutouts'
        self.imp_current_num['pl'] = 32
        self.imp_current_num['d'] = 16
        self.imp_current_num['ax'] = 16
        self.imp_current_num['lbmi'] = 16
        self.imp_current_num['cut'] = 16
        self.imp_maxModels['pl'] = max_models
        self.imp_maxModels['d'] = max_models
        self.imp_maxModels['ax'] = max_models
        self.imp_maxModels['lbmi'] = max_models
        self.imp_maxModels['cut'] = max_models
        self.imp_num_params['pl'] = 2
        self.imp_num_params['d'] = 4
        self.imp_num_params['ax'] = 2
        self.imp_num_params['lbmi'] = 1
        self.imp_num_params['cut'] = 3
        rowLabels['pl'] = 'Position theta:\tPosition z/H:\t'
        rowLabels['d'] = 'Position theta:\tPosition z/H:\t' + \
                           'Parameter a:\tParameter b:\t'
        rowLabels['ax'] = 'Position z/H:\tParameter b:\t'
        rowLabels['lbmi'] = 'Mode number\t'
        rowLabels['cut'] = 'Position theta:\tPosition z/H:' +\
                           '\tNr. elements around\t'
        rowLabels2['pl'] = '\tPL value for model'
        rowLabels2['d'] = '\tWb for model'
        rowLabels2['ax'] = '\tWb for model'
        rowLabels2['lbmi'] = '\tSF for model'
        rowLabels2['cut'] = '\tcutout diameter for model'
        pngs['pl'] = 'pl2.png'
        pngs['d'] = 'd2.png'
        pngs['ax'] = 'axisymmetric.png'
        pngs['lbmi'] = 'lbmi2.png'
        pngs['cut'] = 'cutout2.png'
        self.imp_tableKw['pl'] = form.pl_tableKw
        self.imp_tableKw['d'] = form.d_tableKw
        self.imp_tableKw['ax'] = form.ax_tableKw
        self.imp_tableKw['lbmi'] = form.lbmi_tableKw
        self.imp_tableKw['cut'] = form.cut_tableKw
        imp_numKw['pl'] = form.pl_numKw
        imp_numKw['d'] = form.d_numKw
        imp_numKw['ax'] = form.ax_numKw
        imp_numKw['lbmi'] = form.lbmi_numKw
        imp_numKw['cut'] = form.cut_numKw
        #
        for k in ['pl', 'd', 'ax', 'lbmi', 'cut']:
            maxIMP = self.imp_current_num[k]
            num_param = self.imp_num_params[k]
            maxModels = self.imp_maxModels[k]
            FXTabItem(impBook, labelTabs[k], None, TAB_LEFT)
            impVF = FXVerticalFrame(impBook, LAYOUT_FILL_Y|FRAME_RAISED|FRAME_SUNKEN)
            impHF = FXHorizontalFrame(impVF)
            self.imp_spinners[k] = AFXSpinner(impHF, 2, labelSpinners[k], imp_numKw[k])
            self.imp_spinners[k].setRange(0, maxIMP)
            FXHorizontalSeparator(impVF)
            impHF = FXHorizontalFrame(impVF)
            self.imp_tables[k] = AFXTable(impHF, 20, visibleCols[k]+1,
                           maxModels+num_param+2, maxIMP+1,
                           self.imp_tableKw[k], 0,
                           opts=AFXTABLE_TYPE_FLOAT|AFXTABLE_STYLE_DEFAULT)
            for i in range(self.imp_current_num[k]):
                self.imp_tables[k].setColumnWidth(i+1, colWidths[k])
            self.imp_tables[k].setLeadingRows(1)
            self.imp_tables[k].setLeadingColumns(1)
            self.imp_tables[k].showHorizontalGrid(True)
            self.imp_tables[k].showVerticalGrid(True)
            self.imp_tables[k].setGridColor(1)
            colLabel = ''
            for i in range(1, maxIMP+1):
                colLabel += k.upper() + '%02d\t' % i
                self.imp_tables[k].setColumnEditable(i, True)
                self.imp_tables[k].setItemEditable(num_param + 1, i, False)
                self.imp_tables[k].setColumnType(i,
                                     self.imp_tables[k].FLOAT)
            self.imp_tables[k].setLeadingRowLabels(colLabel)
            rowLabel = rowLabels[k]
            for i in range(1, maxModels+1):
                rowLabel +=  rowLabels2[k] + ' %02d' % i
            self.imp_tables[k].setLeadingColumnLabels(rowLabel)
            pngpath = os.path.join(DAHOME, 'gui', 'icons', pngs[k])
            icon = afxCreatePNGIcon(pngpath)
            FXLabel(impHF, '', icon)
        #
        # Tabs / Geometric Imperfections / Mid-Surface Imperfections
        #
        FXTabItem(impBook, 'Mid-Surface Imperfections', None, TAB_LEFT)
        impVF = FXVerticalFrame(impBook, LAYOUT_FILL_Y|FRAME_RAISED|FRAME_SUNKEN)
        impHF = FXHorizontalFrame(impVF, opts=LAYOUT_CENTER_Y)
        impVF = FXVerticalFrame(impHF)
        FXCheckButton(impVF, 'Use the "theta z imperfection" format', form.imp_ms_theta_z_formatKw)
        FXLabel(impVF, '')
        FXLabel(impVF, '')
        self.imp_ms_db = AFXComboBox(impVF, 0, 15, 'Select from database:', form.imp_msKw)

        reload(conecylDB)
        if form.imp_ms_theta_z_formatKw.getValue():
            imps = conecylDB.imps_theta_z
        else:
            imps = conecylDB.imps
        keys = map(str, imps.keys())
        keys.sort()
        self.imp_ms_db.appendItem('')
        for k in keys:
            self.imp_ms_db.appendItem(k)

        FXCheckButton(impVF,    'Strech H_points to H_measured', form.imp_ms_stretch_HKw)
        impVA = AFXVerticalAligner(impVF)
        AFXTextField(impVA, 8,  'Radius tolerance to ignore dummy points (% of the radius):', form.imp_r_TOLKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(impVA, 8,  'Number of closest points to use in the inverse weighted interpolation:', form.imp_ms_ncpKw, opts=AFXTEXTFIELD_INTEGER)
        AFXTextField(impVA, 8,  'Power parameter to use in the inverse weighted interpolation:\n'+\
                                '(when increased, increases the influence of the closest points)', form.imp_ms_power_parameterKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(impVA, 8,  'Number of sections along Z axis to classify the measured data\n'+\
                                '(to speed up the search algorithm):', form.imp_ms_num_sec_zKw, opts=AFXTEXTFIELD_INTEGER)
        FXLabel(impHF, '    ')
        impVF2 = FXVerticalFrame(impHF)
        FXLabel(impVF2, 'scaling factor=0 will NOT\napply the imperfection', opts=LAYOUT_CENTER_X)
        self.imp_ms_sf = AFXTable(impVF2, 21, 2,(max_models+1), 2, form.imp_ms_scalingsKw, 0,
            opts=AFXTABLE_EDITABLE|AFXTABLE_TYPE_FLOAT|AFXTABLE_STYLE_DEFAULT)
        self.imp_ms_sf.setLeadingRows(1)
        self.imp_ms_sf.setLeadingColumns(1)
        self.imp_ms_sf.setLeadingRowLabels('scaling factor')
        colLabel = '\t'.join([('model %02d' % i) for i in xrange(1, max_models+1)])
        self.imp_ms_sf.setLeadingColumnLabels(colLabel)
        FXLabel(impVF, '')
        FXLabel(impVF, '')
        self.apply_imp_ms = FXButton(impVF, 'Apply Mid-Surface Imperfections')
        #
        # Tabs / Mid-Surface Imperfections / Thickness imperfections
        #
        FXTabItem(impBook, 'Thickness imperfections', None, TAB_LEFT)
        impVF = FXVerticalFrame(impBook, LAYOUT_FILL_Y|FRAME_RAISED|FRAME_SUNKEN)
        impHF = FXHorizontalFrame(impVF, opts=LAYOUT_CENTER_Y)
        impVF = FXVerticalFrame(impHF)
        FXCheckButton(impVF, 'Use the "theta z thickness" format', form.imp_t_theta_z_formatKw)
        FXLabel(impVF, '')
        FXLabel(impVF, '')
        self.imp_t_db = AFXComboBox(impVF, 0, 15, 'Select from database:', form.imp_thickKw)

        reload(conecylDB)
        if form.imp_t_theta_z_formatKw.getValue():
            imps = conecylDB.imps_theta_z
        else:
            imps = conecylDB.imps
        keys = map(str, imps.keys())
        keys.sort()
        self.imp_t_db.appendItem('')
        for k in keys:
            self.imp_t_db.appendItem(k)

        FXCheckButton(impVF,    'Strech H_points to H_measured', form.imp_t_stretch_HKw)
        impVA = AFXVerticalAligner(impVF)
        AFXTextField(impVA, 8,  'Define number of properties to use (zero to use from measured data):', form.imp_num_setsKw, opts=AFXTEXTFIELD_INTEGER)
        AFXTextField(impVA, 8,  'Number of closest points to use in the inverse weighted interpolation:', form.imp_t_ncpKw, opts=AFXTEXTFIELD_INTEGER)
        AFXTextField(impVA, 8,  'Power parameter to use in the inverse weighted interpolation:\n'+\
                                '(when increased, increases the influence of the closest points)', form.imp_t_power_parameterKw, opts=AFXTEXTFIELD_FLOAT)
        AFXTextField(impVA, 8,  'Number of sections along Z axis to classify the measured data\n'+\
                                '(to speed up the search algorithm):', form.imp_t_num_sec_zKw, opts=AFXTEXTFIELD_INTEGER)
        FXLabel(impHF, '    ')
        impVF2 = FXVerticalFrame(impHF)
        FXLabel(impVF2, 'scaling factor=0 will NOT\napply the imperfection', opts=LAYOUT_CENTER_X)
        self.imp_t_sf = AFXTable(impVF2, 21, 2,(max_models+1), 2,
            form.imp_t_scalingsKw, 0,
            opts=AFXTABLE_EDITABLE|AFXTABLE_TYPE_FLOAT|AFXTABLE_STYLE_DEFAULT)
        self.imp_t_sf.setLeadingRows(1)
        self.imp_t_sf.setLeadingColumns(1)
        self.imp_t_sf.setLeadingRowLabels('scaling factor')
        colLabel = '\t'.join([('model %02d' % i) for i in xrange(1, max_models+1)])
        self.imp_t_sf.setLeadingColumnLabels(colLabel)
        FXLabel(impVF, '')
        FXLabel(impVF, '')
        self.apply_imp_t = FXButton(impVF, 'Apply Thickness Imperfections')
        #
        # Tabs / Load Imperfection
        #
        FXTabItem(mainTabBook, 'Load Imperfection')
        liFrame = FXHorizontalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        liBook = FXTabBook(liFrame, None, 0, TABBOOK_LEFTTABS|LAYOUT_FILL_X)
        #
        # Tabs / Load Imperfection / Load Asymmetry
        #
        FXTabItem(liBook, 'Load Asymmetry', None, TAB_LEFT)
        liHF = FXHorizontalFrame(liBook,)# opts=LAYOUT_CENTER_X|LAYOUT_FILL_Y|FRAME_RAISED|FRAME_SUNKEN)
        liVF = FXVerticalFrame(liHF, opts=LAYOUT_CENTER_X|FRAME_RAISED|FRAME_SUNKEN)
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'la.png')
        icon = afxCreatePNGIcon(pngpath)
        self.la_fig = FXLabel(liHF, '', icon)
        liVF1 = FXVerticalFrame(liVF, opts=LAYOUT_CENTER_X|FRAME_RAISED|FRAME_SUNKEN)
        self.lasw = FXSwitcher(liVF)
        FXRadioButton(liVF1, 'Do not apply load asymmetry', self.lasw, FXSwitcher.ID_OPEN_FIRST)
        FXRadioButton(liVF1, 'Unique load asymmetry to all models', self.lasw, FXSwitcher.ID_OPEN_FIRST+1)
        FXRadioButton(liVF1, 'Different load asymmetry for each model', self.lasw, FXSwitcher.ID_OPEN_FIRST+2)
        FXLabel(self.lasw, 'No load asymmetry will be applied')
        liFA = AFXVerticalAligner(self.lasw)
        self.la_beta = AFXTextField(liFA, 8, 'beta (degrees):', form.betadegKw, opts=AFXTEXTFIELD_FLOAT)
        self.la_omega = AFXTextField(liFA, 8, 'omega (degrees):', form.omegadegKw, opts=AFXTEXTFIELD_FLOAT)
        self.lasw.setCurrent(self.form.laKw.getValue())
        #
        liFB = FXHorizontalFrame(self.lasw)
        self.betadegs = AFXTable(liFB, 21, 2,(max_models+1), 2,
            form.betadegsKw, 0,
            opts=AFXTABLE_EDITABLE|AFXTABLE_TYPE_FLOAT|AFXTABLE_STYLE_DEFAULT)
        self.betadegs.setLeadingRows(1)
        self.betadegs.setLeadingColumns(1)
        self.betadegs.setLeadingRowLabels('beta (degrees)')
        self.betadegs.setLeadingColumnLabels(colLabel)
        self.omegadegs = AFXTable(liFB, 21, 2,(max_models+1), 2,
            form.omegadegsKw, 0,
            opts=AFXTABLE_EDITABLE|AFXTABLE_TYPE_FLOAT|AFXTABLE_STYLE_DEFAULT)
        self.omegadegs.setLeadingRows(1)
        self.omegadegs.setLeadingColumns(1)
        self.omegadegs.setLeadingRowLabels('omega (degrees)')
        self.omegadegs.setLeadingColumnLabels(colLabel)
        #

        #
        # Tabs / Run models
        #
        FXTabItem(mainTabBook, 'Run models')
        execFrame = FXHorizontalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        execVF = FXVerticalFrame(execFrame, LAYOUT_FILL_X|LAYOUT_FILL_Y)
        execHF = FXHorizontalFrame(execVF, opts=LAYOUT_FILL_X)
        execVF2 = FXVerticalFrame(execHF, opts=LAYOUT_CENTER_Y)
        self.std_to_run = AFXComboBox(execVF2, 0, 10, 'Select study to run:',
                                       form.std_to_postKw)
        FXLabel(execVF2, '')
        AFXTextField(execVF2, 5,
            'Number of cpus (some licenses do not allow this feature)',
            form.ncpusKw, opts=AFXTEXTFIELD_INTEGER)
        FXLabel(execVF2, '')
        FXCheckButton(execVF2,
            'Use job stopper (default: after the second drop or after 30%\n'+
            'of reaction load drop it stops the analysis)',
            form.use_job_stopperKw)
        FXLabel(execVF2, '')
        self.exec_std = FXButton(execVF2, 'Run study!')
        self.exec_log = FXText(execHF, None, 0,
            TEXT_READONLY|TEXT_SHOWACTIVE|LAYOUT_FIX_WIDTH|LAYOUT_FIX_HEIGHT|
            LAYOUT_CENTER_X|LAYOUT_CENTER_Y, 0, 0, 500, 440)
        self.exec_log.setBarColumns(3)
        self.exec_log.setBarColor(FXRGB(190, 190, 190))
        self.exec_log.setText('RUN LOG FILE')
        #
        # Tabs / Post-processing tools
        #
        FXTabItem(mainTabBook, 'Post-processing tools')
        postFrame = FXVerticalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        self.std_to_post = AFXComboBox(postFrame, 0, 10, 'Select study:',
                           form.std_to_postKw, opts=LAYOUT_CENTER_X)
        postBook = FXTabBook(postFrame, None, 0, TABBOOK_LEFTTABS|LAYOUT_FILL_X)
        #
        # Tabs / Post-processing tools / Load shortening curves
        #
        FXTabItem(postBook, 'Load shortening curves', None, TAB_LEFT)
        postVF = FXVerticalFrame(postBook, FRAME_RAISED|FRAME_SUNKEN)
        postVF2 = FXVerticalFrame(postVF, opts=LAYOUT_CENTER_X|LAYOUT_CENTER_Y)
        self.post_ls_button = FXButton(postVF2, 'Plot load shortening curves')
        FXCheckButton(postVF2, 'Put plots in Excel', form.post_put_in_ExcelKw)
        FXCheckButton(postVF2, 'Open Excel', form.post_open_ExcelKw)
        #
        # Tabs / Post-processing tools / Knock-down curve
        #
        FXTabItem(postBook, 'Knock-down curve', None, TAB_LEFT)
        postVF = FXVerticalFrame(postBook, FRAME_RAISED|FRAME_SUNKEN)
        postVF2 = FXVerticalFrame(postVF, opts=LAYOUT_CENTER_X|LAYOUT_CENTER_Y)
        FXCheckButton(postVF2, 'Put plots in Excel', form.post_put_in_ExcelKw)
        FXCheckButton(postVF2, 'Open Excel', form.post_open_ExcelKw)
        postVF2 = FXVerticalFrame(postVF, opts=LAYOUT_CENTER_X|LAYOUT_CENTER_Y)
        self.post_kdf_button = FXButton(postVF2, 'Plot knock-down curves')
        #
        # Tabs / Post-processing tools / Stress analysis
        #
        FXTabItem(postBook, 'Stress analysis', None, TAB_LEFT)
        postVF = FXVerticalFrame(postBook, FRAME_RAISED|FRAME_SUNKEN)
        postVF2 = FXVerticalFrame(postVF, opts=LAYOUT_CENTER_X|LAYOUT_CENTER_Y)
        self.model_to_post = AFXComboBox(postVF2, 0, 10, 'Select model:',
                             form.model_to_postKw)
        FXLabel(postVF2, 'Stress analysis using the Hashin criterion (implemented for composite/monolitic only)')
        FXLabel(postVF2, 'This macro performs an envolope among all elements, ' +\
                        'among all the plies, considering for each ply: the ' +\
                        'bottom, the middle and the top')
        postVF2 = FXVerticalFrame(postVF, opts=LAYOUT_CENTER_X|LAYOUT_CENTER_Y)
        self.post_stress_button = FXButton(postVF2, 'Start stress analysis')
        #
        # Tabs / Post-processing tools / Utils
        #
        FXTabItem(postBook, 'Utils', None, TAB_LEFT)
        postVF = FXVerticalFrame(postBook, FRAME_RAISED|FRAME_SUNKEN)
        postVF2 = FXVerticalFrame(postVF, opts=LAYOUT_LEFT|LAYOUT_CENTER_Y)
        FXLabel(postVF2, 'Plot current field output as an opened cone/cylinder')
        FXLabel(postVF2, '')
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'opened_conecyl.png')
        icon = afxCreatePNGIcon(pngpath)
        FXLabel(postVF2, '', icon, opts=ICON_AFTER_TEXT)
        self.plot_opened_conecyl = FXButton(postVF2, 'Plot opened cone/cylinder')
        #
        # Tabs / About this plug-in
        #
        FXTabItem(mainTabBook, 'About this plug-in')
        aboutVF = FXVerticalFrame(mainTabBook, FRAME_RAISED|FRAME_SUNKEN)
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'pfh.png')
        icon = afxCreatePNGIcon(pngpath)
        FXLabel(aboutVF, 'DESICOS package Version {0}'.format(version))
        FXLabel(aboutVF, '')
        FXLabel(aboutVF, 'Released by partner:', icon, opts=ICON_AFTER_TEXT)
        pngpath = os.path.join(DAHOME, 'gui', 'icons', 'desicos2.png')
        icon = afxCreatePNGIcon(pngpath)
        FXLabel(aboutVF, '', icon)
        tmp = FXText(aboutVF, None, 0, TEXT_READONLY|LAYOUT_FIX_WIDTH|LAYOUT_FIX_HEIGHT|\
            LAYOUT_CENTER_Y, 0, 0, 700, 150)
        tmp.setText(\
                  'OBS:\n\n'
                  '- Have fun!\n\n')
        FXLabel(aboutVF, 'Contact: castrosaullo@gmail.com')
        #
        self.extraUpdates()


    def update_database(self, update_all=False):
        form = self.form
        if update_all:
            ccs = fetch('ccs', local_only=True)
            laminaprops = fetch('laminaprops')
            allowables = fetch('allowables')
            self.ccs = fetch('ccs')
            self.laminaprops = laminaprops
            self.allowables = allowables
            keys_ccs = sorted(map(str, ccs.keys()))
            keys_laminaprops = sorted(map(str, laminaprops.keys()))
            keys_allowables = sorted(map(str, allowables.keys()))

            # ccs
            keys = keys_ccs + sorted(conecylDB.include_in_GUI)
            self.ccs_keys = keys
            self.ccs_CB.clearItems()
            self.ccs_CB.appendItem('Enter New')
            for k in keys:
                self.ccs_CB.appendItem(k)

            # laminaprops
            keys = keys_laminaprops
            self.laminaprops_keys = keys
            self.stackTableListId = self.laminateTable.addList(
                                         ' \t' + '\t'.join(keys))
            self.laminateTable.setColumnListId(1, self.stackTableListId)
            self.laminaprops_CB.clearItems()
            self.laminaprops_CB.appendItem('Enter New')
            for k in keys:
                self.laminaprops_CB.appendItem(k)

            # allowables
            keys = keys_allowables
            self.allowables_keys = keys
            self.allowables_CB.clearItems()
            self.allowables_CB.appendItem('Enter New')
            for k in keys:
                self.allowables_CB.appendItem(k)
        # ccs
        k = form.ccKeyKw.getValue()
        if k in self.ccs_keys and k <> form.last_loadedKw.getValue():
           cc = self.ccs[k]
           cc_dict2form(ccname=k, cc=cc, db=self, form=form)
        if k=='Enter New':
            self.new_cc_name.enable()
            self.save_cc_button.enable()
            self.del_cc_button.disable()
        elif k=='deleted!' or k=='conecyl loaded!':
            self.new_cc_name.disable()
            self.save_cc_button.disable()
            self.del_cc_button.disable()
        else:
            self.new_cc_name.disable()
            self.save_cc_button.disable()
            self.del_cc_button.enable()
        # laminaprops
        k = form.laminapropKeyKw.getValue()
        if k in self.laminaprops_keys:
            v = self.laminaprops[k]
            vstr = ','.join([str(i) for i in v])
            form.laminapropKw.setValues(vstr)
        if k=='Enter New':
            self.new_laminaprop_name.enable()
            self.save_laminaprop_button.enable()
            self.del_laminaprop_button.disable()
        elif k=='deleted!':
            self.new_laminaprop_name.disable()
            self.save_laminaprop_button.disable()
            self.del_laminaprop_button.disable()
        else:
            self.new_laminaprop_name.disable()
            self.save_laminaprop_button.disable()
            self.del_laminaprop_button.enable()
        # allowables
        k = form.allowablesKeyKw.getValue()
        if k in self.allowables_keys:
            v = self.allowables[k]
            vstr = ','.join([str(i) for i in v])
            form.allowablesKw.setValues(vstr)
        if k=='Enter New':
            self.new_allowables_name.enable()
            self.save_allowables_button.enable()
            self.del_allowables_button.disable()
        elif k=='deleted!':
            self.new_allowables_name.disable()
            self.save_allowables_button.disable()
            self.del_allowables_button.disable()
        else:
            self.new_allowables_name.disable()
            self.save_allowables_button.disable()
            self.del_allowables_button.enable()


    def save_cc(self):
        name = self.form.new_cc_nameKw.getValue()
        value = cc_form2dict(self, self.form)
        self.form.last_loadedKw.setValue(name)
        message(conecylDB.save('ccs', name, value))


    def del_cc(self):
        name = self.form.ccKeyKw.getValue()
        message(conecylDB.delete('ccs', name))


    def save_laminaprop(self):
        name = self.form.new_laminaprop_nameKw.getValue()
        value = self.form.laminapropKw.getValues()
        value = tuple(float(i) for i in value.split(',') if i <> '')
        if len(value) == 2:
            value = (value[0], value[0], value[1])
        message(conecylDB.save('laminaprops', name, value))


    def del_laminaprop(self):
        name = self.form.laminapropKeyKw.getValue()
        message(conecylDB.delete('laminaprops', name))


    def save_allowables(self):
        name = self.form.new_allowables_nameKw.getValue()
        value = self.form.allowablesKw.getValues()
        value = tuple(float(i) for i in value.split(','))
        message(conecylDB.save('allowables', name, value))


    def del_allowables(self):
        name = self.form.allowablesKeyKw.getValue()
        message(conecylDB.delete('allowables', name))


    def extraUpdates(self):
        # updating list of studies
        keys = mdb.models.keys()
        tmplst = []
        for k in keys:
            if k[-3:] <> '_lb':
                tmplst.append(k.split('_'))
        std_names = set(['_'.join(k[:len(k)-2]) for k in tmplst])
        names = os.listdir(TMP_DIR)
        for name in names:
            if name.find('.study') > -1:
                std_names.add(name.split('.')[0])
        std_names = list(std_names)
        std_names.sort()
        #
        self.std_to_load.clearItems()
        self.std_to_post.clearItems()
        self.std_to_run.clearItems()
        for std_name in std_names:
            self.std_to_post.appendItem(std_name)
            self.std_to_load.appendItem(std_name)
            self.std_to_run.appendItem(std_name)
        self.model_to_post.clearItems()
        std_name = self.form.std_to_postKw.getValue()
        for k in keys:
            if k.find(std_name) > -1 and k.find(std_name + '_lb') == -1:
                self.model_to_post.appendItem(k)
        self.update_database(update_all=True)


    def slowUpdates(self):
        form = self.form
        std_name = form.std_to_postKw.getValue()
        self.logcount = 0
        log_path = os.path.join(TMP_DIR, std_name, 'run_log.txt')
        if os.path.isfile(log_path):
            log_file = open(log_path, 'r')
            text = ''
            for line in log_file.readlines():
                text += line
            log_file.close()
            self.exec_log.setText(text)
            self.exec_log.setCursorRow(100)


    def saveStudy(self):
        message('Saving...')
        self.form.laKw.setValue(self.lasw.getCurrent())
        self.logcount = 10000
        command = 'import gui_commands\n'    +\
                  'reload(gui_commands)\n' +\
                  'gui_commands.save_study("%s", %s)\n' \
                  % (str(self.form.std_nameKw.getValue()),
                      str(self.form.get_params_from_gui()))
        sendCommand(command)
        self.extraUpdates()


    def processUpdates(self):
        form = self.form
        std_name = form.std_nameKw.getValue()
        form.std_nameKw.setValue(rsc(std_name))

        # imp_tables[k]
        for k in ['pl', 'd', 'ax', 'lbmi', 'cut']:
            correct_num = self.imp_spinners[k].getValue()
            current_num = self.imp_current_num[k]
            if   current_num > correct_num:
                self.imp_current_num[k] = correct_num
                for col in range(correct_num+1, current_num+1):
                    self.imp_tables[k].setColumnEditable(col, False)
                    self.imp_tables[k].shadeReadOnlyItems(True)
            elif current_num < correct_num:
                self.imp_current_num[k] = correct_num
                for col in range(current_num+1, correct_num+1):
                    self.imp_tables[k].setColumnEditable(col, True)
                    num_param = self.imp_num_params[k]
                    self.imp_tables[k].setItemEditable(num_param+1, col, False)
                    self.imp_tables[k].shadeReadOnlyItems(True)
            #TODO FIXME there is an update bug in the tables
            # when the perturbation loads are deleted for example
            # sometimes they are not really deleted, specially when the user
            # does it faster

        # linking variables
        num_plies = form.laminateKw.getNumRows()
        #
        std_name = form.std_to_postKw.getValue()
        #
        self.logcount += 1
        if form.just_created_study:
            form.loaded_study = True
            form.just_created_study = False
            self.extraUpdates()
        if self.logcount > 20:
            self.slowUpdates()

        # apply Mid-Surface Imperfections
        if self.apply_imp_ms.getState() == STATE_DOWN:
            self.apply_imp_ms.setState(STATE_UP)
            std_name = form.std_nameKw.getValue()
            if not form.imp_msKw.getValue():
                message('An imperfection must be selected!')
            elif not form.loaded_study:
                message('The study must be created or loaded first!')
            else:
                form.imp_ms_std_nameKw.setValue(std_name)
                command = 'import gui_commands\n' +\
                          'reload(gui_commands)\n'
                command += form.apply_imp_ms.getCommandString()
                sendCommand(command, writeToReplay=False, writeToJournal=True)

        # apply Thickness Imperfections
        if self.apply_imp_t.getState() == STATE_DOWN:
            self.apply_imp_t.setState(STATE_UP)
            std_name = form.std_nameKw.getValue()
            if form.imp_thickKw.getValue()=='':
                message('An imperfection must be selected!')
            elif not form.loaded_study:
                message('The study must be created or loaded first!')
            else:
                form.imp_t_std_nameKw.setValue(std_name)
                command = 'import gui_commands\n' +\
                          'reload(gui_commands)\n'
                command += form.apply_imp_t.getCommandString()
                sendCommand(command, writeToReplay=False, writeToJournal=True)

        # post load shortening curve button
        if self.post_ls_button.getState() == STATE_DOWN:
            self.post_ls_button.setState(STATE_UP)
            reload(gui_plot)
            put_in_Excel = form.post_put_in_ExcelKw.getValue()
            open_Excel = form.post_open_ExcelKw.getValue()
            gui_plot.plot_ls_curve(std_name,
                                    put_in_Excel, open_Excel)
        # post knock-down curves
        if self.post_kdf_button.getState() == STATE_DOWN:
            self.post_kdf_button.setState(STATE_UP)
            reload(gui_plot)
            put_in_Excel = form.post_put_in_ExcelKw.getValue()
            open_Excel = form.post_open_ExcelKw.getValue()
            gui_plot.plot_kdf_curve(std_name,
                                     put_in_Excel, open_Excel,
                                     configure_session=False)
        # post stress analysis button
        if self.post_stress_button.getState() == STATE_DOWN:
            self.post_stress_button.setState(STATE_UP)
            reload(gui_plot)
            cc_name = form.model_to_postKw.getValue()
            gui_plot.plot_stress_analysis(std_name, cc_name)
        # plot opened conecyl
        if self.plot_opened_conecyl.getState() == STATE_DOWN:
            self.plot_opened_conecyl.setState(STATE_UP)
            reload(gui_plot)
            gui_plot.plot_opened_conecyl(std_name)
        # cc, laminapropKeys, plyts, stack,  laminaprop and allowables updates
        self.update_database()
        if self.save_cc_button.getState() == STATE_DOWN:
            self.save_cc_button.setState(STATE_UP)
            tmp = form.new_cc_nameKw.getValue()
            form.new_cc_nameKw.setValue(rsc(tmp))
            self.save_cc()
            self.update_database(update_all=True)
        if self.del_cc_button.getState() == STATE_DOWN:
            self.del_cc_button.setState(STATE_UP)
            self.del_cc()
            form.ccKeyKw.setValue('deleted!')
            self.update_database(update_all=True)
        if self.save_laminaprop_button.getState() == STATE_DOWN:
            self.save_laminaprop_button.setState(STATE_UP)
            tmp = form.new_laminaprop_nameKw.getValue()
            form.new_laminaprop_nameKw.setValue(rsc(tmp))
            self.save_laminaprop()
            self.update_database(update_all=True)
        if self.del_laminaprop_button.getState() == STATE_DOWN:
            self.del_laminaprop_button.setState(STATE_UP)
            self.del_laminaprop()
            form.laminapropKeyKw.setValue('deleted!')
            self.update_database(update_all=True)
        if self.save_allowables_button.getState() == STATE_DOWN:
            self.save_allowables_button.setState(STATE_UP)
            tmp = form.new_allowables_nameKw.getValue()
            form.new_allowables_nameKw.setValue(rsc(tmp))
            self.save_allowables()
            self.update_database(update_all=True)
        if self.del_allowables_button.getState() == STATE_DOWN:
            self.del_allowables_button.setState(STATE_UP)
            self.del_allowables()
            form.allowablesKeyKw.setValue('deleted!')
            self.update_database(update_all=True)
        # run models
        if self.exec_std.getState() == STATE_DOWN:
            self.exec_std.setState(STATE_UP)
            self.logcount = 10000
            ncpus = form.ncpusKw.getValue()
            command = ('import __main__\n' +
                       '__main__.stds["{0}"].write_inputs()\n'.format(std_name))
            sendCommand(command)
            reload(gui_commands)
            gui_commands.run_study(std_name, ncpus, form.use_job_stopperKw.getValue())
        # save study
        if self.save_std.getState() == STATE_DOWN:
            self.save_std.setState(STATE_UP)
            self.saveStudy()
        # load study
        if self.load_std.getState() == STATE_DOWN:
            self.load_std.setState(STATE_UP)
            message('Loading...')
            self.logcount = 10000
            command = 'import gui_commands\n'    +\
                      'reload(gui_commands)\n' +\
                      'gui_commands.load_study("%s")\n' % std_name
            sendCommand(command)
            reload(gui_commands)
            gui_commands.load_study_gui(std_name, form)
            message('The DESICOS study "%s.study" has been opened.' \
                     % os.path.join(TMP_DIR, std_name))
            message(' ')
            form.loaded_study = True
            return

        # changing variable widgets
        if form.displ_controlledKw.getValue():
            self.axial_displ.enable()
            self.axial_load.disable()
            self.axial_step.disable()
        else:
            self.axial_displ.disable()
            self.axial_load.enable()
            self.axial_step.enable()

        if form.separate_load_stepsKw.getValue():
            self.art_damp1.enable()
            self.damp_factor1.enable()
            self.minInc1.enable()
            self.initialInc1.enable()
            self.maxInc1.enable()
            self.maxNumInc1.enable()
        else:
            self.art_damp1.disable()
            self.damp_factor1.disable()
            self.minInc1.disable()
            self.initialInc1.disable()
            self.maxInc1.disable()
            self.maxNumInc1.disable()

        #if form.laKw.getValue() == False:
        #    self.la_beta.disable()
        #    self.la_omega.disable()
        #else:
        #    self.la_beta.enable()
        #    self.la_omega.enable()
        # default profile
        # webBrowser url
        #TODO
        if False:
            #FXMAPFUNC(...
            status = webBrowser.openWithURL('www.pfh.de')
            status = webBrowser.openWithURL('www.desicos.eu')
        return


    def show(self):

        # Note: This method is only necessary because the prototype
        # application allows changes to be made in the dialog code and
        # reloaded while the application is still running. Normally you
        # would not need to have a show() method in your dialog.

        # Resize the dialog to its default dimensions to account for
        # any widget changes that may have been made.
        #
        self.resize(self.getDefaultWidth(), self.getDefaultHeight())
        AFXDataDialog.show(self)

