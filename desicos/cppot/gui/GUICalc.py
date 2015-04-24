import math
import time

from PyQt4 import QtGui

import GUIHandle
from desicos.cppot.core.ply_model import TrapezPlyPieceModel, \
    Trapez2PlyPieceModel, RectPlyPieceModel

REFRESH_INTERVAL = 0.05 # Refresh GUI every .. seconds

class Variation(QtGui.QMainWindow):
    def __init__(self, MainWindow, handle):
        super(Variation, self).__init__()

        # Init Handles
        self.result_handle = GUIHandle.ResultHandle()
        self.data_handle = handle

        self.initUI()

    def calc(self):
        # Calculate Variations and their Ratios
        # This is implemented as a generator, that periodically yields control
        # to the main UI. This allows keeping the GUI responsive
        last_time = time.time()

        # Get Input Parameters
        # Make a duplicate of handle, to allow modifications
        handle = self.data_handle.make_copy()

        # Set Input for Progress bar
        num_calc = handle.num_calc() # Max Number of Variations
        num_done = 0

        maxStartlist = []
        # Fiber Angle Loop
        for angle in handle.angle.steps():
            # Check for highest possible s_start value
            # Where the line L0 still touches the circle
            angle_rad = math.radians(angle)
            s_start_max = self.data_handle.start.max_value
            if angle_rad != 0:
                s_start_limit = handle.cg.s1 / math.sin(abs(angle_rad))
                s_start_max = min(s_start_max, s_start_limit)
            handle.start.max_value = s_start_max
            maxStartlist.append(s_start_max)

            # s_start Loop
            for start in handle.start.steps():
                # Width Loop
                for width in handle.width.steps():
                    # Variation Loop
                    for var in handle.var.steps():

                        # build ply piece model
                        try:
                            model = self.buildModel(start, angle, width, var)
                        except ValueError:
                            print angle, start, width, var
                            raise

                        # Evaluate the model
                        Phi        = model.corner_orientations()
                        num_pieces = model.num_pieces()
                        A_piece    = model.ply_piece_area()
                        A_ply      = A_piece * num_pieces

                        R_DoC      = A_ply / handle.cg.cone_area
                        Aeff       = model.effective_area()[0]
                        R_Aeff     = Aeff / A_piece
                        R_cont     = model.ratio_continuous_fibers()
                        R_total    = R_DoC * R_Aeff * R_cont
                        R_SumAeff  = R_DoC * R_Aeff

                        # Save Results to ResultHandle
                        self.result_handle.add(
                            angle=angle, start=start, width=width, var=var,
                            Phi1=Phi[0], Phi2=Phi[1], Phi3=Phi[2], Phi4=Phi[3],
                            num_pieces=num_pieces, R_DoC=R_DoC, R_Aeff=R_Aeff,
                            R_cont=R_cont, R_SumAeff=R_SumAeff, R_total=R_total)
                        num_done += 1

                        if time.time() - last_time > REFRESH_INTERVAL:
                            # update progress bar
                            progress = 100.0 * num_done / num_calc
                            self.pbar.setValue(progress)
                            yield progress
                            last_time = time.time()

            # Compensate for steps missed by reducing start.max_value
            skipped_steps = (handle.start.num_steps() - self.data_handle.start.num_steps())
            num_done += skipped_steps * handle.var.num_steps() * handle.width.num_steps()

        if not self.data_handle.start:
            self.data_handle.start.max_value = max(maxStartlist)

    def buildModel(self, start, angle, width, var):
        # Build the ply piece model
        shape = self.data_handle.shape
        cg = self.data_handle.cg
        if shape == 1:
            model = TrapezPlyPieceModel(cg, angle, start, width, 0.0, var)
        elif shape == 2:
            model = Trapez2PlyPieceModel(cg, angle, start, width, 0.0, var)
        elif shape == 3:
            model = RectPlyPieceModel(cg, angle, start, width, 0.0, var)
        else:
            assert False # Should never be reached
        model.rebuild()
        return model

    def initUI(self):
        # Progress Bar

        self.setGeometry(500, 500, 240, 65)
        self.setWindowTitle('Progress')

        self.pbar = QtGui.QProgressBar(self)
        self.pbar.setGeometry(20, 20, 200, 25)
        self.pbar.setValue(0.0)

        self.show()
