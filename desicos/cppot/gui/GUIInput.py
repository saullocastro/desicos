import csv
import os

from PyQt4 import QtGui, QtCore

import GUIConeGeo
import GUIHandle
import GUICalc
import GUIEval
import GUIPlot

class InputWindow(QtGui.QMainWindow):
    def __init__(self):
        super(InputWindow, self).__init__()
        self.handle = GUIHandle.DataHandle()

        self.initUI()

    def initUI(self):

        # General
        # -------
        self.setGeometry(100, 100, 830, 360)
        self.setWindowTitle('DESICOS: Optimization Tool for Cone Ply Pieces')

        self.statusBar().showMessage('Ready')

        # Menu Bar
        # --------
        # The menu bar has two different folders. In the first are some Basic actions
        # to load and save studies and close the tool. The second folder contains shortcuts
        # to the Evaluation Tool and the Plot Ply Piece Tool
        me_OpenResults = QtGui.QAction(QtGui.QIcon('icons/Load.png'), '&Load Study', self)
        me_SaveResults = QtGui.QAction(QtGui.QIcon('icons/Save.png'), '&Save Study', self)
        me_Quit        = QtGui.QAction(QtGui.QIcon('icons/quit.png'), '&Quit Tool', self)

        me_Quit.triggered.connect(QtGui.qApp.quit)
        me_OpenResults.triggered.connect(self.LoadStudy)
        me_SaveResults.triggered.connect(self.SaveStudy)

        me_Quit.setStatusTip('Exit Parametric Study Tool')
        me_OpenResults.setStatusTip('Load Parameters')
        me_SaveResults.setStatusTip('Save Parameters')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(me_OpenResults)
        fileMenu.addAction(me_SaveResults)
        fileMenu.addAction(me_Quit)

        # Actions of the second Folder: Open Evaluation Tool & Open Plot Ply Piece Tool
        me_OpenEval    = QtGui.QAction(QtGui.QIcon('icons/EvalTool.png'), '&Evaluation Tool', self)
        me_OpenPlot    = QtGui.QAction(QtGui.QIcon('icons/plotPly.png'), '&Plot Ply Piece Tool', self)
        me_OpenCone    = QtGui.QAction(QtGui.QIcon('icons/ConeGeo.png'), '&Cone Geometry Tool', self)
        me_OpenEval.triggered.connect(self.OpenEval)
        me_OpenPlot.triggered.connect(self.OpenPlot)
        me_OpenCone.triggered.connect(self.OpenConeGeo)

        fileMenu = menubar.addMenu('&Tools')
        fileMenu.addAction(me_OpenEval)
        fileMenu.addAction(me_OpenPlot)
        fileMenu.addAction(me_OpenCone)

        # GUI-Buttons
        #-------------
        # 'Set Cone Geometry'
        #  will open a new Window in which the cone Geometry can be changed
        pb_coneGeo = QtGui.QPushButton('Set Cone Geometry', self)
        pb_coneGeo.clicked.connect(self.OpenConeGeo)
        pb_coneGeo.move(20, 30)
        pb_coneGeo.resize(120, 40)
        pb_coneGeo.setStatusTip('Set Cone Geometry')

        # Start calculation
        # Starts the calculation, opens a progress bar and afterwards the Evaluation Tool
        pb_Start = QtGui.QPushButton('Start Calculation', self)
        pb_Start.clicked.connect(self.startCalc)
        pb_Start.move(380,300)
        pb_Start.resize(100,40)
        pb_Start.setStatusTip('Start Calculation')

        # Some labels for the GUI
        t_width = QtGui.QLabel('Max. Width', self)
        t_width.move(20, 100)
        t_starting = QtGui.QLabel('Starting Position', self)
        t_starting.move(20, 140)
        t_angle = QtGui.QLabel('Fiber Angle', self)
        t_angle.move(20, 180)
        t_var = QtGui.QLabel('Eccentricity', self)
        t_var.move(20, 220)

        # Fixed (CB)
        # A group of Check Boxes to fix the parameters. In this case only the min. Value
        # will be used
        t_fixed = QtGui.QLabel('Fixed', self)
        t_fixed.move(104, 70)

        self.cb_width = QtGui.QCheckBox('', self)
        self.cb_width.move(110, 100)
        self.cb_width.setObjectName('FixWidth')
        self.cb_width.stateChanged.connect(self.changeFixed)
        self.cb_width.setStatusTip('Fix Maximum Width, Only the Min. Value will be used')

        self.cb_starting = QtGui.QCheckBox('', self)
        self.cb_starting.move(110, 140)
        self.cb_starting.setObjectName('FixStart')
        self.cb_starting.stateChanged.connect(self.changeFixed)
        self.cb_starting.setStatusTip('Fix Starting Position, Only the Min. Value will be used')

        self.cb_angle = QtGui.QCheckBox('', self)
        self.cb_angle.move(110, 180)
        self.cb_angle.setObjectName('FixAngle')
        self.cb_angle.stateChanged.connect(self.changeFixed)
        self.cb_angle.setStatusTip('Fix Fiber Angle, Only the Min. Value will be used')

        self.cb_var = QtGui.QCheckBox('', self)
        self.cb_var.move(110, 220)
        self.cb_var.setObjectName('FixVar')
        self.cb_var.stateChanged.connect(self.changeFixed)
        self.cb_var.setStatusTip('Fix Width Variation, Only the Min. Value will be used')

        # MinValue (eL)
        # Some Line Edits to change the Min. Value of the Study parameters
        t_MinVal = QtGui.QLabel('Min. Value', self)
        t_MinVal.move(150, 70)

        self.e_MinWidth = QtGui.QLineEdit("%.2f" % self.handle.width.min_value, self)
        self.e_MinWidth.move(140, 100)
        self.e_MinWidth.setObjectName('MinWidth')
        self.e_MinWidth.editingFinished.connect(self.changeEdit)
        self.e_MinWidth.setStatusTip('Set Minimum Width')

        self.e_MinStart = QtGui.QLineEdit("%.2f" % self.handle.start.min_value, self)
        self.e_MinStart.move(140, 140)
        self.e_MinStart.setObjectName('MinStart')
        self.e_MinStart.editingFinished.connect(self.changeEdit)
        self.e_MinStart.setStatusTip('Set Minimum s_start Value')

        self.e_MinAngle = QtGui.QLineEdit("%.2f" % self.handle.angle.min_value, self)
        self.e_MinAngle.move(140, 180)
        self.e_MinAngle.setObjectName('MinAngle')
        self.e_MinAngle.editingFinished.connect(self.changeEdit)
        self.e_MinAngle.setStatusTip('Set Minimum Fiber Angle Value')

        self.e_MinVar = QtGui.QLineEdit("%.2f" % self.handle.var.min_value, self)
        self.e_MinVar.move(140, 220)
        self.e_MinVar.setObjectName('MinVar')
        self.e_MinVar.editingFinished.connect(self.changeEdit)
        self.e_MinVar.setStatusTip('Set Minimum Width Variation Value')

        # MaxValue (eL)
        # Some Line Edits to change the Max. Value of the Study parameters
        t_MaxVal = QtGui.QLabel('Max. Value', self)
        t_MaxVal.move(260, 70)

        self.e_MaxWidth = QtGui.QLineEdit("%.2f" % self.handle.width.max_value, self)
        self.e_MaxWidth.move(260, 100)
        self.e_MaxWidth.setObjectName('MaxWidth')
        self.e_MaxWidth.editingFinished.connect(self.changeEdit)
        self.e_MaxWidth.setStatusTip('Set Maximum Width')

        self.e_MaxStart = QtGui.QLineEdit("%.2f" % self.handle.start.max_value, self)
        self.e_MaxStart.move(260, 140)
        self.e_MaxStart.setObjectName('MaxStart')
        self.e_MaxStart.editingFinished.connect(self.changeEdit)
        self.e_MaxStart.setStatusTip('Set Maximum s_start Value')

        self.e_MaxAngle = QtGui.QLineEdit("%.2f" % self.handle.angle.max_value, self)
        self.e_MaxAngle.move(260, 180)
        self.e_MaxAngle.setObjectName('MaxAngle')
        self.e_MaxAngle.editingFinished.connect(self.changeEdit)
        self.e_MaxAngle.setStatusTip('Set Maximum Fiber Angle Value')

        self.e_MaxVar = QtGui.QLineEdit("%.2f" % self.handle.var.max_value, self)
        self.e_MaxVar.move(260, 220)
        self.e_MaxVar.setObjectName('MaxVar')
        self.e_MaxVar.editingFinished.connect(self.changeEdit)
        self.e_MaxVar.setStatusTip('Set Maximum Width Variation Value')

        # StepWidth (eL)
        # Some Line Edits to change the Step Width of the Study parameters
        t_StepVal = QtGui.QLabel('Step Size:', self)
        t_StepVal.move(380, 70)

        self.e_StepWidth = QtGui.QLineEdit("%.2f" % self.handle.width.step, self)
        self.e_StepWidth.move(380, 100)
        self.e_StepWidth.setObjectName('StepWidth')
        self.e_StepWidth.editingFinished.connect(self.changeEdit)
        self.e_StepWidth.setStatusTip('Set number of Steps for the Variation of the Maximum Width')

        self.e_StepStart = QtGui.QLineEdit("%.2f" % self.handle.start.step, self)
        self.e_StepStart.move(380, 140)
        self.e_StepStart.setObjectName('StepStart')
        self.e_StepStart.editingFinished.connect(self.changeEdit)
        self.e_StepStart.setStatusTip('Set number of Steps for the Variation of the Starting Position')

        self.e_StepAngle = QtGui.QLineEdit("%.2f" % self.handle.angle.step, self)
        self.e_StepAngle.move(380, 180)
        self.e_StepAngle.setObjectName('StepAngle')
        self.e_StepAngle.editingFinished.connect(self.changeEdit)
        self.e_StepAngle.setStatusTip('Set number of Steps for the Variation of the Fiber Angle')

        self.e_StepVar = QtGui.QLineEdit("%.2f" % self.handle.var.step, self)
        self.e_StepVar.move(380, 220)
        self.e_StepVar.setObjectName('StepVar')
        self.e_StepVar.editingFinished.connect(self.changeEdit)
        self.e_StepVar.setStatusTip('Set number of Steps for the Variation of the Width Variation')

        # Set Shape
        # Three Radio Buttons are used to set the Shape of the studied ply pieces
        t_StepVal = QtGui.QLabel('Choose Shape: ', self)
        t_StepVal.move(20, 260)

        self.pb_ShapeTrapez = QtGui.QRadioButton('A', self)
        self.pb_ShapeTrapez.move(145, 260)
        self.pb_ShapeTrapez.setObjectName('ShapeTrapez')
        self.pb_ShapeTrapez.clicked.connect(self.changeShape)
        self.pb_ShapeTrapez.toggle()
        self.pb_ShapeTrapez.setStatusTip('Trapezoidal shape without overlaps')

        self.pb_ShapeTrapez2 = QtGui.QRadioButton('B', self)
        self.pb_ShapeTrapez2.move(265, 260)
        self.pb_ShapeTrapez2.setObjectName('ShapeTrapez2')
        self.pb_ShapeTrapez2.clicked.connect(self.changeShape)
        self.pb_ShapeTrapez2.setStatusTip('Trapezoidal shape with one overlap')

        self.pb_ShapeRect = QtGui.QRadioButton('C', self)
        self.pb_ShapeRect.move(385, 260)
        self.pb_ShapeRect.setObjectName('ShapeRect')
        self.pb_ShapeRect.clicked.connect(self.changeShape)
        self.pb_ShapeRect.setStatusTip('Rectangular shape with many overlaps')

        self.show()

    def OpenEval(self):
        # Starts the Evaluation Tool with an empty Result Handle
        results = GUIHandle.ResultHandle()
        # Store window so it doesn't get garbage-collected
        self.eval_window = GUIEval.EvalTool(results, self.handle)

    def OpenPlot(self):
        # Opens the Plot Ply Piece Tool
        # Store window so it doesn't get garbage-collected
        self.plot_window = GUIPlot.PlotTool(self.handle)

    def OpenConeGeo(self):
        # Opens the Cone Geometry App
        # Store window so it doesn't get garbage-collected
        self.cg_window = GUIConeGeo.ConeGeo(self.handle)

    def updateEntry(self):
        # updates the entries of all line edits
        # used when saved study parameters are loaded
        self.e_MinWidth.setText("%.2f" % self.handle.width.min_value)
        self.e_MinStart.setText("%.2f" % self.handle.start.min_value)
        self.e_MinAngle.setText("%.2f" % self.handle.angle.min_value)
        self.e_MinVar.setText("%.2f" % self.handle.var.min_value)

        self.e_MaxWidth.setText("%.2f" % self.handle.width.max_value)
        self.e_MaxStart.setText("%.2f" % self.handle.start.max_value)
        self.e_MaxAngle.setText("%.2f" % self.handle.angle.max_value)
        self.e_MaxVar.setText("%.2f" % self.handle.var.max_value)

        self.e_StepWidth.setText("%.2f" % self.handle.width.step)
        self.e_StepStart.setText("%.2f" % self.handle.start.step)
        self.e_StepAngle.setText("%.2f" % self.handle.angle.step)
        self.e_StepVar.setText("%.2f" % self.handle.var.step)

        if self.handle.shape == 1:
            self.pb_ShapeTrapez.setChecked(True)
        elif self.handle.shape == 2:
            self.pb_ShapeTrapez2.setChecked(True)
        elif self.handle.shape == 3:
            self.pb_ShapeTrapez.setChecked(True)
        else:
            assert False, 'Invalid shape value'

        self.cb_width.setChecked(self.handle.width.fix)
        self.cb_starting.setChecked(self.handle.start.fix)
        self.cb_angle.setChecked(self.handle.angle.fix)
        self.cb_var.setChecked(self.handle.var.fix)

    def LoadStudy(self):
        # Loads saved study parameters
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Load study file',
            (os.getenv('HOME') or ''), filter='CPPOT files (*.cppot)')
        with open(fname, 'rb') as f:
            csv_data = csv.reader(f, delimiter=',')
            csv_data = list(csv_data)
        self.handle.load_from_table(csv_data)

        self.updateEntry()

    def SaveStudy(self):
        # Saves study parameters
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save study file',
            (os.getenv('HOME') or ''), filter='CPPOT files (*.cppot)')
        with open(fname, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            for row in self.handle.get_as_table():
                writer.writerow(row)

    def changeFixed(self, state):
        # This function is called when the Fix is changed (Check Boxes)
        # To distinguish between the different check boxes are different
        # ObjectNames used.
        #
        # Saves the change to the Handle

        source = self.sender()
        source_name = str(source.objectName())
        object_map = {
            "FixWidth" : 'width',
            "FixStart" : 'start',
            "FixAngle" : 'angle',
            "FixVar" : 'var',
        }
        param_name = object_map[source_name]
        getattr(self.handle, param_name).fix = (state == QtCore.Qt.Checked)

    def changeEdit(self):
        # This function is called whenever one of the values in the Line Edits
        # is changed. The changes are saved to the handle.
        source = self.sender()
        source_name = str(source.objectName())
        text = source.text()
        value = text.toDouble()
        value = value[0]

        object_map = {
            "MinWidth" : ('width', 'min_value'),
            "MaxWidth" : ('width', 'max_value'),
            "StepWidth" : ('width', 'step'),
            "MinStart" : ('start', 'min_value'),
            "MaxStart" : ('start', 'max_value'),
            "StepStart" : ('start', 'step'),
            "MinAngle" : ('angle', 'min_value'),
            "MaxAngle" : ('angle', 'max_value'),
            "StepAngle" : ('angle', 'step'),
            "MinVar" : ('var', 'min_value'),
            "MaxVar" : ('var', 'max_value'),
            "StepVar" : ('var', 'step'),
        }
        param_name, attr = object_map[source_name]
        param = getattr(self.handle, param_name)
        widget = getattr(self, 'e_' + source_name)

        if (attr == 'min_value' and value >= param.max_value) or \
           (attr == 'max_value' and value <= param.min_value) or \
           (attr == 'step' and value <= 0):
            self.WrongEntry(param_name, attr)
            widget.setText("%.2f" % getattr(param, attr))
        else:
            setattr(param, attr, value)
            widget.setText("%.2f" % value)
            self.statusBar().showMessage('Ready')

    def WrongEntry (self, param_name, attr):
        # Whenever an Entry is wrong a Message is shown in the status bar

        if param_name == 'width':
            name = 'Maximum Width, \n'
        elif param_name == 'start':
            name = 'Starting Position, \n'
        elif param_name == 'angle':
            name = 'Fiber Angle, \n'
        elif param_name == 'var':
            name = 'Width Variation, \n'
        else:
            assert False # Should not be reached

        if attr == 'min_value':
            msg = 'Minimum should be lower than Maximum'
        elif attr == 'max_value':
            msg = 'Maximum should be higher than Minimum'
        elif attr == 'step':
            msg = 'Number of Steps should be positive'
        else:
            assert False # Should not be reached

        msg = 'Wrong Entry: \n' + name + msg

        warn = QtGui.QMessageBox.warning(self, 'Warning', msg,
            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        if warn == QtGui.QMessageBox.Ok:
            return 1

    def changeShape(self, state):
        # This function is called when the shape is changed (Radio Buttons)
        # Saves the change to the Handle
        source = self.sender()

        if source.objectName() == "ShapeTrapez":
            self.handle.shape = 1
        elif source.objectName() == "ShapeTrapez2":
            self.handle.shape = 2
        elif source.objectName() == "ShapeRect":
            self.handle.shape = 3
        else:
            assert False # Should not be reached

    def startCalc(self):
        # Calculate the total number of variations
        num_calc = self.handle.num_calc()

        # Show Warning Message if the Number of Variations is higher than 10000
        if num_calc > 10000:
            proceed = self.NumWarning(num_calc)
            if not proceed:
                return
        variations = GUICalc.Variation(self, self.handle)
        for progress in variations.calc():
            QtGui.QApplication.processEvents()
        self.StartEval(variations.result_handle)

    def NumWarning(self, num_calc):
        # Opens a Message Box if the Number of Variations is larger than 10000
        # It is possible to choose if the calculation should be started or not

        result = QtGui.QMessageBox.warning(self, 'Warning', "The Number of calculations is very high (%d variations). Do you want to continue?" % num_calc,
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        return result == QtGui.QMessageBox.Yes

    def StartEval(self, result_handle):
        # Starts the Evaluation Tool, is called by GUICalc.Variation after the calculation is finished.
        # This detour is necessary to open the Evaluation Tool permenantly
        self.eval_window = GUIEval.EvalTool(result_handle, self.handle)
