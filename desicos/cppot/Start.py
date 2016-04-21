import sys
import os

from PyQt4 import QtGui

#----------------------------------
# CONE PLY PIECE OPTIMIZATION TOOL
#----------------------------------
#
# by   Florian Burau
# Date 16.01.2014
#
#----------------------------------

desicos_folder = os.path.realpath('../..')
sys.path.append(desicos_folder)

from gui import GUIInput

def main (args):
    app = QtGui.QApplication(sys.argv)
    ex = GUIInput.InputWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main(sys.argv)
