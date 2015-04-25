import math

from PyQt4 import QtGui, QtCore
import numpy as np

from matplotlib.figure import Figure
# import the Qt4Agg FigureCanvas object, that binds Figure to
# Qt4Agg backend. It also inherits from QWidget
from matplotlib.backends.backend_qt4agg \
import FigureCanvasQTAgg as FigureCanvas
# import the NavigationToolbar Qt4Agg widget
from matplotlib.backends.backend_qt4agg \
import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.path import Path
from matplotlib.patches import PathPatch

from desicos.cppot.core.ply_model import TrapezPlyPieceModel, \
    Trapez2PlyPieceModel, RectPlyPieceModel
from desicos.cppot.core.geom import Point2D, Line2D
import GUIConeGeo
import GUIHandle


class Qt4MplCanvas(FigureCanvas):
    """Class to represent the FigureCanvas widget"""
    def __init__(self, parent):
        # plot definition
        self.fig = Figure()
        # initialization of the canvas
        FigureCanvas.__init__(self, self.fig)
        # set the parent widget
        self.setParent(parent)
        # we define the widget as expandable
        FigureCanvas.setSizePolicy(self,
        QtGui.QSizePolicy.Expanding,
        QtGui.QSizePolicy.Expanding)
        # notify the system of updated policy
        FigureCanvas.updateGeometry(self)


class PlotWindow(QtGui.QMainWindow):
    def __init__(self):
        # initialization of Qt MainWindow widget
        QtGui.QMainWindow.__init__(self)
        # set window title
        self.setWindowTitle("Plot Window")
        # instantiate a widget, it will be the main one
        self.main_widget = QtGui.QWidget(self)
        # create a vertical box layout widget
        vbl = QtGui.QVBoxLayout(self.main_widget)
        # instantiate our Matplotlib canvas widget
        self.qmc = Qt4MplCanvas(self.main_widget)
        # instantiate the navigation toolbar
        ntb = NavigationToolbar(self.qmc, self.main_widget)
        # pack these widget into the vertical box
        vbl.addWidget(self.qmc)
        vbl.addWidget(ntb)
        # set the focus on the main widget
        self.main_widget.setFocus()
        # set the central widget of MainWindow to main_widget
        self.setCentralWidget(self.main_widget)


