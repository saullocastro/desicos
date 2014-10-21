#!/usr/bin/env python
from multiprocessing import Process, Manager, Value, Array,freeze_support
import logging
from threading import Thread
import threading
import thread
import io
import sys
import PySide
import time
import sys
import os
import json
#from PySide.QtCore import QRect, QMetaObject, QObject
#from PySide.QtGui  import (QApplication, QMainWindow, QWidget, 
#			QGridLayout, QTabWidget, QPlainTextEdit,
#			QMenuBar, QMenu, QStatusBar, QAction, 
#			QIcon, QFileDialog, QMessageBox, QFont)

from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import *

from PySide.QtGui  import *
from PySide import QtWebKit

#sys.path.append( '../stochastic/')

from stochastic.imperfGen import *
from viewer import DesicosViewer3D

from conecylDB import *
class MyStream(QtCore.QObject):
	message = QtCore.Signal(str)
	def __init__(self, parent=None):
		super(MyStream, self).__init__(parent)

	def write(self, message):
		self.message.emit(str(message))
	
	def flush(self):
		pass
myStream = MyStream()
msgStream=io.TextIOBase()
msgStream=myStream
#sys.stdout=myStream
#sys.stderr=myStream

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S ', level=logging.INFO,stream=myStream)
#mlog=multiprocessing.log_to_stderr()

#mlog.setLevel(logging.INFO)

class DesicosStGenUI(QMainWindow):
	def __init__(self, parent=None):
		super(DesicosStGenUI, self).__init__(parent)
#		try:
		fp=open('config.json')
		fd=''
		for l in fp:
			fd+=l
		fp.close()
		self.config=json.loads(fd)
		self.sg=ImperfFactory(self.config['conecylDB_file'] )
		self.ccdb=ConeCylDB(self.config['conecylDB_file'])

#		except:
#			logging.info('Can`t configure')
	
		self.viewTabViewCCDBvsTXT='CCDB'
		self.viewMode='folded'
		self.evalTabImpType='ms'
#		sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
#		sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)
		self.amplThreshold=5e-10
		self.fxMax=0.1
		self.fyMax=0.1
		
		self.initUI()

	def normalOutputWritten(self, text):
		cursor = self.msgDISP.textCursor()
		cursor.movePosition(QtGui.QTextCursor.End)
		cursor.insertText(text)
		self.msgDISP.setTextCursor(cursor)
		self.msgDISP.ensureCursorVisible()
	def __del__(self):
		# Restore sys.stdout
		sys.stderr = sys.__stderr__


	@QtCore.Slot(str)
	def on_myStream_message(self, message):
		self.msgDISP.moveCursor(QtGui.QTextCursor.End)
		self.msgDISP.insertPlainText(message)


	def initUI(self):
		self.inputsOK=False
		self.input1CC=None

		self.resize(800, 600)
		mainWidget=QtGui.QWidget(self)
		self.setCentralWidget(mainWidget)
		vLayout=QtGui.QVBoxLayout(mainWidget)
		
		self.mainTabWidget = QTabWidget(mainWidget)
		vLayout.addWidget(self.mainTabWidget)
	
		self.msgDISP=QtGui.QTextEdit(mainWidget)
		vLayout.addWidget(self.msgDISP)

		self.tabInputs = QWidget()
		inpLayout=QVBoxLayout(self.tabInputs)

		inputTab=QTabWidget(self.mainTabWidget)
		inputTab.setTabPosition(QTabWidget.West)
#### View tab
		viewTab = QWidget()
		viewTabLayoutV=QVBoxLayout(viewTab)
		viewTabLayoutV.setAlignment(QtCore.Qt.AlignTop)
		viewTabLayoutHW=QWidget()
		viewTabLayoutH=QHBoxLayout(viewTabLayoutHW)
		viewTabLayoutH.setAlignment(QtCore.Qt.AlignTop)
		viewTabLayoutG1W=QWidget()
		viewTabLayoutG1=QGridLayout(viewTabLayoutG1W)
#		viewTabLayoutG1.setAlignment(QtCore.Qt.AlignTop)
		viewTabLayoutG2W=QWidget()
		viewTabLayoutG2=QGridLayout(viewTabLayoutG2W)
#		viewTabLayoutG2.setAlignment(QtCore.Qt.AlignTop)

		viewTabLabel_ViewTab=QLabel(u'Visualize imperfections')
		viewTabLabel_ViewTab.setAlignment(QtCore.Qt.AlignTop)
		viewTabLayoutV.addWidget(viewTabLabel_ViewTab)

		viewTabLayoutV.addWidget(viewTabLayoutHW)
		viewTabLayoutH.addWidget(viewTabLayoutG1W)
		viewTabLayoutH.addWidget(viewTabLayoutG2W)


		viewTabLabel_ViewVTK=QLabel(u'View a VTK file')

		viewTabLabel_ViewVTKFile=QLabel(u'Select VTK file to view:')

		self.viewTabViewVTKTW=QtGui.QTableWidget(1,1,viewTabLayoutG1W)
		self.viewTabViewVTKTW.setItem(0,0,QtGui.QTableWidgetItem())
#		self.viewTabViewVTKTW.item(0,0).setText(os.getcwd())
		self.viewTabViewVTKTW.verticalHeader().setVisible(False)
		self.viewTabViewVTKTW.horizontalHeader().setVisible(False)
		self.viewTabViewVTKTW.verticalHeader().setResizeMode(QHeaderView.Stretch)
		self.viewTabViewVTKTW.horizontalHeader().setResizeMode(QHeaderView.Stretch)
		self.viewTabViewVTKTW.setMaximumHeight(22)

		self.viewTabViewVTKSubmitBT=QPushButton(u'Submit VTK file for viewing')
	
		viewTabLabel_ViewOptionsLabel=QLabel(u' ---   View options  ---')

		viewTabOptFoldButtonGroup=QButtonGroup(viewTabLayoutG1W)
		viewTabOptFoldRadButton=QRadioButton(u'Folded view',viewTabLayoutG1W)
		viewTabOptFoldRadButton.setChecked(True)
		viewTabOptUnfoldRadButton=QRadioButton(u'Unfolded view',viewTabLayoutG1W)

		viewTabLabel_ViewCCDBTXT=QLabel(u'View ConeCylDB entry or TXT file')

		viewTabCCDBTXTButtonGroup=QButtonGroup(viewTabLayoutG2W)
		viewTabViewCCDBRadButton=QRadioButton(u'View ConeCylDB',viewTabLayoutG2W)
		viewTabViewCCDBRadButton.setChecked(True)
		viewTabViewTXTRadButton=QRadioButton(u'View TXT file',viewTabLayoutG2W)
	
		viewTabLabel_ExtractFromVTK=QLabel(u'Extract imperfection from VTK file?')
		viewTabLabel_ExtractFromVTK_PLACEHOLDER=QLabel(u'TO BE DONE IN NEXT VERSION')
		
		self.viewTabViewTXTTW=QtGui.QTableWidget(1,1,viewTabLayoutG2W)
		self.viewTabViewTXTTW.setItem(0,0,QtGui.QTableWidgetItem())
