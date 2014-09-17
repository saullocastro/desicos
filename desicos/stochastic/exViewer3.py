#!/usr/bin/env python
from multiprocessing import Process
from multiprocessing import Process, Value, Array

from threading import Thread
import threading
import thread
import io
import sys
import PySide
import time
import sys
import os
#from PySide.QtCore import QRect, QMetaObject, QObject
#from PySide.QtGui  import (QApplication, QMainWindow, QWidget, 
#                       QGridLayout, QTabWidget, QPlainTextEdit,
#                       QMenuBar, QMenu, QStatusBar, QAction, 
#                       QIcon, QFileDialog, QMessageBox, QFont)

from PySide import QtGui
from PySide import QtCore
from PySide.QtCore import *

from PySide.QtGui  import *

sys.path.append( '../stochastic/')
sys.path.append( '../abaqus-conecyl-python_DEV/')

from conecylDB import imps, R_measured, H_measured, t_measured
from measured_imp_ms import read_file
from stochastic.imperfGen import *
from viewer import DesicosViewer3D
from stochastic.strFact import StructurePattern

sg=ImperfFactory()
#sg.addInputsFromCCDB(['degenhardt_2010_z22','degenhardt_2010_z23','degenhardt_2010_z25'])
#sg.compute()
desView3D=DesicosViewer3D()
desView3D.setScalingFactor(200.)

#sg.sMidS.strFacts[0].connectOutputArray(sg.sMidS.aveFunc)
x=np.linspace(0,500,500)
y=np.linspace(0,200,200)

arr=np.zeros((200,500))
strFact1=StructurePattern()
strFact1.AZ=0.2
strFact1.AT=0.2
strFact1.nBlkT=200
strFact1.nBlkZ=110
strFact1.setGeometry(250,250,0)
strFact1.connectOutputArray(arr)
aa1=strFact1.getPattern('tBlk','zBlk',mode='grt')


strFact2=StructurePattern()
strFact2.setGeometry(250,250,0)
strFact2.connectOutputArray(arr)
strFact2.AZ=0.7
strFact2.AT=1.0
strFact2.KT=np.deg2rad(70.)
strFact2.KZ=np.deg2rad(85.)
strFact2.nBlkT=40
strFact2.nBlkZ=20
aa2=strFact2.getPattern('tBlk','zBlk',mode='grt')

strFact3=StructurePattern()
strFact3.setGeometry(250,250,0)
strFact3.connectOutputArray(arr)
strFact3.AZ=0.0
strFact3.AT=0.3
strFact3.KT=np.deg2rad(-65.)
strFact3.KZ=np.deg2rad(85.)
strFact3.nBlkT=15
strFact3.nBlkZ=20
aa3=strFact3.getPattern('tBlk','zBlk',mode='grt')

aa=aa1+aa2+aa3
#aa=aa2
#plot Surface pattern
desView3D.addArray2d(x,y,aa)#,mode='square')

#plot Full Power spectrum
#desView3D.addArray2d(sg.sMidS.x*sg.sMidS.RB,sg.sMidS.y,sg.sMidS.winFilter)#,mode='square')

#plot Interpolated Power spectrum
#desView3D.addArray2d(sg.sMidS.fyIn,sg.sMidS.fxIn,sg.sMidS.shMod,mode='square')

#desView3D.addWidgets()
desView3D.show()