class PlotTool(QtGui.QMainWindow):
    # Tool for plotting the ply pieces on the unwounded surface of the cone

    def __init__(self, data_handle):
        super(PlotTool, self).__init__()
        # Used only for the geometry here
        self.data_handle = data_handle

        self.width = data_handle.width.min_value
        self.start = data_handle.start.min_value
        self.angle = data_handle.angle.min_value
        self.var = data_handle.var.min_value

        self.shape = data_handle.shape
        self.type = 1
        self.ResS = 40
        self.ResPhi = 100
        self.show_pieces = True
        self.show_explanations = False

        self.initUI()

    def initUI(self):
        self.setGeometry(200, 200, 270, 580)
        self.setWindowTitle('Plot Ply Pieces Tool')

        me_Quit = QtGui.QAction(QtGui.QIcon('icons/quit.png'), '&Quit', self)
        me_Quit.triggered.connect(self.closeWindow)
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(me_Quit)

        # Set Cone Geometry

        pb_coneGeo = QtGui.QPushButton('Set Cone Geometry', self)
        pb_coneGeo.clicked.connect(self.openConeGeo)
        pb_coneGeo.setGeometry(20, 30, 120, 40)
        pb_coneGeo.setStatusTip('Set Cone Geometry')

        Type_group = QtGui.QButtonGroup(self)

        # Select Plot Type

        t_Type = QtGui.QLabel('Choose Plot Type:', self)
        t_Type.setGeometry(20, 80, 150, 20)

        self.rb_TypeGep = QtGui.QRadioButton('Geometry',self)
        self.rb_TypeGep.move(20, 95)
        self.rb_TypeGep.setObjectName('TypeGeo')
        self.rb_TypeGep.clicked.connect(self.changeType)
        self.rb_TypeGep.setStatusTip('Line Plot of the Geometry')
        self.rb_TypeGep.toggle()

        self.rb_TypeAngle = QtGui.QRadioButton('Local Fiber Angle',self)
        self.rb_TypeAngle.move(20, 115)
        self.rb_TypeAngle.setObjectName('TypeAngle')
        self.rb_TypeAngle.clicked.connect(self.changeType)
        self.rb_TypeAngle.setStatusTip('Color Plot of the local fiber angle')

        self.rb_TypeThick = QtGui.QRadioButton('Local Thickness',self)
        self.rb_TypeThick.move(20, 135)
        self.rb_TypeThick.setObjectName('TypeThick')
        self.rb_TypeThick.clicked.connect(self.changeType)
        self.rb_TypeThick.setStatusTip('Color Plot of the local thickness')

        Type_group.addButton(self.rb_TypeGep)
        Type_group.addButton(self.rb_TypeAngle)
        Type_group.addButton(self.rb_TypeThick)

        # Additonal Options for color plots

        self.cb_ShowPieces = QtGui.QCheckBox('Show ply pieces', self)
        self.cb_ShowPieces.move(1000, 1000)
        self.cb_ShowPieces.setObjectName('ShowPieces')
        self.cb_ShowPieces.stateChanged.connect(self.changeShowPiece)
        self.cb_ShowPieces.toggle()

        self.t_ResPhi = QtGui.QLabel('Set Number of Points on circumference:', self)
        self.t_ResPhi.setGeometry(1000, 1000, 200, 20)
        self.e_ResPhi = QtGui.QLineEdit('%.0f' % self.ResPhi, self)
        self.e_ResPhi.setGeometry(1000, 1000, 50, 20)
        self.e_ResPhi.setObjectName('ResPhi')
        self.e_ResPhi.editingFinished.connect(self.changeValue)


        self.t_ResS = QtGui.QLabel('Set Number of Points in s-Direction:', self)
        self.t_ResS.setGeometry(1000, 1000, 200, 20)
        self.e_ResS = QtGui.QLineEdit('%.0f' % self.ResS, self)
        self.e_ResS.setGeometry(1000, 1000, 50, 20)
        self.e_ResS.setObjectName('ResS')
        self.e_ResS.editingFinished.connect(self.changeValue)

        # Select Type:

        Shape_group = QtGui.QButtonGroup(self)
        t_Type = QtGui.QLabel('Choose Geometry Type:', self)
        t_Type.setGeometry(20, 160, 160, 20)

        self.rb_ShapeTrapez = QtGui.QRadioButton('A', self)
        self.rb_ShapeTrapez.move(20, 180)
        self.rb_ShapeTrapez.setObjectName('ShapeTrapez')
        self.rb_ShapeTrapez.clicked.connect(self.changeShape)
        self.rb_ShapeTrapez.toggle()
        self.rb_ShapeTrapez.setStatusTip('Trapezoidal Shape without Overlaps')

        self.rb_ShapeTrapez2 = QtGui.QRadioButton('B', self)
        self.rb_ShapeTrapez2.move(100, 180)
        self.rb_ShapeTrapez2.setObjectName('ShapeTrapez2')
        self.rb_ShapeTrapez2.clicked.connect(self.changeShape)
        self.rb_ShapeTrapez2.setStatusTip('Trapezoidal Shape with one Overlap')

        self.rb_ShapeRect = QtGui.QRadioButton('C', self)
        self.rb_ShapeRect.move(180, 180)
        self.rb_ShapeRect.setObjectName('ShapeRect')
        self.rb_ShapeRect.clicked.connect(self.changeShape)
        self.rb_ShapeRect.setStatusTip('Rectangular Shape with many Overlaps')

        Shape_group.addButton(self.rb_ShapeTrapez)
        Shape_group.addButton(self.rb_ShapeTrapez2)
        Shape_group.addButton(self.rb_ShapeRect)

        # Set Parameters

        t_width = QtGui.QLabel('Set Maximum Width in mm:', self)
        t_width.setGeometry(20, 205, 150, 20)
        self.e_width = QtGui.QLineEdit('%.2f' % self.width, self)
        self.e_width.setGeometry(20, 225, 150, 20)
        self.e_width.setObjectName('width')
        self.e_width.editingFinished.connect(self.changeValue)

        t_angle = QtGui.QLabel('Set Fiber Angle in Degree:', self)
        t_angle.setGeometry(20, 250, 150, 20)
        self.e_angle = QtGui.QLineEdit('%.2f' % self.angle, self)
        self.e_angle.setGeometry(20, 270, 150, 20)
        self.e_angle.setObjectName('angle')
        self.e_angle.editingFinished.connect(self.changeValue)

        t_start = QtGui.QLabel('Set Starting position in mm :', self)
        t_start.setGeometry(20, 295, 150, 20)
        self.e_start = QtGui.QLineEdit('%.2f' % self.start, self)
        self.e_start.setGeometry(20, 315, 150, 20)
        self.e_start.setObjectName('start')
        self.e_start.editingFinished.connect(self.changeValue)

        t_var = QtGui.QLabel('Set Width Variation:', self)
        t_var.setGeometry(20, 340, 150, 20)
        self.e_var = QtGui.QLineEdit('%.2f' % self.var, self)
        self.e_var.setGeometry(20, 360, 150, 20)
        self.e_var.setObjectName('var')
        self.e_var.editingFinished.connect(self.changeValue)

        # Explanations

        self.cb_exp = QtGui.QCheckBox('Plot without explanations (only Geometry)', self)
        self.cb_exp.setGeometry(20, 385, 250, 20)
        self.cb_exp.stateChanged.connect(self.changeExp)

        # Start Printing

        pb_plotPieces = QtGui.QPushButton('Plot Ply Pieces', self)
        pb_plotPieces.clicked.connect(self.plotPlyPieces)
        pb_plotPieces.setGeometry(140, 525, 120, 40)
        pb_plotPieces.setStatusTip('Create plot of ply pieces')

        self.show()

    def openConeGeo(self, state):
        self.GeoApp = GUIConeGeo.ConeGeo(self.data_handle)

    def closeWindow(self):
        self.close()

    def changeType(self, state):
        source = self.sender()

        if source.objectName() == "TypeGeo":
            self.type = 1
            self.cb_ShowPieces.move(1000, 1000)
            self.t_ResPhi.move(1000, 1000)
            self.e_ResPhi.move(1000, 1000)
            self.t_ResS.move(1000, 1000)
            self.e_ResS.move(1000, 1000)
        if source.objectName() == "TypeAngle":
            self.type = 2

            self.cb_ShowPieces.move(20, 410)
            self.t_ResPhi.move(20, 435)
            self.e_ResPhi.move(20, 455)
            self.t_ResS.move(20, 480)
            self.e_ResS.move(20, 500)
        if source.objectName() == "TypeThick":
            self.type = 3

            self.cb_ShowPieces.move(20, 410)
            self.t_ResPhi.move(20, 435)
            self.e_ResPhi.move(20, 455)
            self.t_ResS.move(20, 480)
            self.e_ResS.move(20, 500)

    def changeShape(self, state):
        source = self.sender()

        if source.objectName() == "ShapeTrapez":
            self.shape = 1
        if source.objectName() == "ShapeTrapez2":
            self.shape = 2
        if source.objectName() == "ShapeRect":
            self.shape = 3


    def changeValue(self):
        source = self.sender()
        text = source.text()
        value = text.toDouble()
        value = value[0]

        source_name = str(source.objectName())
        setattr(self, source_name, value)
        widget = getattr(self, 'e_' + source_name)
        format = "%.0f" if source_name in ('ResS', 'ResPhi') else "%.2f"
        widget.setText(format % value)

    def changeExp(self, state):
        if state == QtCore.Qt.Checked:
            self.show_explanations = True
            self.cb_exp.setText('Plot with explanations')
        if state == QtCore.Qt.Unchecked:
            self.show_explanations = False
            self.cb_exp.setText('Plot without explanations (only Geometry)')

    def changeShowPiece(self, state):
        if state == QtCore.Qt.Checked:
            self.show_pieces = True
        if state == QtCore.Qt.Unchecked:
            self.show_pieces = False

    def plotPlyPieces(self, state):
        L0 = Line2D.from_point_angle(Point2D(self.start, 0.0), math.radians(self.angle))
        if len(L0.all_intersections_circle(self.data_handle.cg.s1)) == 0:
            ErrorMsg = QtGui.QMessageBox.critical(self, 'Error',
                "The Start Value is too high for this Fiber Angle. \n The fibers do not reach to the upper cone edge.",
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return

        model = self.buildModel()

        # Evaluate the model
        Phi        = model.corner_orientations()
        num_pieces = model.num_pieces()
        A_piece    = model.ply_piece_area()
        A_ply      = A_piece * num_pieces

        R_DoC      = A_ply / self.data_handle.cg.cone_area
        Aeff       = model.effective_area()[0]
        R_Aeff     = Aeff / A_piece
        R_cont     = model.ratio_continuous_fibers()
        R_total    = R_DoC * R_Aeff * R_cont
        R_SumAeff  = R_DoC * R_Aeff

        result = GUIHandle.Result(
            angle=self.angle, start=self.start, width=self.width, var=self.var,
            Phi1=Phi[0], Phi2=Phi[1], Phi3=Phi[2], Phi4=Phi[3],
            num_pieces=num_pieces, R_DoC=R_DoC, R_Aeff=R_Aeff,
            R_cont=R_cont, R_SumAeff=R_SumAeff, R_total=R_total)

        self.plot_window = PlotWindow()
        if self.type == 1:
            self.printLP(model, self.plot_window.qmc.fig)
        elif self.type == 2:
            self.printAngleThickness(model, self.plot_window.qmc.fig, True)
        elif self.type == 3:
            self.printAngleThickness(model, self.plot_window.qmc.fig, False)
        else:
            assert False
        self.plot_window.show()
        self.result_window = ResultTable(model, result)

    def buildModel(self):
        # Build the ply piece model
        cg = self.data_handle.cg
        if self.shape == 1:
            model = TrapezPlyPieceModel(cg, self.angle, self.start, self.width, 0.0, self.var)
        elif self.shape == 2:
            model = Trapez2PlyPieceModel(cg, self.angle, self.start, self.width, 0.0, self.var)
        elif self.shape == 3:
            model = RectPlyPieceModel(cg, self.angle, self.start, self.width, 0.0, self.var)
        else:
            assert False # Should never be reached
        model.rebuild()
        return model

    def printAngleThickness(self, model, fig, print_angle=True):
        # Prints the local fiber angle or ply thickess of the given ply shape
        ax = fig.add_subplot(111)
        cg = self.data_handle.cg

        s_pts = np.linspace(cg.s2 + 1, cg.s3 - 1, self.ResS + 1)
        phi_min = 0
        phi_max = 2 * np.pi * cg.sin_alpha
        phi_pts = np.linspace(phi_min, phi_max, self.ResPhi + 1)
        s, phi = np.meshgrid(s_pts, phi_pts)
        x = s * np.cos(phi)
        y = s * np.sin(phi)

        func = model.local_orientation if print_angle else model.local_num_pieces
        value = np.array([func(x_i, y_i) + 0.5 for x_i, y_i in zip(x.flatten(), y.flatten())])
        value = np.reshape(value, s.shape)

        if print_angle:
            colors = ax.contourf(x, y, value)
            fig.colorbar(colors)
        else:
            levels = range(1, 14)
            colors = ax.contourf(x, y, value, levels)
            fig.colorbar(colors, ticks=[lvl+0.5 for lvl in levels[:-1]], format='%d')


        styles = ('k--', 'k', 'k', 'k--')
        NUM_PTS_CIRCLE = 300
        # Construct unit circle
        phi_circle = np.hstack((np.array([0.0]),
                               np.linspace(phi_min, phi_max, NUM_PTS_CIRCLE + 1),
                               np.array([0.0])))
        r_circle = np.ones_like(phi_circle)
        r_circle[0] = r_circle[-1] = 0.0
        x_circle = r_circle*np.cos(phi_circle)
        y_circle = r_circle*np.sin(phi_circle)
        # Plot circles (arcs) with radii s1...s4
        for r, style in zip(self.data_handle.get_s(), styles):
            ax.plot(r*x_circle, r*y_circle, style)

        NUM_RADIAL_LINES = 36
        for phi_line in np.linspace(phi_min, phi_max, NUM_RADIAL_LINES + 1):
            L1x = cg.s1*np.cos(phi_line)
            L2x = cg.s4*np.cos(phi_line)
            L1y = cg.s1*np.sin(phi_line)
            L2y = cg.s4*np.sin(phi_line)
            ax.plot([L1x, L2x], [L1y, L2y], '--k')

        limit = cg.s4
        if self.show_pieces:
            for pp in model.ply_pieces:
                line_x, line_y = pp.polygon.get_closed_line()
                limit = max(limit, max(abs(x) for x in line_x), max(abs(y) for y in line_x))
                ax.plot(line_x, line_y, '--g')

        ax.set_adjustable('box')
        ax.set_aspect(1, 'box', 'SW')

        limit = max(limit*1.1, 1000.0)
        ax.axis([-limit, limit, -limit, limit])
        ax.set_aspect('equal')
        ax.set_title('Local Fiber Angle' if print_angle else 'Local thickness')

    def printLP(self, model, fig):
        # Prints ply pieces on unwounded cone area
        ax = fig.add_subplot(111)
        cg = self.data_handle.cg

        # Print cone background

        styles = ('--', '-', '-', '--')
        NUM_PTS_CIRCLE = 300
        phi_min = 0
        phi_max = 2 * np.pi * cg.sin_alpha
        # Construct unit circle
        phi_circle = np.hstack((np.array([0.0]),
                               np.linspace(phi_min, phi_max, NUM_PTS_CIRCLE + 1),
                               np.array([0.0])))
        r_circle = np.ones_like(phi_circle)
        r_circle[0] = r_circle[-1] = 0.0
        x_circle = r_circle*np.cos(phi_circle)
        y_circle = r_circle*np.sin(phi_circle)
        # Plot circles (arcs) with radii s1...s4
        for r, style in zip(self.data_handle.get_s(), styles):
            ax.plot(r*x_circle, r*y_circle, color='0.85', ls=style)

        NUM_RADIAL_LINES = 36
        for phi_line in np.linspace(phi_min, phi_max, NUM_RADIAL_LINES + 1):
            L1x = cg.s1*np.cos(phi_line)
            L2x = cg.s4*np.cos(phi_line)
            L1y = cg.s1*np.sin(phi_line)
            L2y = cg.s4*np.sin(phi_line)
            ax.plot([L1x, L2x], [L1y, L2y], color='0.50', ls='--')

        # print ply pieces
        limit = cg.s4
        if self.show_pieces:
            for pp in model.ply_pieces:
                line_x, line_y = pp.polygon.get_closed_line()
                limit = max(limit, max(abs(x) for x in line_x), max(abs(y) for y in line_x))
                ax.plot(line_x, line_y, color='k')

        if self.show_explanations == 1:
            # print Labels L1 to L4
            P1, P2, P3, P4 = model.base_piece.polygon.points()
            L1pt = 0.5*(P1 + P2)
            L2pt = 0.5*(P2 + P3)
            L3pt = 0.5*(P3 + P4)
            L4pt = 0.5*(P4 + P1)

            ax.annotate('l1', xy=L1pt, xycoords='data',
                xytext=( -5, 15), textcoords='offset points', color='r')
            ax.annotate('l2, max. Width', xy=L2pt, xycoords='data',
                xytext=( 5, 0), textcoords='offset points', color='r')
            ax.annotate('l3', xy=L3pt, xycoords='data',
                xytext=( 5, -15), textcoords='offset points', color='r')
            ax.annotate('l4', xy=L4pt, xycoords='data',
                xytext=( -15, -5), textcoords='offset points', color='r')

            # print Labels Theta, s_start
            th_arc = np.array(range(0, int(self.angle)+1))
            th_arc = np.radians(th_arc)
            arc_x = self.start + 50.0*np.cos(th_arc)
            arc_y = 50.0*np.sin(th_arc)
            ax.plot(arc_x, arc_y, color='k')
            angle_rad = np.radians(self.angle)
            angle_x = [self.start + 70*np.cos(angle_rad), self.start, self.start + 70]
            angle_y = [70*np.sin(angle_rad), 0, 0]
            ax.plot(angle_x, angle_y, color='k')
            ArcAnnoName = 'Theta: ' + str(self.angle)
            ax.annotate(ArcAnnoName, xy=(self.start+50.0, 20.0), xycoords='data',
                xytext=(0,0), textcoords='offset points')

            ax.plot([0.0, self.start], [0.0, 0.0], color='k', marker = 'D', linewidth = 3.0)
            S_start_name = 'starting pos:  \n' +str(self.start) +' mm'
            ax.annotate(S_start_name, xy=(0.0, 0.0), xycoords='data',
                xytext=(20, -25), textcoords='offset points')
            ax.annotate('Eff. Area', xy=(cg.s2+100.0, -10.0), xycoords='data',
                xytext=(50,-50), textcoords='offset points', color='orange',
                arrowprops=dict(arrowstyle = "->", color='orange'))

        # Patches indicating the effective area
        for pp in model.ply_pieces:
            P_tmp = list(model.effective_area(ply_piece=pp)[1].points())
            if len(P_tmp) > 0:
                P_tmp.append([0, 0]) # Add dummy point for CLOSEPOLY
                codes = [Path.MOVETO] + (len(P_tmp)-2)*[Path.LINETO] + [Path.CLOSEPOLY]
                path = Path(P_tmp, codes)
                patch = PathPatch(path, facecolor='black', alpha=0.3)
                ax.add_patch(patch)

        # Make sections outside the cone white (by force)
        NUM_PTS = 100
        phi_outside = np.linspace(phi_max, phi_min + 2*np.pi, NUM_PTS)
        x_outside = cg.s4*np.cos(phi_outside)
        y_outside = cg.s4*np.sin(phi_outside)
        P_tmp = [(0, 0)] + list(zip(x_outside, y_outside)) + [(0, 0)]
        codes = [Path.MOVETO] + NUM_PTS*[Path.LINETO] + [Path.CLOSEPOLY]
        path = Path(P_tmp, codes)
        patch = PathPatch(path, facecolor='white', edgecolor='white')
        ax.add_patch(patch)

        limit = max(limit*1.1, 1000.0)
        ax.axis([-limit, limit, -limit, limit])
        ax.set_aspect('equal')
        ax.set_title('Ply Piece Geometry')


class ResultTable(QtGui.QWidget):
    def __init__(self, model, result):
        super(ResultTable, self).__init__()
        self.setGeometry(300, 300, 280, 300)
        self.setWindowTitle('Result Table')

        lengths = model.edge_lengths()

        my_array = [['Input', ' '],
                    ['Fiber Angle in Degree', '%.2f' % result.angle],
                    ['Maximum Width in mm', '%.2f' % result.width],
                    ['s_start in mm', '%.2f' % result.start],
                    ['Variation', '%.2f' % result.var],
                    ['Geometry', ' '],
                    ['l1 in mm', '%.2f' % lengths[0]],
                    ['l2 in mm', '%.2f' % lengths[1]],
                    ['l3 in mm', '%.2f' % lengths[2]],
                    ['l4 in mm', '%.2f' % lengths[3]],
        # I have really no clue what the meaning of this is. Therefore I left
        # it out while porting the code -- Jasper Reichardt
                    #['Overlapping Length in mm', '%.2f' % OVLength],
                    ['Ratios', ' '],
                    ['Degree of Coverage in %', '%.2f' %(result.R_DoC*100.0)],
                    ['Ratio of effective area in %', '%.2f' %(result.R_Aeff*100.0)],
                    ['Ratio of continous fibers in %', '%.2f' % (result.R_cont*100.0) ],
                    ['Ratio of total effective area in %', '%.2f' % (result.R_SumAeff*100.0)],
                    ['Ratio of total effectiveness in %', '%.2f' % (result.R_total*100.0)],
                    ['Details', ' '],
                    ['Number of plies', '%.2f' % result.num_pieces ],
                    ['phi(T1) in Degree', '%.2f' % result.Phi1 ],
                    ['phi(T2) in Degree', '%.2f' % result.Phi2 ],
                    ['phi(T3) in Degree', '%.2f' % result.Phi3 ],
                    ['phi(T4) in Degree', '%.2f' % result.Phi4 ],]


        tablemodel = MyTableModel(my_array, self)
        tableview  = QtGui.QTableView()
        tableview.setModel(tablemodel)
        tableview.resizeColumnsToContents()

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(tableview)
        self.setLayout(layout)

        self.show()


class MyTableModel(QtCore.QAbstractTableModel):
    def __init__(self, datain, parent = None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.arraydata = datain

    def rowCount(self, parent):
        return len(self.arraydata)

    def columnCount(self, parent):
        return len(self.arraydata[0])

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        elif role == QtCore.Qt.BackgroundRole:
            if index.row() in (0, 5, 10, 16):
                return QtGui.QBrush(QtGui.QColor(200,200,200))
            else:
                return QtGui.QBrush(QtGui.QColor(255,255,255))

        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        return (self.arraydata[index.row()][index.column()])