#		self.viewTabViewTXTTW.item(0,0).setText(os.getcwd())
		self.viewTabViewTXTTW.verticalHeader().setVisible(False)
		self.viewTabViewTXTTW.horizontalHeader().setVisible(False)
		self.viewTabViewTXTTW.verticalHeader().setResizeMode(QHeaderView.Stretch)
		self.viewTabViewTXTTW.horizontalHeader().setResizeMode(QHeaderView.Stretch)
		self.viewTabViewTXTTW.setMaximumHeight(22)
		self.viewTabViewTXTTW.setVisible(False)

		self.viewTabViewCCDBCBox=QComboBox(viewTabLayoutG2W)
		self.viewTabCCDBCBPopulate()		

		viewTabViewTxtScalingLabel=QLabel(u'Scaling Factor:')
		self.viewTabScalingDSBox=QDoubleSpinBox(viewTabLayoutG2W)
		self.viewTabScalingDSBox.setValue(1.0)
		self.viewTabScalingDSBox.setRange(0.1,1e3)
	
		viewTabViewTxtOptionsLabel=QLabel(u'Surface reconstruction options:')
		viewTabViewTxtNBSizeLabel=QLabel(u'Neighborhood Size :')
		viewTabViewTxtSmSpacingLabel=QLabel(u'Sample Spacing :')
		
		self.viewTabViewTxtNBSizeSBox=QSpinBox(viewTabLayoutG2W)
		self.viewTabViewTxtNBSizeSBox.setRange(1,100000)
		self.viewTabViewTxtNBSizeSBox.setValue(80)
		
		self.viewTabViewTxtSmSpacingDSBox=QDoubleSpinBox(viewTabLayoutG2W)
		self.viewTabViewTxtSmSpacingDSBox.setValue(8.0)
		self.viewTabViewTxtSmSpacingDSBox.setRange(0.01,1e15)
	
		viewTabViewTxtSaveVTPLabel=QLabel(u'Save to VTK file?')
		
		self.viewTabViewCCDBTXTSubmitBT=QPushButton('Submit for viewing')
		
	
		self.viewTabSaveVTPTW=QtGui.QTableWidget(1,1,viewTabLayoutG2W)
		self.viewTabSaveVTPTW.verticalHeader().setVisible(False)
		self.viewTabSaveVTPTW.horizontalHeader().setVisible(False)
		self.viewTabSaveVTPTW.verticalHeader().setResizeMode(QHeaderView.Stretch)
		self.viewTabSaveVTPTW.horizontalHeader().setResizeMode(QHeaderView.Stretch)
		self.viewTabSaveVTPTW.setMaximumHeight(22)
		self.viewTabSaveVTPTW.setItem(0, 0,QtGui.QTableWidgetItem())
		self.viewTabSaveVTPTW.item(0,0).setText('output.vtp')

		self.viewTabSaveVTPBT=QPushButton('Save VTK file')	

		viewTabLayoutG1.addWidget(viewTabLabel_ViewVTK,0,0,2,6)
		viewTabLayoutG1.addWidget(viewTabLabel_ViewVTKFile,2,0,1,1)
		viewTabLayoutG1.addWidget(self.viewTabViewVTKTW,3,0,2,6)
		viewTabLayoutG1.addWidget(self.viewTabViewVTKSubmitBT,5,0,2,6)
		viewTabLayoutG1.addWidget(viewTabLabel_ExtractFromVTK,8,0,2,6)
		viewTabLayoutG1.addWidget(viewTabLabel_ExtractFromVTK_PLACEHOLDER,10,0,6,6)
		viewTabLayoutG1.addWidget(viewTabLabel_ViewOptionsLabel,18,3,2,6)
		viewTabLayoutG1.addWidget(viewTabOptFoldRadButton,20,0,1,3)
		viewTabLayoutG1.addWidget(viewTabOptUnfoldRadButton,20,3,1,3)

		viewTabLayoutG2.addWidget(viewTabLabel_ViewCCDBTXT,0,0,2,6)
		viewTabLayoutG2.addWidget(viewTabViewCCDBRadButton,2,0)
		viewTabLayoutG2.addWidget(viewTabViewTXTRadButton,2,3)
		viewTabLayoutG2.addWidget(self.viewTabViewTXTTW,3,0,2,6)	
		viewTabLayoutG2.addWidget(self.viewTabViewCCDBCBox,3,0,2,6)
		viewTabLayoutG2.addWidget(viewTabViewTxtScalingLabel,5,0,2,3)
		viewTabLayoutG2.addWidget(self.viewTabScalingDSBox,5,3,2,3)
		viewTabLayoutG2.addWidget(viewTabViewTxtOptionsLabel,7,0,1,6)
		viewTabLayoutG2.addWidget(viewTabViewTxtNBSizeLabel,8,0,2,3)
		viewTabLayoutG2.addWidget(self.viewTabViewTxtNBSizeSBox,8,3,2,3)
		viewTabLayoutG2.addWidget(viewTabViewTxtSmSpacingLabel,10,0,2,3)
		viewTabLayoutG2.addWidget(self.viewTabViewTxtSmSpacingDSBox,10,3,2,3)
		viewTabLayoutG2.addWidget(self.viewTabViewCCDBTXTSubmitBT,14,0,1,6)
		viewTabLayoutG2.addWidget(viewTabViewTxtSaveVTPLabel,16,0,1,6)
		viewTabLayoutG2.addWidget(self.viewTabSaveVTPTW,17,0,1,6)
		viewTabLayoutG2.addWidget(self.viewTabSaveVTPBT,18,0,1,6)
		
		self.mainTabWidget.addTab(viewTab,'View imperfections')

### viewTab connectors
		self.viewTabViewVTKTW.itemDoubleClicked.connect(self.viewTabViewVTKSetFile)
		self.viewTabViewVTKSubmitBT.clicked.connect(self.viewTabSubmitVTKFile)
		viewTabOptFoldRadButton.clicked.connect(self.viewTabSetFoldView)
		viewTabOptUnfoldRadButton.clicked.connect(self.viewTabSetUnfoldView)

		viewTabViewCCDBRadButton.clicked.connect(self.viewTabShowCCDBBox)
		viewTabViewTXTRadButton.clicked.connect(self.viewTabShowTXTTW)
		self.viewTabViewTXTTW.itemDoubleClicked.connect(self.viewTabViewTXTSetFile)
		self.viewTabViewCCDBTXTSubmitBT.clicked.connect(self.viewTabSumbitCCDBTXTFile)
		self.viewTabSaveVTPTW.itemDoubleClicked.connect(self.viewTabViewVTKOUTSetFile)
		self.viewTabSaveVTPBT.clicked.connect(self.viewTabSumbitVTKOutFile)

