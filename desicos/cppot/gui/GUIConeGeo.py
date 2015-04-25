import sys
import os
import math
import csv

from PyQt4 import QtGui, QtCore

class ConeGeo(QtGui.QMainWindow):
    # This class opens a Main Window in which the Cone Geometry can be changed
    def __init__(self, handle):
        super(ConeGeo,self).__init__()
        # Get Handle (Parameters of the study)
        self.save_to_handle = handle
        self.handle = handle.make_copy()
        # Start UI
        self.initUI()

    def initUI(self):

        #---------
        # GENERAL
        #---------

        self.setGeometry(200, 200, 770, 500)
        self.setWindowTitle('Cone Geometry Input')

        # Some basic functions for the menu bar

        me_OpenResults = QtGui.QAction(QtGui.QIcon('icons/Load.png'), '&Load Geometry', self)
        me_SaveResults = QtGui.QAction(QtGui.QIcon('icons/Save.png'), '&Save Geometry', self)

        me_OpenResults.triggered.connect(self.LoadCone)
        me_SaveResults.triggered.connect(self.SaveCone)

        me_OpenResults.setStatusTip('Load Cone Geometry')
        me_SaveResults.setStatusTip('Save Cone Geometry')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(me_OpenResults)
        fileMenu.addAction(me_SaveResults)

        self.statusBar().showMessage('Ready')

        #--------------
        # GUI Controls
        #--------------
        current_y = 30

        # Set Alpha
        t_setAlpha = QtGui.QLabel('<b>Half-cone angle in degrees</b>', self)
        t_setAlpha.move(20, current_y)
        t_setAlpha.resize(250, 20)
        current_y += 25
        self.e_setAlpha = QtGui.QLineEdit(str(self.handle.alphadeg), self)
        self.e_setAlpha.move(20, current_y)
        self.e_setAlpha.editingFinished.connect(self.changeEdit)
        self.e_setAlpha.setObjectName('alpha')
        self.e_setAlpha.resize(100, 20)
        current_y += 35

        # Set H
        t_setH = QtGui.QLabel('<b>Free cone height H in mm</b>', self)
        t_setH.move(20, current_y)
        t_setH.resize(250, 20)
        current_y += 25
        self.e_setH = QtGui.QLineEdit(str(self.handle.cg.H), self)
        self.e_setH.move(20, current_y)
        self.e_setH.editingFinished.connect(self.changeEdit)
        self.e_setH.setObjectName('H')
        self.e_setH.resize(100, 20)
        current_y += 35

        # Set Radius
        t_setRbot = QtGui.QLabel('<b>Bottom free cone radius (r3) in mm</b>', self)
        t_setRbot.move(20, current_y)
        t_setRbot.resize(250, 20)
        current_y += 25
        self.e_setRbot = QtGui.QLineEdit(str(self.handle.cg.rbot), self)
        self.e_setRbot.move(20, current_y)
        self.e_setRbot.editingFinished.connect(self.changeEdit)
        self.e_setRbot.setObjectName('Rbot')
        self.e_setRbot.resize(100, 20)
        current_y += 35

        # Set Support height
        t_setHextra = QtGui.QLabel('<b>Support height on top/bottom in mm</b>', self)
        t_setHextra.move(20, current_y)
        t_setHextra.resize(250, 20)
        current_y += 25
        self.e_setHextra = QtGui.QLineEdit(str(self.handle.cg.extra_height), self)
        self.e_setHextra.move(20, current_y)
        self.e_setHextra.editingFinished.connect(self.changeEdit)
        self.e_setHextra.setObjectName('Hextra')
        self.e_setHextra.resize(100, 20)
        current_y += 35

        #-----------------
        # Control Display
        #-----------------
        # The following GUI-Items are there to control the cone geometry

        # h is the distance between the cone vertex and the radius planes

        self.e_setS = []
        self.e_setR = []
        self.e_setZ = []
        for i in range(4):
            t_setZ = QtGui.QLabel('z%d in mm' % (i+1), self)
            t_setZ.move(20, current_y)
            e_setZ = QtGui.QLabel("%.2f" % self.handle.get_z()[i], self)
            e_setZ.move(20,current_y + 15)
            self.e_setZ.append(e_setZ)

            t_setR = QtGui.QLabel('r%d in mm' % (i+1), self)
            t_setR.move(120, current_y)
            e_setR = QtGui.QLabel("%.2f" % self.handle.get_r()[i], self)
            e_setR.move(120, current_y + 15)
            self.e_setR.append(e_setR)

            t_setS = QtGui.QLabel('s%d in mm' % (i+1), self)
            t_setS.move(220, current_y)
            e_setS = QtGui.QLabel("%.2f" % self.handle.get_s()[i], self)
            e_setS.move(220, current_y + 15)
            self.e_setS.append(e_setS)
            current_y += 35

        # Set Geometry Button
        pb_SetGeo = QtGui.QPushButton('Set Geometry \n and close Window', self)
        pb_SetGeo.clicked.connect(self.setGeo)
        pb_SetGeo.move(180, 430)
        pb_SetGeo.resize(160, 40)

        self.show()

    def closeWindow(self):
        self.close()

    def changeEdit(self):
        # This function handles the Changes in the different Line Edits and
        # saves the changes to the Data Handle.
        source = self.sender()
        source_name = str(source.objectName())
        text = source.text()
        value = text.toDouble()
        value = value[0]

        # Distinguish between the different Line Edits by their objectNames
        if source_name == "alpha":
            if (0.0 < value < 90.0):
                self.statusBar().showMessage('Ready')
                self.handle.alphadeg = value
            else:
                self.statusBar().showMessage('Half-cone angle not in valid range (0-90 degrees)')
        elif source_name == "H":
            if value > 0.0:
                self.statusBar().showMessage('Ready')
                self.handle.cg.H = value
            else:
                self.statusBar().showMessage('Free cone height must be greater than 0.0')
        elif source_name == "Rbot":
            if value > 0.0:
                self.statusBar().showMessage('Ready')
                self.handle.cg.rbot = value
            else:
                self.statusBar().showMessage('Bottom free cone radius must be greater than 0.0')
        elif source_name == "Hextra":
            if value >= 0.0:
                self.statusBar().showMessage('Ready')
                self.handle.cg.extra_height = value
            else:
                self.statusBar().showMessage('Support height must be greater than or equal to 0.0')
        else:
            assert False # Should not be reached

        # Update Window (necessary for the correct painting)
        self.updateEntry()

    def updateEntry(self):
        # Show the changes in the Control GUI's
        for e, z in zip(self.e_setZ, self.handle.get_z()):
            e.setText("%.2f" % z)
        for e, r in zip(self.e_setR, self.handle.get_r()):
            e.setText("%.2f" % r)
        for e, s in zip(self.e_setS, self.handle.get_s()):
            e.setText("%.2f" % s)

        self.e_setAlpha.setText("%.2f" % self.handle.alphadeg)
        self.e_setH.setText("%.2f" % self.handle.cg.H)
        self.e_setRbot.setText("%.2f" % self.handle.cg.rbot)
        self.e_setHextra.setText("%.2f" % self.handle.cg.extra_height)

        self.update()

    def LoadCone(self):
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Load geometry file',
            (os.getenv('HOME') or ''), filter='CPPOT-geometry files (*.cppgeom)')
        with open(fname, 'rb') as f:
            csv_data = csv.reader(f, delimiter=',')
            csv_data = list(csv_data)

        self.handle.alphadeg = float(csv_data[0][0])
        self.handle.cg.H = float(csv_data[0][1])
        self.handle.cg.rbot = float(csv_data[0][2])
        self.handle.cg.extra_height = float(csv_data[0][3])
        self.updateEntry()

    def SaveCone(self):
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save geometry file',
            (os.getenv('HOME') or ''), filter='CPPOT-geometry files (*.cppgeom)')
        with open(fname, 'wb') as f:
            writer = csv.writer(f, delimiter=',')
            row = [self.handle.alphadeg, self.handle.cg.H,
                   self.handle.cg.rbot, self.handle.cg.extra_height]
            writer.writerow([float(r) for r in row])

    def setGeo(self):
        # Gives the changed Geometry to the global Handle
        if min(self.handle.get_r()) > 0.0:
            #Check that all radii are valid
            self.save_to_handle.load_from(self.handle)
            self.close()
        else:
            self.statusBar().showMessage('Invalid cone geometry: all radii r1...r4 must be positive!')

    def paintEvent(self, event=None):
        #Basic Paint Event
        self.qp = QtGui.QPainter()
        self.qp.begin(self)
        self.draw(self.qp)
        self.qp.end()

    def draw(self, qp):
        # This function draws the cone on the right side of the GUI

        # Draw a white background retangle
        qp.setBrush(QtGui.QColor(255,255,255))
        qp.drawRect(350, 40, 400, 430)

        # Set pen options
        pen = QtGui.QPen(QtCore.Qt.black, 1)
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        qp.setPen(pen)

        # Calculate the scale parameter
        r = self.handle.get_r()
        z = self.handle.get_z()
        maxW = 2.0*max(r)
        scale = 360.0/maxW

        # Vertices of Cone
        # ----------------
        # P1, P2, P3, P4                Vertices of the Cone
        # negP1, negP2, negP3, negP4    Vertices mirrored to middle line
        # top                          Top point of cone

        x0, y0 = (550.0, 450.0 + min(z)*scale)
        length_z = max(r) / self.handle.cg.tan_alpha + min(z)
        top = (x0, y0 - length_z*scale)

        P1 = (x0 + scale*r[0], y0 - scale*z[0])
        P2 = (x0 + scale*r[1], y0 - scale*z[1])
        P3 = (x0 + scale*r[2], y0 - scale*z[2])
        P4 = (x0 + scale*r[3], y0 - scale*z[3])

        negP1 = (x0 - scale*r[0], y0 - scale*z[0])
        negP2 = (x0 - scale*r[1], y0 - scale*z[1])
        negP3 = (x0 - scale*r[2], y0 - scale*z[2])
        negP4 = (x0 - scale*r[3], y0 - scale*z[3])

        # Vertices for Polygons
        # ---------------------
        # MC: Middle Cone Part (Free cone)
        # UC: Upper Cone Part
        # LC: Lower Cone Part

        MC_P1 = QtCore.QPoint(*P2)
        MC_P2 = QtCore.QPoint(*P3)
        MC_P3 = QtCore.QPoint(*negP3)
        MC_P4 = QtCore.QPoint(*negP2)

        UC_P1 = QtCore.QPoint(*P1)
        UC_P2 = QtCore.QPoint(*P2)
        UC_P3 = QtCore.QPoint(*negP2)
        UC_P4 = QtCore.QPoint(*negP1)

        LC_P1 = QtCore.QPoint(*P3)
        LC_P2 = QtCore.QPoint(*P4)
        LC_P3 = QtCore.QPoint(*negP4)
        LC_P4 = QtCore.QPoint(*negP3)

        # Draw upper and lower cone (red)

        pen.setColor(QtGui.QColor(200,0,0))
        qp.setPen(pen)
        qp.setBrush(QtGui.QColor(255,200,200))

        qp.drawPolygon(UC_P1, UC_P2, UC_P3, UC_P4)
        qp.drawPolygon(LC_P1, LC_P2, LC_P3, LC_P4)

        # Draw Middle Cone (blue)
        pen.setColor(QtGui.QColor(0,0,200))
        qp.setPen(pen)
        qp.setBrush(QtGui.QColor(200,200,255))

        qp.drawPolygon(MC_P1, MC_P2, MC_P3, MC_P4)

        pen.setStyle(QtCore.Qt.CustomDashLine)
        pen.setDashPattern([1, 4, 6, 4])
        qp.setPen(pen)

        # Draw Middle Line
        qp.drawLine(x0, 50, x0, 470)

        pen.setStyle(QtCore.Qt.DotLine)
        qp.setPen(pen)
        pen.setWidth(1)
        qp.drawLine(top[0], top[1], P1[0], P1[1])
        qp.drawLine(top[0], top[1], negP1[0], negP1[1])

        qp.drawText(x0+20, P1[1]-5, 'r1')
        qp.drawText(x0+20, P2[1]-5, 'r2')
        qp.drawText(x0+60, P3[1]-5, 'r3')
        qp.drawText(x0+60, P4[1]-5, 'r4')

        # Coordinate System
        pen = QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        qp.drawLine(x0, y0, x0 + 40, y0)
        qp.drawLine(x0 + 35, y0 - 5, x0 + 40, y0)
        qp.drawLine(x0 + 35, y0 + 5, x0 + 40, y0)
        qp.drawText(x0 + 20, y0 + 10, 'r')

        qp.drawLine(x0, y0, x0, y0 - 40)
        qp.drawLine(x0, y0 - 40, x0 - 5, y0 - 35)
        qp.drawLine(x0, y0 - 40, x0 + 5, y0 - 35)
        qp.drawText(x0 - 10, y0 - 30, 'z')


        sina = self.handle.cg.sin_alpha
        cosa = self.handle.cg.cos_alpha
        sina45 = math.sin(self.handle.cg.alpharad + math.pi/4)
        cosa45 = math.cos(self.handle.cg.alpharad + math.pi/4)
        qp.drawLine(top[0], top[1], top[0] + sina*40, top[1] + cosa*40)
        qp.drawLine(top[0] + sina*40 - 7.1*sina45, top[1] + cosa*40 - 7.1*cosa45, top[0] + sina*40, top[1] + cosa*40)
        qp.drawLine(top[0] + sina*40 + 7.1*cosa45, top[1] + cosa*40 - 7.1*sina45, top[0] + sina*40, top[1] + cosa*40)
        qp.drawText(top[0] + sina*30, top[1] + cosa*30 - 5, 's')

        qp.drawText(x0 + 5, 0.5*(P2[1] + P3[1]), 'Free Cone')
