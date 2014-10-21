#!/usr/bin/env python
from multiprocessing import Process
import io
import sys
import PySide
import time
import sys
import os
#from PySide.QtCore import QRect, QMetaObject, QObject
#from PySide.QtGui  import (QApplication, QMainWindow, QWidget, 
#			QGridLayout, QTabWidget, QPlainTextEdit,
#			QMenuBar, QMenu, QStatusBar, QAction, 
#			QIcon, QFileDialog, QMessageBox, QFont)

from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import *

from PySide.QtGui  import *

sys.path.append( '../stochastic/')

msgStream=io.TextIOBase()

from stochastic.imperfGen import *
class MiniLogger(object):
	def info(self,message):
		msgStream.write(time.strftime("%a %H:%M:%S:  ",time.localtime())+str(message)+'\n')
	def error(self,message):
		msgStream.write(time.strftime("%a %H:%M:%S: ERROR: ",time.localtime())+str(message)+'\n')
#
#class EmittingStream(QtCore.QObject):
#
#	textWritten = QtCore.pyqtSignal(str)
#
#	def write(self, text):
#		self.textWritten.emit(str(text))
#
class MyStream(QtCore.QObject):
	message = QtCore.Signal(str)
	def __init__(self, parent=None):
		super(MyStream, self).__init__(parent)

	def write(self, message):
		self.message.emit(str(message))

class DesicosStGenUI(QMainWindow):
	def __init__(self, parent=None):
		super(DesicosStGenUI, self).__init__(parent)
		self.initUI()
		self.sg=ImperfFactory()
		self.log=MiniLogger()
#		sys.stderr = EmittingStream(textWritten=self.normalOutputWritten)
#		sys.stdout = EmittingStream(textWritten=self.normalOutputWritten)

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
		self.resize(800, 600)
		mainWidget=QtGui.QWidget(self)
		self.setCentralWidget(mainWidget)
		vLayout=QtGui.QVBoxLayout(mainWidget)
		
		self.mainTabWidget = QTabWidget(mainWidget)
		vLayout.addWidget(self.mainTabWidget)

		self.tabInputs = QWidget()
		inpLayout=QVBoxLayout(self.tabInputs)

		inputTab=QTabWidget(self.mainTabWidget)
		inputTab.setTabPosition(QTabWidget.West)
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
		header = self.inTxtTable.horizontalHeader()
		header.setResizeMode(QHeaderView.Stretch)
		header.setTextElideMode(QtCore.Qt.ElideLeft)	

		self.inTxtTable.setColumnCount(2)
		self.inTxtTable.setRowCount(1)
		self.inTxtTable.setColumnWidth(0,  160)
		self.inTxtTable.setColumnWidth(1,  160)
		self.inTxtTable.setHorizontalHeaderLabels(["Mid surface imperfections:","Thickness imperfections:" ])
		self.inTxtTable.setItem(0, 0,QtGui.QTableWidgetItem())
		self.inTxtTable.setItem(0, 1,QtGui.QTableWidgetItem())

		self.inTxtTableSubmitBT=QtGui.QPushButton("Submit for processing",inTxtTab)
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
		inTxtLayoutV2.addWidget(self.inTxtTableSubmitBT,8,0)
		inTxtLayoutV2.addWidget(self.inTxtTableReset)
	###.inTxtTab connectors:
		inTxtTableAddRowBT.clicked.connect(self.inTxtTableAddRow)
		self.inTxtTableDelRowBT.clicked.connect(self.inTxtTableDeleteRow)
		self.inTxtTable.itemDoubleClicked.connect(self.inTxtTableEditCell)
		self.inTxtTableReset.clicked.connect(self.inTxtTableClearAll)
		self.inTxtTableSubmitBT.clicked.connect(self.inTxtTableSubmit)
		inputTab.addTab(inTxtTab,'From txt files')

##### input from ccDB	
		inCCTab = QWidget()
		inCCLayoutV=QVBoxLayout(inCCTab)
		inCCLayoutHw=QWidget()
		inCCLayoutH=QHBoxLayout(inCCLayoutHw)
		inCCLayoutV2w=QWidget()
		inCCLayoutV2=QVBoxLayout(inCCLayoutV2w)

		inCCLabel=QtGui.QLabel(u"Select inputs from DESICOS conecyl DB",inCCTab)

		self.inCCTable = QtGui.QTableWidget(inCCTab)
		self.inCCTable.setColumnCount(2)
		self.inCCTable.setRowCount(1)
		self.inCCTable.setHorizontalHeaderLabels(["Input name:", "Used"])
	
		self.submitCcdbTableBT=QtGui.QPushButton("Submit for processing",inCCTab)
		self.resetCcdbTableBT=QtGui.QPushButton("Clear selection",inCCTab)

		inCCLayoutV.addWidget(inCCLabel)
		inCCLayoutV.addWidget(inCCLayoutHw)
		inCCLayoutH.addWidget(self.inCCTable)
		inCCLayoutH.addWidget(inCCLayoutV2w)
		inCCLayoutV2.addWidget(self.submitCcdbTableBT)
		inCCLayoutV2.addWidget(self.resetCcdbTableBT)
		inputTab.addTab(inCCTab,'From conecyl DB')
	