##### input from txt files	
		inTxtTab = QWidget()
		inTxtLayoutV=QVBoxLayout(inTxtTab)
		inTxtLayoutHw=QWidget()
		inTxtLayoutH=QHBoxLayout(inTxtLayoutHw)
		inTxtLayoutV2w=QWidget()
		inTxtLayoutV2=QGridLayout(inTxtLayoutV2w)

		inTxtLabel=QtGui.QLabel(u"Select inputs from plain text files",inTxtTab)

		self.inTxtTable = QtGui.QTableWidget(inTxtTab)
		self.inTxtTable.setMinimumSize(330,500)
		inTxtHeader = self.inTxtTable.horizontalHeader()
		inTxtHeader.setResizeMode(QHeaderView.Stretch)
		inTxtHeader.setTextElideMode(QtCore.Qt.ElideLeft)	

		self.inTxtTable.setColumnCount(2)
		self.inTxtTable.setRowCount(1)
		self.inTxtTable.setColumnWidth(0,  160)
		self.inTxtTable.setColumnWidth(1,  160)
		self.inTxtTable.setHorizontalHeaderLabels(["Mid surface imperfections:","Thickness imperfections:" ])
		self.inTxtTable.setItem(0, 0,QtGui.QTableWidgetItem())
		self.inTxtTable.setItem(0, 1,QtGui.QTableWidgetItem())

		self.submitInputTableTxtBT=QtGui.QPushButton("Submit for processing",inTxtTab)
		inTxtTableAddRowBT=QtGui.QPushButton("Add Row",inTxtTab)
		self.inTxtTableDelRowBT=QtGui.QPushButton("Delete Row",inTxtTab)
		self.inTxtTableReset=QtGui.QPushButton("Clear table",inTxtTab)
	

		inTxtLabMSG=QtGui.QLabel(u"Set MEASURED cylinder parameters:",inTxtTab)
		inTxtLabFig=QtGui.QLabel(inTxtTab)
		inTxtLabFig.setPixmap(QtGui.QPixmap("gui/geometry.png"))
		inTxtLabSetR=QtGui.QLabel(u"Cylinder Radius R [mm]  :",inTxtTab)
		inTxtLabSetH=QtGui.QLabel(u"Cylinder Height H [mm]  :",inTxtTab)
		inTxtLabSetA=QtGui.QLabel(u"Cylinder Angle  alpha [deg]  :",inTxtTab)
		self.inTxtIN_R=QtGui.QDoubleSpinBox(inTxtTab)
		self.inTxtIN_H=QtGui.QDoubleSpinBox(inTxtTab)
		self.inTxtIN_A=QtGui.QDoubleSpinBox(inTxtTab)
		self.inTxtIN_R.setRange(0,1e15)
		self.inTxtIN_H.setRange(0,1e15)
		self.inTxtIN_A.setRange(0,89.0)
		self.inTxtIN_R.setValue(250.)
		self.inTxtIN_H.setValue(500.)
		self.inTxtIN_A.setValue(0.)
		

		inTxtLayoutV.addWidget(inTxtLabel)
		inTxtLayoutV.addWidget(inTxtLayoutHw)
		inTxtLayoutH.addWidget(self.inTxtTable)
		inTxtLayoutH.addWidget(inTxtLayoutV2w)

		inTxtLayoutV2.addWidget(inTxtLabFig,0,0,2,2)
		inTxtLayoutV2.addWidget(inTxtLabMSG,3,0)
		inTxtLayoutV2.addWidget(inTxtLabSetR,4,0)
		inTxtLayoutV2.addWidget(self.inTxtIN_R,4,1)
		inTxtLayoutV2.addWidget(inTxtLabSetH,5,0)
		inTxtLayoutV2.addWidget(self.inTxtIN_H,5,1)
		inTxtLayoutV2.addWidget(inTxtLabSetA,6,0)
		inTxtLayoutV2.addWidget(self.inTxtIN_A,6,1)
		inTxtLayoutV2.addWidget(inTxtTableAddRowBT,7,0)
		inTxtLayoutV2.addWidget(self.inTxtTableDelRowBT,7,1)
		inTxtLayoutV2.addWidget(self.submitInputTableTxtBT,8,0)
		inTxtLayoutV2.addWidget(self.inTxtTableReset)
	###.inTxtTab connectors:
		inTxtTableAddRowBT.clicked.connect(self.inTxtTableAddRow)
		self.inTxtTableDelRowBT.clicked.connect(self.inTxtTableDeleteRow)
		self.inTxtTable.itemDoubleClicked.connect(self.inTxtTableEditCell)
		self.inTxtTableReset.clicked.connect(self.inTxtTableClearAll)
		self.submitInputTableTxtBT.clicked.connect(self.submitInputTableTxt)
		inputTab.addTab(inTxtTab,'From txt files')

##### input from ccDB	
		inCCTab = QWidget()
		inCCLayoutV=QVBoxLayout(inCCTab)
		inCCLayoutHw=QWidget()
		inCCLayoutH=QHBoxLayout(inCCLayoutHw)
		inCCLayoutV2w=QWidget()
		inCCLayoutV2=QVBoxLayout(inCCLayoutV2w)
		inCCLayoutV2.setAlignment(QtCore.Qt.AlignTop)
		inCCLabel=QtGui.QLabel(u"Select inputs from DESICOS conecyl DB",inCCTab)

		self.inCCTable = QtGui.QTableWidget(inCCTab)
		self.inCCTable.setColumnCount(1)
		self.inCCTable.setRowCount(0)
		self.inCCTable.setHorizontalHeaderLabels(["Use:    ConecylDB sample"])
		self.inCCTable.setMinimumSize(330,500)
		inCCHeader = self.inCCTable.horizontalHeader()
		inCCHeader.setResizeMode(QHeaderView.Stretch)
		inCCHeader.setTextElideMode(QtCore.Qt.ElideLeft)
		self.inCCTablePopulate()
		self.inCCTableSubmitBT=QtGui.QPushButton("Submit for processing",inCCTab)
		self.inCCTableSelectAllBT=QtGui.QPushButton("Select all",inCCTab)
		self.inCCTableDeselectAllBT=QtGui.QPushButton("Deselect all",inCCTab)

		inCCLayoutV.addWidget(inCCLabel)
		inCCLayoutV.addWidget(inCCLayoutHw)
		inCCLayoutH.addWidget(self.inCCTable)
		inCCLayoutH.addWidget(inCCLayoutV2w)
		inCCLayoutV2.addWidget(self.inCCTableSubmitBT)
		inCCLayoutV2.addWidget(self.inCCTableSelectAllBT)
		inCCLayoutV2.addWidget(self.inCCTableDeselectAllBT)

	###inCCTab connectors:
		inTxtTableAddRowBT.clicked.connect(self.inTxtTableAddRow)
		self.inCCTableSelectAllBT.clicked.connect(self.inCCTabSelectAll)
		self.inCCTableDeselectAllBT.clicked.connect(self.inCCTabDeselectAll)
		self.inCCTableSubmitBT.clicked.connect(self.inCCTabSubmit)
		inputTab.addTab(inCCTab,'From conecyl DB')
		self.mainTabWidget.addTab(inputTab,'1) Select inputs')


