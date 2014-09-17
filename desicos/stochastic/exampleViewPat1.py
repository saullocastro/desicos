import sys
sys.path.append( '../stochastic/')
sys.path.append( '../abaqus-conecyl-python_DEV/')
from conecylDB import imps, R_measured, H_measured, t_measured
from measured_imp_ms import read_file
from stochastic.imperfGen import *
import numpy.ma
from viewer import DesicosViewer3D


k=0.26

sg=ImperfFactory()
sg.addInputsFromCCDB(['degenhardt_2010_z22','degenhardt_2010_z23','degenhardt_2010_z25'])
sg.compute()
desView3D=DesicosViewer3D()
desView3D.setScalingFactor(200.)


sg.sMidS.strFacts[0].connectOutputArray(sg.sMidS.aveFunc)

aa=sg.sThick.indata[0]
tmax=np.max(aa)
tmin=np.min(aa)
tval=tmin+k*(tmax-tmin)
mask=ma.masked_greater(aa,tval).mask
aa[mask]=0.0

#plot Surface pattern
desView3D.addArray2d(sg.sThick.x*sg.sThick.RB,sg.sThick.y,aa)#,mode='square')

#plot Full Power spectrum
#desView3D.addArray2d(sg.sMidS.x*sg.sMidS.RB,sg.sMidS.y,sg.sMidS.winFilter)#,mode='square')

#plot Interpolated Power spectrum
#desView3D.addArray2d(sg.sMidS.fyIn,sg.sMidS.fxIn,sg.sMidS.shMod,mode='square')

#desView3D.addWidgets()
desView3D.show()