#		self.msgDISP=QtGui.QTextEdit(inCCTab)#Label(u"",inCCTab)
#		self.msgDISP=QtGui.QTextEdit()
		self.msgDISP=QtGui.QTextBrowser()
		vLayout.addWidget(self.msgDISP)
		self.mainTabWidget.addTab(inputTab,'1) Select inputs')

###Evaluate Tab
		self.evalTabWidget = QWidget()
		self.evalLayout = QVBoxLayout(self.evalTabWidget)
		evalLabel=QtGui.QLabel(u"Evaluate tab",self.evalTabWidget)
		self.evalLayout.addWidget(evalLabel)
		self.evalLayout.addWidget(evalLabel)

		self.mainTabWidget.addTab(self.evalTabWidget,'2) Process inputs')
	
		self.saveTabWidget = QWidget()
		self.saveLayout = QVBoxLayout(self.saveTabWidget)
		saveLabel=QtGui.QLabel(u"Save your results",self.saveTabWidget)
		self.saveLayout.addWidget(saveLabel)
		self.saveLayout.addWidget(saveLabel)

		self.mainTabWidget.addTab(self.saveTabWidget,'3) Save results')

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
		self.log.info('Txt input Table cleared')
	def inTxtTableEditCell(self,item):
		row=self.inTxtTable.currentRow()		
		col=self.inTxtTable.currentColumn()

		if col == 0:
			filenames = QtGui.QFileDialog.getOpenFileNames(self, 'Open Midsurface imperfection files', '.')
			if len(filenames[0]) == 1:
				item.setText(str(filenames[0][0]))
				self.log.info("Added Midsurface imperfection :" +str(filenames[0][0]))
			if len(filenames[0]) > 1:
				item.setText(str(filenames[0][0]))
				self.log.info("Added Midsurface imperfection :" +str(filenames[0][0]))
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
					self.log.info("Added Midsurface imperfection :" +str(filenames[0][i]))

		if col == 1:
			filenames = QtGui.QFileDialog.getOpenFileNames(self, 'Open thickness imperfection files', '.')
			if len(filenames[0]) == 1:
				item.setText(str(filenames[0][0]))
				self.log.info("Added Thickness imperfection :" +str(filenames[0][0]))
			if len(filenames[0]) > 1:
				item.setText(str(filenames[0][0]))
				self.log.info("Added Thickness imperfection :" +str(filenames[0][0]))
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
					self.log.info("Added Thickness imperfection :" +str(filenames[0][i]))

	def inTxtTableSubmit(self):
		self.log.info('submitting ' + str(self.inTxtTable.rowCount())+' samples from TXT-input table to sample generator. PLEASE WAIT !')
		print " files submitted"
		if self.inTxtTable.rowCount() <2:
			self.log.error('Can`t submit TXT-input table with '+str(self.inTxtTable.rowCount())+' samples! At least 3 samples required!' )
		else:
			time.sleep(5)
		#	self.submitInputTable(self.inTxtTable)
	def submitInputTable(self,table):
		self.log.info('submitting ' + str(self.inTxtTable.rowCount())+' samples from TXT-input table to sample generator. PLEASE WAIT !')
		mslist=[]
		tilist=[]
		for row in range(0,table.rowCount()):
			mslist.append(str(table.item(row,0).text()))
	
			tilist.append(str(table.item(row,1).text()))
		p1=Process(target=self.sg.addInputsFromTxts,args=(100.0,100.0,0.0,mslist,tilist))
		p1.start()
		p1.join()
		self.log.info('submitted '+str(mslist))	
		
		#	self.sg.putAutogenToFolder('results/','sample',2)

if __name__ == '__main__':
	app = QApplication(['DESICOS-STOCHASTIC-GEN v 0.1: Create stochastic samples for DESICOS project'])
#	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("plastique"))
	QtGui.QApplication.setStyle(QtGui.QStyleFactory.create("cde"))
	QtGui.QApplication.setPalette(QtGui.QApplication.style().standardPalette())
	frame = DesicosStGenUI()
	frame.show()
	myStream = MyStream()
	myStream.message.connect(frame.on_myStream_message)
	msgStream=myStream
	frame.log.info('DESICOS-STOCHASTIC-GEN started')
	sys.exit(app.exec_())