###Evaluate Tab
		self.evalTabWidget = QWidget()
		evalLayoutV = QVBoxLayout(self.evalTabWidget)
		evalLayoutV.setAlignment(QtCore.Qt.AlignTop)
		evalLabel=QtGui.QLabel(u"Evaluate input files before generating new samples",self.evalTabWidget)
		evalLayoutGW = QWidget()
		evalLayoutG = QGridLayout(evalLayoutGW)
		evalLayoutV.addWidget(evalLabel)
		evalLayoutV.addWidget(evalLayoutGW)
		
		
		self.mainTabWidget.addTab(self.evalTabWidget,'2) Process inputs')
		evalTabImTypeLabel=QLabel(r'Select imperfection type to evaluate : ')
		evalTabImRadButtonGroup=QButtonGroup(evalLayoutGW)
		self.evalTabImMidsRadButton=QRadioButton('Midsurface imperfection',evalLayoutGW)
		self.evalTabImMidsRadButton.setChecked(True)
		self.evalTabImThickRadButton=QRadioButton('Thickness imperfection',evalLayoutGW)
		evalTabSetAmplLabel=QLabel('Power spectrum aplitude threshold:')
		self.evalTabSetAmplLineEdit=QLineEdit(str(self.amplThreshold),self.evalTabWidget)
		self.evalTabSetAmplLineEdit.setFixedWidth(80)	

		evalTabFxLabel=QLabel('Maximum freq. fraction   -   Radial direction :')
		self.evalTabFxDSBox=QDoubleSpinBox(self.evalTabWidget)
		self.evalTabFxDSBox.setDecimals(4)
		self.evalTabFxDSBox.setRange(0.01,1.0)
		self.evalTabFxDSBox.setValue(0.1)
		self.evalTabFxDSBox.setSingleStep(0.05)
	
		evalTabFyLabel=QLabel('Axial direction :')
		self.evalTabFyDSBox=QDoubleSpinBox(self.evalTabWidget)
		self.evalTabFyDSBox.setDecimals(4)
		self.evalTabFyDSBox.setRange(0.01,1.0)
		self.evalTabFyDSBox.setValue(0.1)
		self.evalTabFyDSBox.setSingleStep(0.05)

		evalTabRadSamLabel=QLabel('Radial sampling: ')
		self.evalTabRadSamSBox=QSpinBox(self.evalTabWidget)
		self.evalTabRadSamSBox.setRange(36,10000)
		self.evalTabRadSamSBox.setValue(256)
		
		evalTabAxiSamLabel=QLabel('Axial sampling: ')
		self.evalTabAxiSamSBox=QSpinBox(self.evalTabWidget)
		self.evalTabAxiSamSBox.setRange(10,10000)
		self.evalTabAxiSamSBox.setValue(80)

		evalTabFilterLabel=QLabel('Imperfection filter: ')
		self.evalTabFilterCB=QComboBox(self.evalTabWidget)
		
		self.evalTabShowFilterButton=QPushButton('View current filter')

		self.evalTabRecomputeButton=QPushButton('Recompute with new settings')
		self.evalTabShowAvfButton=QPushButton('View average imperfection',self.evalTabWidget)
		evalTabShowAvfScalingLabel=QLabel('Scaling factor: ')
		self.evalTabAvfScalingDSBox=QDoubleSpinBox(self.evalTabWidget)
		self.evalTabAvfScalingDSBox.setRange(0.05,1.0e10)
		self.evalTabAvfScalingDSBox.setValue(100.)

		self.evalTabShowRedSpectrumButton=QPushButton('View reduced power spectrum')
		evalTabShowPowSpectrumScalingLabel=QLabel('Scaling factor: ')
		self.evalTabPowSpectrumScalingDSBox=QDoubleSpinBox(self.evalTabWidget)
		self.evalTabPowSpectrumScalingDSBox.setRange(0.05,1.0e10)
		self.evalTabPowSpectrumScalingDSBox.setValue(100.)

		evalTabMaterialLabel=QLabel('Apply material pattern:')
		self.evalTabMaterialCB=QComboBox(self.evalTabWidget)


		evalLayoutG.addWidget(evalTabImTypeLabel,0,0,2,2)
		evalLayoutG.addWidget(self.evalTabImMidsRadButton,0,3,2,2)
		evalLayoutG.addWidget(self.evalTabImThickRadButton,0,6,2,2)
		evalLayoutG.addWidget(evalTabSetAmplLabel,3,0,1,1)
		evalLayoutG.addWidget(self.evalTabSetAmplLineEdit,3,3,1,1)
		evalLayoutG.addWidget(evalTabFxLabel,4,0,1,2)
		evalLayoutG.addWidget(self.evalTabFxDSBox,4,3,1,1)
		evalLayoutG.addWidget(evalTabFyLabel,4,4,1,1)
		evalLayoutG.addWidget(self.evalTabFyDSBox,4,5,1,1)
		evalLayoutG.addWidget(evalTabRadSamLabel,5,0,1,2)
		evalLayoutG.addWidget(self.evalTabRadSamSBox,5,3,1,1)
		evalLayoutG.addWidget(evalTabAxiSamLabel,5,4,1,1)
		evalLayoutG.addWidget(self.evalTabAxiSamSBox,5,5,1,1)
		evalLayoutG.addWidget(evalTabFilterLabel,6,0,1,1)
		evalLayoutG.addWidget(self.evalTabFilterCB,6,3,1,1)
		evalLayoutG.addWidget(self.evalTabShowFilterButton,6,4,1,1)
		evalLayoutG.addWidget(self.evalTabRecomputeButton,9,0,1,3)
		evalLayoutG.addWidget(self.evalTabShowAvfButton,11,0,1,1)
		evalLayoutG.addWidget(evalTabShowAvfScalingLabel,11,2,1,1)
		evalLayoutG.addWidget(self.evalTabAvfScalingDSBox,11,3,1,1)
		evalLayoutG.addWidget(self.evalTabShowRedSpectrumButton,12,0,1,1)
		evalLayoutG.addWidget(evalTabShowPowSpectrumScalingLabel,12,2,1,1)
		evalLayoutG.addWidget(self.evalTabPowSpectrumScalingDSBox,12,3,1,1)
		evalLayoutG.addWidget(evalTabMaterialLabel,13,0,1,1)
		evalLayoutG.addWidget(self.evalTabMaterialCB,13,3,1,1)

	###eval Tab connectors:
		self.evalTabFilterCBPopulate()
		self.evalTabSetAmplLineEdit.editingFinished.connect(self.evalTabSetAmplThreshold)
		self.evalTabFilterCB.currentIndexChanged.connect(self.evalTabSetFilter)
		self.evalTabShowFilterButton.clicked.connect(self.evalTabShowFilter)
		self.evalTabShowAvfButton.clicked.connect(self.evalTabShowAverageIm)
		self.evalTabSetSampling()
		self.evalTabRadSamSBox.valueChanged.connect(self.evalTabSetSampling)
		self.evalTabAxiSamSBox.valueChanged.connect(self.evalTabSetSampling)
		self.evalTabRecomputeButton.clicked.connect(self.evalTabRecompute)
		self.evalTabShowRedSpectrumButton.clicked.connect(self.evalTabShowReducedSpectrum)
		self.evalTabMaterialCBPopulate()
		
###save Tab
		self.saveTabWidget = QWidget()
		saveLayout = QVBoxLayout(self.saveTabWidget)
		saveLabel=QtGui.QLabel(u"Save new samples",self.saveTabWidget)
		font=saveLabel.font()
