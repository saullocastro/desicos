import glob
import sys
sys.path.append(r'C:\clones\desicos')

from desicos.conecylDB.read_write import xyz2thetazimp, xyzthick2thetazthick

for path in glob.glob('*_msi.txt'):
    xyz2thetazimp(path, 0, 250, 510, fmt='%1.8f')

for path in glob.glob('*_ti.txt'):
    xyzthick2thetazthick(path, 0, 250, 510, fmt='%1.8f')
