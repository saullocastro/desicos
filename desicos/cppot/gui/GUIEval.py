import csv
import os

from PyQt4 import QtGui, QtCore

import GUIHandle
import GUIPrint
from desicos.constants import TOL
from desicos import xlwt

class EvalTool(QtGui.QMainWindow):
    AXES = [('angle', 'Fiber Angle'),
            ('start', 'Starting Position'),
            ('width', 'Maximum Width'),
            ('var', 'Width Variation')]

    def __init__(self, ResultHandle, DataHandle):
        super(EvalTool, self).__init__()

        self.result_handle = ResultHandle
        self.data_handle = DataHandle

        self.graphics_type = None # 2 or 3
        self.axis_2d = [None, None, None, None]
        self.axis_3d = [None, None]
        self.result_types = 5*[False]

        self.initUI()

    def initUI(self):
        self.setGeometry(200, 200, 320, 500)
        self.setWindowTitle('Evaluation Tool')

        self.statusBar().showMessage('Ready')

        me_OpenResults = QtGui.QAction(QtGui.QIcon('icons/Load.png'), '&Load Results', self)
        me_SaveResults = QtGui.QAction(QtGui.QIcon('icons/Save.png'), '&Save Results', self)
        # me_Quit        = QtGui.QAction(QtGui.QIcon('icons/quit.png'), '&Quit Evaluation Tool', self)
        me_Export      = QtGui.QAction(QtGui.QIcon('icons/Export.png'), '&Export to Excel', self)

        # me_Quit.triggered.connect(self.closeWindow)
        me_OpenResults.triggered.connect(self.OpenResults)
        me_SaveResults.triggered.connect(self.SaveResults)
        me_Export.triggered.connect(self.ExportResults)

        # me_Quit.setStatusTip('Exit Evaluation Tool')
        me_OpenResults.setStatusTip('Load Results')
        me_SaveResults.setStatusTip('Save Current Results')
        me_Export.setStatusTip('Export Results to Excel')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(me_OpenResults)
        fileMenu.addAction(me_SaveResults)
        fileMenu.addAction(me_Export)
        # fileMenu.addAction(me_Quit)

        t_ResultType = QtGui.QLabel('Choose Results: ', self)
        t_ResultType.setGeometry(10, 30, 250, 20)

        # Result Types
        self.cb_ResultType1 = QtGui.QCheckBox('Ratio of continous Fibers', self)
        self.cb_ResultType1.setGeometry(100, 30, 250, 20)
        self.cb_ResultType2 = QtGui.QCheckBox('Ratio of effective Area (single ply piece)', self)
        self.cb_ResultType2.setGeometry(100, 50, 250, 20)
        self.cb_ResultType3 = QtGui.QCheckBox('Degree of Coverage', self)
        self.cb_ResultType3.setGeometry(100, 70, 250, 20)
        self.cb_ResultType4 = QtGui.QCheckBox('Ratio of total effective area', self)
        self.cb_ResultType4.setGeometry(100, 90, 250, 20)
        self.cb_ResultType5 = QtGui.QCheckBox('Ratio of total effectivness', self)
        self.cb_ResultType5.setGeometry(100, 110, 250, 20)

        self.cb_ResultType1.stateChanged.connect(self.changeResultType)
        self.cb_ResultType2.stateChanged.connect(self.changeResultType)
        self.cb_ResultType3.stateChanged.connect(self.changeResultType)
        self.cb_ResultType4.stateChanged.connect(self.changeResultType)
        self.cb_ResultType5.stateChanged.connect(self.changeResultType)

        # 2D or 3D Graphic

        self.pb_2D = QtGui.QPushButton('2D Graphics', self)
        self.pb_2D.setGeometry(10, 150, 150, 30)
        self.pb_2D.setStatusTip('Open 2D-Result Menu')
        self.pb_2D.clicked.connect(self.Menu2D)

        self.pb_3D = QtGui.QPushButton('3D Graphics', self)
        self.pb_3D.setGeometry(160, 150, 150, 30)
        self.pb_3D.setStatusTip('Open 3D-Result Menu')
        self.pb_3D.clicked.connect(self.Menu3D)

        # Menu for 3D-Graphics

        self.t_3DxAxis = QtGui.QLabel('Choose Variable for x-Axis', self)
        self.t_3DxAxis.move(1000,1000)

        self.t_3DyAxis = QtGui.QLabel('Choose Variable for y-Axis', self)
        self.t_3DyAxis.move(1000,1000)

        self.lm_3DxAxis = QtGui.QListWidget(self)
        self.lm_3DxAxis.setObjectName('3DxAxis')
        self.lm_3DxAxis.setGeometry(1000,1000, 150, 90)
        self.lm_3DxAxis.itemClicked.connect(self.change3DAxis)

        self.lm_3DyAxis = QtGui.QListWidget(self)
        self.lm_3DyAxis.setObjectName('3DyAxis')
        self.lm_3DyAxis.setGeometry(1000,1000, 150, 90)
        self.lm_3DyAxis.itemClicked.connect(self.change3DAxis)

        # Menu for 2D-Graphics

        # select number of Graphs
        self.pm_2DNumGraphs = QtGui.QComboBox(self)
        self.pm_2DNumGraphs.setObjectName('2DNumGraphs')
        self.pm_2DNumGraphs.move(1000,1000)

        self.t_2DxAxis1 = QtGui.QLabel('Choose x-Axis (Graph 1)', self)
        self.t_2DxAxis1.move(1000,1000)
        self.t_2DxAxis2 = QtGui.QLabel('Choose x-Axis (Graph 2)', self)
        self.t_2DxAxis2.move(1000,1000)
        self.t_2DxAxis3 = QtGui.QLabel('Choose x-Axis (Graph 3)', self)
        self.t_2DxAxis3.move(1000,1000)
        self.t_2DxAxis4 = QtGui.QLabel('Choose x-Axis (Graph 4)', self)
        self.t_2DxAxis4.move(1000,1000)

        self.lm_2DxAxis1 = QtGui.QListWidget(self)
        self.lm_2DxAxis1.setObjectName('2DxAxis1')
        self.lm_2DxAxis1.setGeometry(1000,1000, 100, 80)
        self.lm_2DxAxis1.itemClicked.connect(self.change2DAxis)

        self.lm_2DxAxis2 = QtGui.QListWidget(self)
        self.lm_2DxAxis2.setObjectName('2DxAxis2')
        self.lm_2DxAxis2.setGeometry(1000,1000, 100, 80)
        self.lm_2DxAxis2.itemClicked.connect(self.change2DAxis)

        self.lm_2DxAxis3 = QtGui.QListWidget(self)
        self.lm_2DxAxis3.setObjectName('2DxAxis3')
        self.lm_2DxAxis3.setGeometry(1000,1000, 100, 80)
        self.lm_2DxAxis3.itemClicked.connect(self.change2DAxis)

        self.lm_2DxAxis4 = QtGui.QListWidget(self)
        self.lm_2DxAxis4.setObjectName('2DxAxis4')
        self.lm_2DxAxis4.setGeometry(1000,1000, 100, 80)
        self.lm_2DxAxis4.itemClicked.connect(self.change2DAxis)

        # General Start Button

        self.pb_startGraphic = QtGui.QPushButton('Draw Graphic', self)
        self.pb_startGraphic.setGeometry(1000, 1000, 150, 30)
        self.pb_startGraphic.setStatusTip('Open new Window with results')
        self.pb_startGraphic.clicked.connect(self.startGraphic)

        self.show()

    def OpenResults(self):
        # Load results file
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Load results file',
            (os.getenv('HOME') or ''), filter='CPPOT-result files (*.cppres)')
        with open(fname, 'rb') as f:
            csv_data = csv.reader(f, delimiter=',')
            csv_data = list(csv_data)
        if not len(csv_data) > 1:
            critical = QtGui.QMessageBox.critical(self, 'Critical Error', "Cannot load, data file is empty." ,
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return

        self.result_handle.clear()
        for row in csv_data[1:]:
            self.result_handle.add(*[float(x) for x in row[1:]])
            shape = row[0]
        if shape in 'ABC':
            self.data_handle.shape = '_ABC'.index(shape)

        # Set parameters in data_handle based on the loaded values
        for attr in GUIHandle.DataHandle.ATTRIBUTES:
            values = sorted(set(getattr(r, attr) for r in self.result_handle.get()))
            param = getattr(self.data_handle, attr)
            param.min_value = values[0]
            if len(values) == 1:
                param.min_value = values[0]
                param.step = 1
                param.max_value = values[0]
                param.fix = True
            else:
                param.min_value = values[0]
                param.step = values[1] - values[0]
                num_steps = (values[-1] + TOL - values[0]) // param.step + 1
                param.max_value = values[0] + num_steps * param.step
                param.fix = False

        # reset chosen axis
        self.axis_2d = [None, None, None, None]
        self.axis_3d = [None, None]

    def SaveResults(self):
        HEADERS = ['Shape', 'Theta in Degree', 's_start in mm', 'Max. Width in mm',
            'Width Variation', 'Phi1 in Degree', 'Phi2 in Degree', 'Phi3 in Degree',
            'Phi4 in Degree', 'Number of Pieces', 'Degree of Coverage ',
            'Ratio of effective Area', 'Ratio of continous fibers',
            'Ratio of total effective area', 'Ratio of total effectiveness']
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save results file',
            (os.getenv('HOME') or ''), filter='CPPOT-result files (*.cppres)')
        with open(fname, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            shape = '_ABC'[self.data_handle.shape]
            writer.writerow(HEADERS)
            for r in self.result_handle.get():
                writer.writerow([shape] + [str(x) for x in r])

    def changeResultType(self, state):
        source = self.sender()
        enabled = (state == QtCore.Qt.Checked)

        if source.text() == 'Ratio of continous Fibers':
            self.result_types[0] = enabled
        if source.text() == 'Ratio of effective Area (single ply piece)':
            self.result_types[1] = enabled
        if source.text() == 'Degree of Coverage':
            self.result_types[2] = enabled
        if source.text() == 'Ratio of total effective area':
            self.result_types[3] = enabled
        if source.text() == 'Ratio of total effectivness':
            self.result_types[4] = enabled

    def Menu2D(self):
        # Choose Number of Graphs
        self.graphics_type = 2
        self.t_3DxAxis.move(1000,1000)
        self.t_3DyAxis.move(1000,1000)
        self.lm_3DxAxis.setGeometry(1000,1000, 150, 90)
        self.lm_3DyAxis.setGeometry(1000,1000, 150, 90)

        NumGraphs = 0

        lm_2D_axes = [self.lm_2DxAxis1, self.lm_2DxAxis2,
                      self.lm_2DxAxis3, self.lm_2DxAxis4]
        for a in lm_2D_axes:
            a.clear()

        for name, label in self.AXES:
            if not getattr(self.data_handle, name).fix:
                for a in lm_2D_axes:
                    a.addItem(label)
                NumGraphs += 1

        for i in range (0, NumGraphs):
            self.pm_2DNumGraphs.addItem(str(i))

        if NumGraphs > 0:
            self.t_2DxAxis1.setGeometry(10, 200, 150, 20)
            self.lm_2DxAxis1.setGeometry(10, 220, 140, 90)
        if NumGraphs > 1:
            self.t_2DxAxis2.setGeometry(170, 200, 150, 20)
            self.lm_2DxAxis2.setGeometry(170, 220, 140, 90)
        if NumGraphs > 2:
            self.t_2DxAxis3.setGeometry(10, 320, 150, 20)
            self.lm_2DxAxis3.setGeometry(10, 340, 140, 90)
        if NumGraphs > 3:
            self.t_2DxAxis4.setGeometry(170, 320, 150, 20)
            self.lm_2DxAxis4.setGeometry(170, 340, 140, 90)

        self.pb_startGraphic.setGeometry(170, 430, 140, 50)

    def change2DAxis(self):
        source = self.sender()

        text_map = dict((label, name) for name, label in self.AXES)
        if source.objectName() == '2DxAxis1':
            temp = self.lm_2DxAxis1.selectedItems()
            self.axis_2d[0] = text_map[str(temp[0].text())]
        elif source.objectName() == '2DxAxis2':
            temp = self.lm_2DxAxis2.selectedItems()
            self.axis_2d[1] = text_map[str(temp[0].text())]
        elif source.objectName() == '2DxAxis3':
            temp = self.lm_2DxAxis3.selectedItems()
            self.axis_2d[2] = text_map[str(temp[0].text())]
        elif source.objectName() == '2DxAxis4':
            temp = self.lm_2DxAxis4.selectedItems()
            self.axis_2d[3] = text_map[str(temp[0].text())]
        else:
            assert False

    def Menu3D(self):
        self.graphics_type = 3
        # Check that there are at least two free variables
        attrs = GUIHandle.DataHandle.ATTRIBUTES
        num_vars = len([None for attr in attrs if not getattr(self.data_handle, attr).fix])
        if num_vars <= 1:
            critical = QtGui.QMessageBox.critical(self, 'Critical Error', "It is not possible to make a 3D-Graph with only one variable. \n Please open a different Result-File or make a new Calculation." ,
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return

        # Move 2D Menu Away
        self.t_2DxAxis1.move(1000,1000)
        self.t_2DxAxis2.move(1000,1000)
        self.t_2DxAxis3.move(1000,1000)
        self.t_2DxAxis4.move(1000,1000)

        self.lm_2DxAxis1.move(1000,1000)
        self.lm_2DxAxis2.move(1000,1000)
        self.lm_2DxAxis3.move(1000,1000)
        self.lm_2DxAxis4.move(1000,1000)

        # Move 3d Menu close
        self.t_3DxAxis.setGeometry(10,200,150,20)
        self.t_3DyAxis.setGeometry(170,200, 150, 20)
        self.lm_3DxAxis.setGeometry(10, 220, 140, 90)
        self.lm_3DyAxis.setGeometry(170, 220, 140, 90)

        self.pb_startGraphic.setGeometry(170, 430, 140, 50)

        self.lm_3DxAxis.clear()
        self.lm_3DyAxis.clear()

        for name, label in self.AXES:
            if not getattr(self.data_handle, name).fix:
                self.lm_3DxAxis.addItem(label)
                self.lm_3DyAxis.addItem(label)

    def change3DAxis(self, item):
        source = self.sender()

        text_map = dict((label, name) for name, label in self.AXES)
        if source.objectName() == '3DxAxis':
            temp = self.lm_3DxAxis.selectedItems()
            self.axis_3d[0] = text_map[str(temp[0].text())]
        elif source.objectName() == '3DyAxis':
            temp = self.lm_3DyAxis.selectedItems()
            self.axis_3d[1] = text_map[str(temp[0].text())]
        else:
            assert False

    def startGraphic(self):
        if not any(self.result_types):
            critical = QtGui.QMessageBox.critical(self, 'Critical Error', "Please choose at least one result to draw" ,
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return
        if self.graphics_type == 2:
            axis_2d = [a for a in self.axis_2d if a is not None]
            if len(axis_2d) == 0:
                critical = QtGui.QMessageBox.critical(self, 'Critical Error', "Please select at least one variable" ,
                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return
            self.plot_window = GUIPrint.printResults2D(self.result_handle, self.data_handle, axis_2d, self.result_types)

        if self.graphics_type == 3:
            if None in self.axis_3d:
                critical = QtGui.QMessageBox.critical(self, 'Critical Error', "Please select a variable for both axes" ,
                    QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return
            self.plot_window = GUIPrint.printResults3D(self.result_handle, self.data_handle, self.axis_3d, self.result_types)

    def ExportResults(self):
        # Exports the Data to Excel

        style_percent = xlwt.easyxf(num_format_str='0.00%')
        style_rational = xlwt.easyxf(num_format_str='0.00')
        style_rational_grey = xlwt.easyxf('pattern: pattern solid, fore_colour gray25;',
            num_format_str='0.00')

        #QtGui.QFileDialog.getOpenFileName(self, 'Choose Directory', '*.xls')

        book = xlwt.Workbook()
        sheet1 = book.add_sheet('Input & Optima')
        sheet2 = book.add_sheet('All Results')

        # Study Parameters
        row = 0

        sheet1.write(row ,0, 'Study Parameters', xlwt.easyxf('font: bold True;'))
        row += 1
        sheet1.write(row, 1, 'MinValue')
        sheet1.write(row, 2, 'MaxValue')
        sheet1.write(row, 3, 'StepSize')
        row += 1

        sheet1.write(row, 0, 'Fiber Angle in Degree')
        sheet1.write(row+1, 0, 'Starting Position in mm')
        sheet1.write(row+2, 0, 'Maximum Width in mm')
        sheet1.write(row+3, 0, 'Width Variation')

        attrs = GUIHandle.DataHandle.ATTRIBUTES
        assert len(attrs) == 4
        for i, attr in enumerate(attrs, start=2):
            sheet1.write(i, 1, getattr(self.data_handle, attr).min_value)
            sheet1.write(i, 2, getattr(self.data_handle, attr).max_value)
            sheet1.write(i, 3, getattr(self.data_handle, attr).step)
        row += 4

        # Cone Geometry
        row += 1 # Blank line

        sheet1.write(row, 0, 'Cone Geometry', xlwt.easyxf('font: bold True;'))
        row += 1
        sheet1.write(row, 0, 'Half Cone Angle in degrees')
        sheet1.write(row, 1, self.data_handle.alphadeg)
        row += 1
        sheet1.write(row, 0, 'Free cone height in mm')
        sheet1.write(row, 1, self.data_handle.cg.H)
        row += 1
        sheet1.write(row, 0, 'Bottom radius (r3) in mm')
        sheet1.write(row, 1, self.data_handle.cg.rbot)
        row += 1
        sheet1.write(row, 0, 'Support height in mm')
        sheet1.write(row, 1, self.data_handle.cg.extra_height)
        row += 1

        sheet1.write(row, 1, '1')
        sheet1.write(row, 2, '2')
        sheet1.write(row, 3, '3')
        sheet1.write(row, 4, '4')
        row += 1

        sheet1.write(row, 0, 'Radius in mm')
        sheet1.write(row+1, 0, 'Height (z) in mm')
        sheet1.write(row+2, 0, 's in mm')

        for i in range (0, 4):
            sheet1.write(row, i+1, self.data_handle.get_r()[i])
            sheet1.write(row+1, i+1, self.data_handle.get_z()[i])
            sheet1.write(row+2, i+1, self.data_handle.get_s()[i])
        row += 3

        # All Results

        # Theta, maxW, Var, start, phi1, phi2, phi3, phi4, NumPieces, R_cov, R_cont, R_Aeff, R_SumAeff, R_total

        sheet2.write(0, 0, 'Shape', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 1, 'Fiber Angle in Degree', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 2, 'Starting Position in mm', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 3, 'Maximum Width in mm', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 4, 'Width Variation', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))

        sheet2.write(0, 5, 'Phi(T1)', xlwt.easyxf('font: bold True;'))
        sheet2.write(0, 6, 'Phi(T2)', xlwt.easyxf('font: bold True;'))
        sheet2.write(0, 7, 'Phi(T3)', xlwt.easyxf('font: bold True;'))
        sheet2.write(0, 8, 'Phi(T4)', xlwt.easyxf('font: bold True;'))

        sheet2.write(0, 9, 'Number of Pieces', xlwt.easyxf('font: bold True;'))

        sheet2.write(0, 10, 'Degree of Coverage', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 11, 'Ratio of effective area (single piece)', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 12, 'Ratio of continous Fibers', xlwt.easyxf('pattern: pattern solid, fore_colour gray25; font: bold True;'))
        sheet2.write(0, 13, 'Ratio of total effective area', xlwt.easyxf('pattern: pattern solid, fore_colour gray40; font: bold True;'))
        sheet2.write(0, 14, 'Ratio of total effectiveness', xlwt.easyxf('pattern: pattern solid, fore_colour gray40; font: bold True;'))

        shape = '_ABC'[self.data_handle.shape]

        for i, data_row in enumerate(self.result_handle.get(), start=1):
            sheet2.write(i, 0, shape, style_rational_grey)
            for j, value in enumerate(data_row):
                sheet2.write(i, j+1, value, style_rational if (4 <= j <= 8) else style_rational_grey)

        row += 1 # Blank line

        # Optimal Results

        sheet1.write(row, 0, 'Optimal Results', xlwt.easyxf('font: bold True;'))
        row += 1
        sheet1.write(row, 1, 'Fiber Angle in Degree')
        sheet1.write(row, 2, 'Starting Position in mm')
        sheet1.write(row, 3, 'Maximum Width in mm')
        sheet1.write(row, 4, 'Width Variation')

        sheet1.write(row, 5, 'Phi(T1)')
        sheet1.write(row, 6, 'Phi(T2)')
        sheet1.write(row, 7, 'Phi(T3)')
        sheet1.write(row, 8, 'Phi(T4)')

        sheet1.write(row, 9, 'Number of Pieces')

        sheet1.write(row, 10, 'Degree of Coverage')
        sheet1.write(row, 11, 'Ratio of effective area (single piece)')
        sheet1.write(row, 12, 'Ratio of continous Fibers')
        sheet1.write(row, 13, 'Ratio of total effective area')
        sheet1.write(row, 14, 'Ratio of total effectiveness')
        row += 1

        opt_columns = range(9, 14)
        sheet1.write(row, 0, 'Degree of Coverage')
        sheet1.write(row+1, 0, 'Ratio of effective Area (single piece)')
        sheet1.write(row+2, 0, 'Ratio of continous Fibers')
        sheet1.write(row+3, 0, 'Ratio of total effective area')
        sheet1.write(row+4, 0, 'Ratio of total effectiveness')

        for i, col in enumerate(opt_columns):
            max_res = max(self.result_handle.get(), key=lambda x: x[col])
            for j, value in enumerate(max_res):
                sheet1.write(row+i, j+1, value, style_percent if j in opt_columns else style_rational)

        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save to excel',
            (os.getenv('HOME') or ''), filter='Excel files (*.xls)')
        book.save(fname)