#		font.setPointSize(72)
		saveLabel.setFont(font)
		saveLayoutHW=QWidget()
		saveLayoutHW.setMinimumSize(330,500)
		saveLayoutH=QHBoxLayout(saveLayoutHW)
		saveLayoutTxtsW=QWidget()
		saveLayoutCCDBW=QWidget()
		saveLayoutTxts=QGridLayout(saveLayoutTxtsW)
		saveLayoutTxts.setAlignment(QtCore.Qt.AlignTop)
		saveLayoutTxts.setSpacing(40)

		saveLayoutCCDB=QGridLayout(saveLayoutCCDBW)
		saveLayoutCCDB.setAlignment(QtCore.Qt.AlignTop)
		saveLayoutCCDB.setSpacing(40)

		saveLabelTxt=QtGui.QLabel(u"Save as txt files to folder: ",self.saveTabWidget)
		saveLabelCCDB=QtGui.QLabel(u"Save to conecylDB: ",self.saveTabWidget)
		saveLabelNrSamples=QtGui.QLabel(u"Number of samples to generate:",self.saveTabWidget)
		saveLabelSelectFolder=QtGui.QLabel(u"Select Folder, where to save new samples:",self.saveTabWidget)
		saveLabelSelectBnTxt=QtGui.QLabel(u"Select BASENAME for new samples:",self.saveTabWidget)
		saveLabelSelectBnCCDB=QtGui.QLabel(u"Select BASENAME for new samples:",self.saveTabWidget)
		saveLabelNrSamples.setAlignment(QtCore.Qt.AlignCenter)
		saveLabelNrSamples2=QtGui.QLabel(u"Number of samples to generate:",self.saveTabWidget)
		saveLabelNrSamples2.setAlignment(QtCore.Qt.AlignCenter)
		saveLabelCopyPropsCCDB=QtGui.QLabel(u"Use material properties inherited from:",self.saveTabWidget)
		
		self.saveNrSamplesCCDBBox=QtGui.QSpinBox(self.saveTabWidget)
		self.saveNrSamplesTxtBox=QtGui.QSpinBox(self.saveTabWidget)
		self.saveNrSamplesCCDBBox.setRange(1,1000)
		self.saveNrSamplesTxtBox.setRange(1,1000)
		self.saveToTxtNameLineEdit=QtGui.QLineEdit(self.saveTabWidget)
		self.saveToTxtNameLineEdit.setText('Sample')
		self.saveToCCDBNameLineEdit=QtGui.QLineEdit(self.saveTabWidget)
		self.saveToCCDBNameLineEdit.setText('Sample')
		
		self.saveToFolderNameTW=QtGui.QTableWidget(1,1,self.saveTabWidget)
		self.saveToFolderNameTW.setItem(0,0,QtGui.QTableWidgetItem())
		self.saveToFolderNameTW.item(0,0).setText(os.getcwd())
		self.saveToFolderNameTW.verticalHeader().setVisible(False)
		self.saveToFolderNameTW.horizontalHeader().setVisible(False)
		self.saveToFolderNameTW.verticalHeader().setResizeMode(QHeaderView.Stretch)
		self.saveToFolderNameTW.horizontalHeader().setResizeMode(QHeaderView.Stretch)
		self.saveToFolderNameTW.setMaximumHeight(22)
		self.saveCopyPropsCB=QtGui.QComboBox(self.saveTabWidget)
		self.saveCopyPropsCB.setMaximumHeight(22)

		self.saveTxtBT=QtGui.QPushButton("SAVE new samples to folder",self.saveTabWidget)
		self.saveCCDBBT=QtGui.QPushButton("SAVE new samples to conecylDB",self.saveTabWidget)

		saveLayout.addWidget(saveLabel,QtCore.Qt.AlignTop)
		saveLayout.addWidget(saveLayoutHW)
		saveLayoutH.addWidget(saveLayoutTxtsW)
		saveLayoutH.addWidget(saveLayoutCCDBW)
		########saveLayoutTxts
		saveLayoutTxts.addWidget(saveLabelTxt,0,0,1,6,QtCore.Qt.AlignHCenter)
		saveLayoutTxts.addWidget(saveLabelNrSamples,3,0,1,3)
		saveLayoutTxts.addWidget(self.saveNrSamplesTxtBox,3,3,1,1)
		saveLayoutTxts.addWidget(saveLabelSelectBnTxt,5,0,2,6)
		saveLayoutTxts.addWidget(self.saveToTxtNameLineEdit,6,0,1,6)
		saveLayoutTxts.addWidget(saveLabelSelectFolder,9,0,3,6)
		saveLayoutTxts.addWidget(self.saveToFolderNameTW,10,0,2,6)
		saveLayoutTxts.addWidget(self.saveTxtBT,14,0,1,6)		
		########saveLayoutCCDB
		saveLayoutCCDB.addWidget(saveLabelCCDB,0,0,1,6,QtCore.Qt.AlignHCenter)
		saveLayoutCCDB.addWidget(saveLabelNrSamples2,3,0,1,3)
		saveLayoutCCDB.addWidget(self.saveNrSamplesCCDBBox,3,3,1,1)
		saveLayoutCCDB.addWidget(saveLabelSelectBnCCDB,5,0,2,6)
		saveLayoutCCDB.addWidget(self.saveToCCDBNameLineEdit,6,0,1,6)
		saveLayoutCCDB.addWidget(saveLabelCopyPropsCCDB,9,0,3,6)
		saveLayoutCCDB.addWidget(self.saveCopyPropsCB,10,0,2,6)
		saveLayoutCCDB.addWidget(self.saveCCDBBT,14,0,1,6)
		self.mainTabWidget.addTab(self.saveTabWidget,'3) Save results')
	### saveTab connectors
		self.saveTabCopyPropsCBPopulate()	
		self.saveToFolderNameTW.itemDoubleClicked.connect(self.saveTabSetTxtFolder)
		self.saveTxtBT.clicked.connect(self.saveTabSaveToFolder)
		self.saveCCDBBT.clicked.connect(self.saveTabSaveToCCDB)



		self.helpTabWidget = QtGui.QWidget(self.mainTabWidget)

		self.helpTab_mainLayout = QtGui.QHBoxLayout(self.helpTabWidget)

#		self.helpTab_frame = QtGui.QFrame(self.helpTabWidget)

#		self.helpTab_gridLayout = QtGui.QVBoxLayout(self.helpTab_frame)

#		self.helpTab_horizontalLayout = QtGui.QHBoxLayout()
#		self.helpTab_tb_url = QtGui.QLineEdit(self.helpTab_frame)
#		self.helpTab_bt_back = QtGui.QPushButton(self.helpTab_frame)
#		self.helpTab_bt_ahead = QtGui.QPushButton(self.helpTab_frame)

#		self.helpTab_bt_back.setIcon(QtGui.QIcon().fromTheme("go-previous"))
#		self.helpTab_bt_ahead.setIcon(QtGui.QIcon().fromTheme("go-next"))

