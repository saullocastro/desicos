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


sg=ImperfFactory()
sg.addInputsFromCCDB(['degenhardt_2010_z22','degenhardt_2010_z23','degenhardt_2010_z25'])
sg.compute()
desView3D=DesicosViewer3D()
desView3D.setScalingFactor(1000.)


sg.sMidS.strFacts[0].connectOutputArray(sg.sMidS.aveFunc)

aa=sg.sMidS.strFacts[0].getPattern('tBlk','zBlk')

#plot Surface pattern
#desView3D.addArray2d(sg.sMidS.x*sg.sMidS.RB,sg.sMidS.y,aa)#,mode='square')

#plot Full Power spectrum
#desView3D.addArray2d(sg.sMidS.x*sg.sMidS.RB,sg.sMidS.y,sg.sMidS.winFilter)#,mode='square')

#plot Interpolated Power spectrum
#desView3D.addArray2d(sg.sMidS.fyIn,sg.sMidS.fxIn,sg.sMidS.shMod,mode='square')

#desView3D.addWidgets()
desView3D.show()
