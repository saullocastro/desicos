from viewer import DesicosViewer3D
dv=DesicosViewer3D()
dv.scalingFactor=60.0
dv.addCSVFile('res/pat.txt')
dv.writeVTP('test.vtp')
dv.addWidgets()
dv.show()