#		self.helpTab_horizontalLayout.addWidget(self.helpTab_bt_back)
#		self.helpTab_horizontalLayout.addWidget(self.helpTab_bt_ahead)
#		self.helpTab_horizontalLayout.addWidget(self.helpTab_tb_url)
#		self.helpTab_gridLayout.addLayout(self.helpTab_horizontalLayout)

		self.helpTab_html = QtWebKit.QWebView()

########	self.helpTab_gridLayout.addWidget(self.helpTab_html)
	
		self.helpTab_mainLayout.addWidget(self.helpTab_html)
#		self.helpTab_mainLayout.addWidget(self.helpTab_frame)

#		self.helpTab_tb_url.returnPressed.connect(self.helpTab_browse)
#		self.helpTab_bt_back.clicked.connect(self.helpTab_html.back)
#		self.helpTab_bt_ahead.clicked.connect(self.helpTab_html.forward)

		self.helpTab_default_url = "gui/help/index.html"
#		self.helpTab_tb_url.setText(self.helpTab_default_url)
		self.helpTab_browse()

		self.mainTabWidget.addTab(self.helpTabWidget,'Help')

## helpTab Methods:
	def helpTab_browse(self):
		url = self.helpTab_default_url #self.helpTab_tb_url.text() if self.helpTab_tb_url.text() else self.helpTab_default_url
		self.helpTab_html.load(QtCore.QUrl(url))
		self.helpTab_html.show()

## viewTab Methods:
	def viewTabSetFoldView(self):
		self.viewMode='folded'

	def viewTabSetUnfoldView(self):
		self.viewMode='unfolded'

	def viewTabShowCCDBBox(self):
		self.viewTabViewTXTTW.setVisible(False)
		self.viewTabViewCCDBCBox.setVisible(True)
		self.viewTabViewCCDBvsTXT='CCDB'

	def viewTabShowTXTTW(self):
		self.viewTabViewCCDBCBox.setVisible(False)
		self.viewTabViewTXTTW.setVisible(True)
		self.viewTabViewCCDBvsTXT='TXT'

	def viewTabCCDBCBPopulate(self):
		im=self.ccdb.getEntryList()
		row=0
		for i in im:
			self.viewTabViewCCDBCBox.addItem(i)

	def viewTabViewVTKSetFile(self,item):
		filename = QtGui.QFileDialog.getOpenFileName(self, 'Open VTK file', '.')
		item.setText(filename[0])

	def viewTabViewVTKOUTSetFile(self,item):
		filename = QtGui.QFileDialog.getSaveFileName(self, 'Open VTK file', '.')
		item.setText(filename[0])


	def viewTabViewTXTSetFile(self,item):
		filename = QtGui.QFileDialog.getOpenFileName(self, 'Open imperfection file', '.')
		item.setText(filename[0])

	def viewTabSubmitVTKFile(self):
		logging.info('Submitted for rendering  VTK : '+str(self.viewTabViewVTKTW.item(0,0).text()))
		a=Array('c',str(self.viewTabViewVTKTW.item(0,0).text()))
		t = Process(target=_viewTabSubmitVTKFile, args=(a,))
		t.daemon = True
		t.start()

	def viewTabSumbitCCDBTXTFile(self):
		if self.viewTabViewCCDBvsTXT == 'TXT':
			fname=self.viewTabViewTXTTW.item(0,0).text()
			caption=fname
		if self.viewTabViewCCDBvsTXT == 'CCDB':
			key=self.viewTabViewCCDBCBox.currentText()
			e=self.ccdb.getEntry(key)
			fname=e.abspath+'/'+e.getProperty('imp_geom')
			caption=key

		logging.info('Submited for vieving: '+str(fname))
		foldMode=Array('c',str(self.viewMode))
		sf=Value('d',self.viewTabScalingDSBox.value())
		nbs=Value('i',self.viewTabViewTxtNBSizeSBox.value())
		ssp=Value('d',self.viewTabViewTxtSmSpacingDSBox.value())
		
		fileName=Array('c',str(fname))
		capt=Array('c',str(caption))
		
		t = Process(target=_viewTabSubmitCCDBTXTFile, args=(fileName,capt,foldMode,sf,nbs,ssp) )
		t.daemon = True
		t.start()

	def viewTabSumbitVTKOutFile(self):
		if self.viewTabViewCCDBvsTXT == 'TXT':
			name=self.viewTabViewTXTTW.item(0,0).text()
			key=name
		if self.viewTabViewCCDBvsTXT == 'CCDB':
			key=self.viewTabViewCCDBCBox.currentText()
			e=self.ccdb.getEntry(key)
			name=e.abspath+'/'+e.getProperty('imp_geom')
		fname=Array('c',str(name))
		outname=Array('c',str(self.viewTabSaveVTPTW.item(0,0).text()))
		caption=Array('c',str(key))
		foldMode=Array('c',str(self.viewMode))
		plot=Value('i',0)
		sf=Value('d',self.viewTabScalingDSBox.value())
		nbs=Value('i',self.viewTabViewTxtNBSizeSBox.value())
		ssp=Value('d',self.viewTabViewTxtSmSpacingDSBox.value())
			
		logging.info('Submited for saving to VTK file: '+str(name))

		t = Process(target=_viewTabSumbitVTKOutFile, args=(fname,outname,foldMode,caption,plot,sf,nbs,ssp))
		t.daemon = True
		t.start()

