import sys
sys.path.append( '../stochastic')
from  st_utils.coords import *
import vtk
import numpy as np


points = vtk.vtkPoints();
d=np.loadtxt('imp1.txt',delimiter=',')
tht=np.linspace(0,250.*2.0*np.pi,d.shape[1])
z=np.linspace(0,500,d.shape[0])



for i in range(d.shape[0]-1):
	for j in range(d.shape[1]-1):
		xx=tht[j]
		yy=z[i]
		zz=100*d[i][j]
		points.InsertNextPoint(xx, yy, zz);

#d=np.loadtxt(r'res/pat.txt')
#r,t,z = rec2cyl(d[:,0],d[:,1],d[:,2])
#r-=r.mean()
#r*=100.0
#t*=250.0
#
#for i in range(d.shape[0]-1):
#	points.InsertNextPoint(t[i],z[i],r[i])
#
inputPolyData = vtk.vtkPolyData();
inputPolyData.SetPoints(points);
delaunay = vtk.vtkDelaunay2D()
delaunay.SetTolerance(0.000001)
delaunay.SetInput(inputPolyData);
delaunay.Update();
outputPolyData = delaunay.GetOutput();
bounds=outputPolyData.GetBounds();
 
minz = bounds[4];
maxz = bounds[5];

lut=vtk.vtkLookupTable()
lut.SetNumberOfTableValues(100)
lut.SetTableRange(minz, maxz)
lut.SetHueRange(0.667, 0.0)
lut.Build()

colors=vtk.vtkFloatArray()
for i in range(0,outputPolyData.GetNumberOfPoints()):
	colors.InsertNextValue(outputPolyData.GetPoint(i)[2])

outputPolyData.GetPointData().SetScalars(colors);
mapper = vtk.vtkPolyDataMapper();
mapper.SetLookupTable(lut)
mapper.InterpolateScalarsBeforeMappingOn()
mapper.SetInputConnection(outputPolyData.GetProducerPort())
mapper.SetScalarModeToUsePointData()
mapper.ScalarVisibilityOn();
mapper.SetScalarRange(colors.GetRange())
surfaceActor = vtk.vtkActor();
surfaceActor.SetMapper(mapper);

ren = vtk.vtkRenderer();
ren.AddActor(surfaceActor);
renWin = vtk.vtkRenderWindow();
renWin.AddRenderer(ren);
renWin.SetWindowName("DESICOS-viewer v0.1 ")
iren = vtk.vtkRenderWindowInteractor();
iren.SetRenderWindow(renWin);
style1 = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style1)
ren.SetBackground(1, 1, 1);
renWin.SetSize(800, 600);

ren.ResetCamera()
iren.Initialize();
renWin.Render();
iren.Start();