### inTxtTableMethods:
	def inTxtTableAddRow(self):
		row=self.inTxtTable.currentRow()
		self.inTxtTable.insertRow(row+1)
		self.inTxtTable.setItem(row+1, 0,QtGui.QTableWidgetItem())
		self.inTxtTable.setItem(row+1, 1,QtGui.QTableWidgetItem())

	def inTxtTableDeleteRow(self):
		row=self.inTxtTable.currentRow()
		self.inTxtTable.removeRow(row)
	def inTxtTableClearAll(self):
		n=self.inTxtTable.rowCount()
		for i in range(n):
			self.inTxtTable.removeRow(0)
		self.inTxtTableAddRow()
		self.initUI()
		logging.info('Txt input Table cleared')
	def inTxtTableEditCell(self,item):
		row=self.inTxtTable.currentRow()		
		col=self.inTxtTable.currentColumn()

		if col == 0:
			filenames = QtGui.QFileDialog.getOpenFileNames(self, 'Open Midsurface imperfection files', '.')
			if len(filenames[0]) == 1:
				item.setText(str(filenames[0][0]))
				logging.info("Added Midsurface imperfection :" +str(filenames[0][0]))
			if len(filenames[0]) > 1:
				item.setText(str(filenames[0][0]))
				logging.info("Added Midsurface imperfection :" +str(filenames[0][0]))
				item.setTextAlignment(QtCore.Qt.AlignRight)
				for i in range(1,len(filenames[0])):
					row+=1
					try:
						itm=self.inTxtTable.item(row,0)
						itm.text()
					except:
						self.inTxtTable.insertRow(row)
						self.inTxtTable.setItem(row, 0,QtGui.QTableWidgetItem())
						self.inTxtTable.setItem(row, 1,QtGui.QTableWidgetItem())
					self.inTxtTable.item(row,0).setText(str(filenames[0][i]))
					logging.info("Added Midsurface imperfection :" +str(filenames[0][i]))

		if col == 1:
			filenames = QtGui.QFileDialog.getOpenFileNames(self, 'Open thickness imperfection files', '.')
			if len(filenames[0]) == 1:
				item.setText(str(filenames[0][0]))
				logging.info("Added Thickness imperfection :" +str(filenames[0][0]))
			if len(filenames[0]) > 1:
				item.setText(str(filenames[0][0]))
				logging.info("Added Thickness imperfection :" +str(filenames[0][0]))
				for i in range(1,len(filenames[0])):
					row+=1
					try:
						itm=self.inTxtTable.item(row,0)
						itm.text()
					except:
						self.inTxtTable.insertRow(row)
						self.inTxtTable.setItem(row, 0,QtGui.QTableWidgetItem())
						self.inTxtTable.setItem(row, 1,QtGui.QTableWidgetItem())
					self.inTxtTable.item(row,1).setText(str(filenames[0][i]))
					logging.info("Added Thickness imperfection :" +str(filenames[0][i]))

	def submitInputTableTxt(self):
		logging.info('submitted ' + str(self.inTxtTable.rowCount())+' samples from TXT-input table to sample generator. PLEASE WAIT !')
		if self.inTxtTable.rowCount() <2:
			logging.error('Can`t submit TXT-input table with '+str(self.inTxtTable.rowCount())+' samples! At least 3 samples required!' )
		else:
			t = Thread(target=self._submitInputTableTxt, args=(self.inTxtTable,))
			lock = threading.Lock()
			t.daemon = True
			t.start()
			#lock.release()

	def _submitInputTableTxt(self,table):
		mslist=[]
		tilist=[]
		for row in range(0,table.rowCount()):
			mslist.append(str(table.item(row,0).text()))
	
			tilist.append(str(table.item(row,1).text()))
		H=self.inTxtIN_H.value()
		R=self.inTxtIN_R.value()
		A=self.inTxtIN_A.value()
		self.sg.reset()
		self.evalTabSetSampling()
		self.evalTabSetFreqRng()
		self.sg.addInputsFromTxts(H,R,A,mslist,tilist)
		#logging.info('submitted '+str(mslist))	
		logging.info('Now, you can generate new samples!')
		self.inputsOK=True	

### inCCTable methods
	
	def inCCTablePopulate(self):
		im=self.ccdb.getEntryList()
		row=0
		for i in im:
			self.inCCTable.insertRow(row)
			chkBoxItem = QtGui.QTableWidgetItem()
			chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
			chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
			self.inCCTable.setItem(row,0,QTableWidgetItem(chkBoxItem))
			self.inCCTable.item(row,0).setText(i)

	def inCCTabSelectAll(self):
		n=self.inCCTable.rowCount()
		for row in range(0,n):
			self.inCCTable.item(row,0).setCheckState(QtCore.Qt.Checked)

	def inCCTabDeselectAll(self):
		n=self.inCCTable.rowCount()
		for row in range(0,n):
			rowChecked=self.inCCTable.item(row,0).setCheckState(QtCore.Qt.Unchecked)
	def inCCTabSubmit(self):
		list2process=[]
		n=self.inCCTable.rowCount()
		for row in range(0,n):
			item=self.inCCTable.item(row,0)
			if item.checkState() == QtCore.Qt.Checked:
				list2process.append(item.text())

		logging.info('submited ' + str(len(list2process) )+' samples from CCDB to sample generator. PLEASE WAIT !')
		logging.info(str(list2process))
		t = Thread(target=self._inCCTabSubmit, args=([list2process]))
		lock = threading.Lock()
		t.daemon = True
		t.start()
			
	def _inCCTabSubmit(self,list2process):
		self.sg.reset()
		self.evalTabSetSampling()
		self.evalTabSetFreqRng()
		self.sg.addInputsFromCCDB(list2process)
		#logging.info('submitted '+str(list2process))		
		logging.info('Now, you can generate new samples!')
		self.inputsOK=True
		self.input1CC=list2process[0]		
		self.saveTabCopyPropsCBPopulate()

### evalTab methods
	def evalTabRecompute(self):
		logging.info('Recomputing')
		self.evalTabSetSampling()
		self.evalTabSetFreqRng()
		mat=self.evalTabMaterialCB.currentText()
		self.sg.applyMaterialPattern(mat)
		t = Process(target=self.sg.compute, args=() )
		t.daemon = True
		t.start()
	def evalTabSetAmplThreshold(self):
		try:
			val=float(self.evalTabSetAmplLineEdit.text())
			self.amplThreshold=val
			self.evalTabSetAmplLineEdit.setText(str(val))
		except:
			pass
		self.sg.setAmplitudeThreshold(self.amplThreshold)

	def evalTabFilterCBPopulate(self):
		fils=self.sg.getFilterList()
		for i in fils:
			self.evalTabFilterCB.addItem(i)
		if 'none' in fils:
			idx=fils.index('none')
			self.evalTabFilterCB.setCurrentIndex(idx)

	def evalTabMaterialCBPopulate(self):
		mats=self.sg.getMaterialPatternList()
		for i in mats:
			self.evalTabMaterialCB.addItem(i)

	def evalTabSetFilter(self):
		fil=self.evalTabFilterCB.currentText()
		self.sg.setFilters(fil)
		logging.info('Changing filter to '+str(fil)+' PLEASE WAIT!')
		t = Process(target=self.sg.compute, args=() )
		t.daemon = True
		t.start()

	def evalTabShowAverageIm(self):
		if self.evalTabImMidsRadButton.isChecked():
			fact=self.sg.sMidS
		if self.evalTabImThickRadButton.isChecked():
			fact=self.sg.sThick
		fact.compute()	
		x=fact.x
		y=fact.y
		data=fact.aveFunc
		(m,n)=data.shape
		ave=np.reshape(data,m*n,order='C')
		
		xx=Array('d',x)
		yy=Array('d',y)
		aveF=Array('d',ave)
		mm=Value('i',m)
		nn=Value('i',n)
		sf=Value('d',self.evalTabAvfScalingDSBox.value())
		opt_sai['foldMode']='unfolded'
		opt_sai['sqrMode']='square'
		opt_sai['xrange']=(0,2.0*np.pi)
		opt_sai['xlabel']='Radial coordinate'
		opt_sai['ylabel']='Axial coordinate'
		opt_sai['zlabel']='Imperfection'
		opt_sai['showCompass']=False
		opt_sai['showScalarBar']=False
		opt_sai['showXYPlane']=False
		opt_sai['showYZPlane']=False
		opt_sai['showZXPlane']=False

		t = Process(target=_evalTabShowArray2D, args=(xx,yy,aveF,mm,nn,sf,opt_sai) )
		t.daemon = True
		t.start()

	def evalTabShowReducedSpectrum(self):
		if self.evalTabImMidsRadButton.isChecked():
			fact=self.sg.sMidS
		if self.evalTabImThickRadButton.isChecked():
			fact=self.sg.sThick
		fact.compute()	
		y=fact.fxCut
		x=fact.fyCut
		data=fact.shCut
		(m,n)=data.shape
		ave=np.reshape(data,m*n,order='C')
		
		xx=Array('d',x)
		yy=Array('d',y)
		aveF=Array('d',ave)
		mm=Value('i',m)
		nn=Value('i',n)
		sf=Value('d',self.evalTabPowSpectrumScalingDSBox.value())
		opt_srs['foldMode']='unfolded'
		opt_srs['sqrMode']='square'
		opt_srs['xlabel']='Radial freqency'
		opt_srs['ylabel']='Axial freqency'
		opt_srs['zlabel']='Amplitude'
		opt_srs['showCompass']=False
		opt_srs['showScalarBar']=False
		opt_srs['showXYPlane']=False
		opt_srs['showYZPlane']=False
		opt_srs['showZXPlane']=False

		t = Process(target=_evalTabShowArray2D, args=(xx,yy,aveF,mm,nn,sf,opt_srs) )
		t.daemon = True
		t.start()

	def evalTabShowFilter(self):
		if self.evalTabImMidsRadButton.isChecked():
			fact=self.sg.sMidS
		if self.evalTabImThickRadButton.isChecked():
			fact=self.sg.sThick
		fact.compute()	
		x=fact.x
		y=fact.y
		data=fact.getFilter()
		(m,n)=data.shape
		ave=np.reshape(data,m*n,order='C')
		
		xx=Array('d',x)
		yy=Array('d',y)
		aveF=Array('d',ave)
		mm=Value('i',m)
		nn=Value('i',n)
		sf=Value('d',self.evalTabAvfScalingDSBox.value())
		opt_sfi['foldMode']='unfolded'
		opt_sfi['sqrMode']='square'
		opt_sfi['xlabel']='Radial coordinate'
		opt_sfi['ylabel']='Axial coordinate'
		opt_sfi['zlabel']=''
		opt_sfi['showCompass']=False
		opt_sfi['showScalarBar']=False
		opt_sfi['showXYPlane']=False
		opt_sfi['showYZPlane']=False
		opt_sfi['showZXPlane']=False

		t = Process(target=_evalTabShowArray2D, args=(xx,yy,aveF,mm,nn,sf,opt_sfi) )
		t.daemon = True
		t.start()

	def evalTabSetSampling(self):
		self.sg.setRadialSampling(self.evalTabRadSamSBox.value())
		self.sg.setAxialSampling(self.evalTabAxiSamSBox.value())
		
	def evalTabSetFreqRng(self):
		xr=(0,self.evalTabFxDSBox.value())
		yr=(0,self.evalTabFyDSBox.value())
		self.sg.setFreqRng(xr,yr)

		
### SaveTab methods
	def saveTabCopyPropsCBPopulate(self):
		im=self.ccdb.getEntryList()
		row=0
		for i in im:
			self.saveCopyPropsCB.addItem(i)
		if self.input1CC != None:
			try:
				idx=im.index(self.input1CC)
				self.saveCopyPropsCB.setCurrentIndex(idx)
			except:
				pass

	def saveTabSetTxtFolder(self,item):
		folder = QtGui.QFileDialog.getExistingDirectory(self, 'Select folder to save txt imperfection files')
		item.setText(str(folder)+'/')

		
	def saveTabSaveToFolder(self):
		if self.inputsOK == True:
			logging.info('generating new samples, PLEASE WAIT!')
			path=self.saveToFolderNameTW.item(0,0).text()
			basename=self.saveToTxtNameLineEdit.text()
			nns=self.saveNrSamplesTxtBox.value()
			self.evalTabRecompute()
			t = Thread(target=self._saveTabSaveTofolder,args=(path,basename,nns))
			lock = threading.Lock()
			t.daemon = True
			t.start()
		
		else:
			logging.error('You can`t create new samples, because input data are not processed yet!')

	def _saveTabSaveTofolder(self,fname,name,nns):
			self.sg.setScalingFactor(1.0)
			self.sg.putAutogenToFolder(fname,name,nns)
			logging.info('Sucessfully generated '+str(nns)+' samples')	

	def saveTabSaveToCCDB(self):
		if self.inputsOK == True:
			props=self.saveCopyPropsCB.currentText()
			self.sg.copyPropsFromCCDB(props)
			basename=self.saveToCCDBNameLineEdit.text()
			nns=self.saveNrSamplesCCDBBox.value()
			self.evalTabRecompute()
			t = Thread(target=self._saveTabSaveToCCDB,args=(basename,nns))
			lock = threading.Lock()
			t.daemon = True
			t.start()
		else:
			logging.error('You can`t create new samples, because input data are not processed yet!')

	

	def _saveTabSaveToCCDB(self,name,nns):
		self.sg.putAutogenToCCDB(name,nns)

def _viewTabSubmitVTKFile(fname):
	desView3D=DesicosViewer3D()
	desView3D.addVTPFile(fname.value)
	desView3D.setCaption(r'VTK file: '+str(fname.value))
	desView3D.addWidgets()
	desView3D.show()
		
def _viewTabSubmitCCDBTXTFile(fname,caption,foldMode,sf,nbs,ssp):

	desView3D=DesicosViewer3D()
	
	desView3D.setScalingFactor(sf.value)
	desView3D.setNeighborhoodSize(nbs.value)
	desView3D.setSampleSpacing(ssp.value)
	desView3D.setCaption(caption)
	desView3D.addCSVFile(fname.value,mode=foldMode.value)
	desView3D.addWidgets()
	myStream.write('Rendered: '+str(fname.value))

	desView3D.show()

def _viewTabSumbitVTKOutFile(fname,outname,foldMode,caption,plot,sf,nbs,ssp):
	desView3D=DesicosViewer3D()
	desView3D.setScalingFactor(sf.value)
	desView3D.setNeighborhoodSize(nbs.value)
	desView3D.setSampleSpacing(ssp.value)
	desView3D.addCSVFile(fname.value,mode=foldMode.value)
	desView3D.writeVTP(outname.value)
	if plot.value == 1:
		desView3D.setCaption(caption.value)
		desView3D.addWidgets()
		desView3D.show()
	#desView3D.close()


def _evalTabShowArray2D(xx,yy,ff,mm,nn,sff,opt):
	x =np.frombuffer(xx.get_obj())
	y =np.frombuffer(yy.get_obj())
	fc=np.frombuffer(ff.get_obj())
	m = mm. value
	n =nn.value
	sf=sff.value
	fm=opt['foldMode']
	sq=opt['sqrMode']
	
	f=np.reshape(fc,(m,n),order='C')

	desView3D=DesicosViewer3D()
	desView3D.setScalingFactor(sf)
	desView3D.addArray2d(x,y,f,sq)
	desView3D.addWidgets(opt)
	desView3D.show()

if __name__ == '__main__':
	freeze_support()
	manager=Manager()
	opt_srs = manager.dict()
	opt_sai = manager.dict()
	opt_sfi = manager.dict()


	app = QApplication(['DESICOS-STOCHASTIC-GEN v 0.1: Create stochastic samples for DESICOS project'])
	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
#	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("cde"))
	QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())
	frame = DesicosStGenUI()
	myStream.message.connect(frame.on_myStream_message)
	frame.show()
	logging.info('DESICOS-STOCHASTIC-GEN started')
	sys.exit(app.exec_())
