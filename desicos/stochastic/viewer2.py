#!/usr/bin/env python

# This example shows how to use Delaunay3D with alpha shapes.
import sys
sys.path.append( '../stochastic')
from  st_utils.coords import *
import vtk
import numpy as np


#pts=np.loadtxt('res/ex3_thick.txt')
pts=np.loadtxt('res/outPat.txt')

def transform_back(pt,pd):
	#The reconstructed surface is transformed back to where the
	#original points are. (Hopefully) it is only a similarity
	#transformation.

	#1. Get bounding box of pt, get its minimum corner (left, bottom, least-z), at c0, pt_bounds

	#2. Get bounding box of surface pd, get its minimum corner (left, bottom, least-z), at c1, pd_bounds

	#3. compute scale as: 
	#      scale = (pt_bounds[1] - pt_bounds[0])/(pd_bounds[1] - pd_bounds[0]);

	#4. transform the surface by T := T(pt_bounds[0], [2], [4]).S(scale).T(-pd_bounds[0], -[2], -[4])

	pt_bounds=pt.GetBounds()

	pd_bounds=pd.GetBounds()

	scale = (pt_bounds[1] - pt_bounds[0])/(pd_bounds[1] - pd_bounds[0]);

	transp = vtk.vtkTransform()
	transp.Translate(pt_bounds[0], pt_bounds[2], pt_bounds[4]);
	transp.Scale(scale, scale, scale);
	transp.Translate(- pd_bounds[0], - pd_bounds[2], - pd_bounds[4]);

	tpd = vtk.vtkTransformPolyDataFilter();
	tpd.SetInput(pd);
	tpd.SetTransform(transp);
	tpd.Update();


	return tpd.GetOutput();


	
	
class rgbPainter:
	def __init__(self):
		self.values=[]
	def setValue(self,val):
		self.values.append(float(val))

	def getMinValue(self):
		a=np.array(self.values)
		return a.min()

	def getMaxValue(self):
		a=np.array(self.values)
		return a.max()

	
	def getPCT(self,val):
		MIN=self.getMinValue()
		MAX=self.getMaxValue()
		l=MAX-MIN
		return (val-MIN)/l

	def getRGB(self,val):
		rgb=[0.,0.,0.]
		MIN=self.getMinValue()
		MAX=self.getMaxValue()
		l=MAX-MIN

		pct=self.getPCT(val)
		r=1.0
		g=1.0
		b=1.0
		if (val < (MIN + 0.25 * l)):
			r = 0
			g = 4 * (val - MIN) / l
		elif (val < (MIN + 0.5 * l)):
			r = 0
			b = 1 + 4 * (MIN + 0.25 * l - val) / l
		elif (val < (MIN + 0.75 * l)):
			r = 4 * (val - MIN - 0.5 * l) / l
			b = 0;
		else:
			g = 1 + 4 * (MIN + 0.75 * l - val) / l
			b = 0
		
		rgb=[255.0*r,255.0*g,255.0*b]
		return rgb 

sf=10.0
paint=rgbPainter()
r,t,z = rec2cyl(pts[:,0],pts[:,1],pts[:,2])

#im=np.abs(getGeomImperfection(r,z,np.mean(r)))
if pts.shape[1] == 4:
	im=pts[:,3]
else:
	im=getGeomImperfection(r,z,np.mean(r))
rid=r-im
xx,yy,zz=cyl2rec(rid+im*sf,t,z)

math = vtk.vtkMath()
points = vtk.vtkPoints()

colors =vtk.vtkUnsignedCharArray()
colors.SetNumberOfComponents(3);
colors.SetName("Colors");

for i in range(0,pts.shape[0]):
	#points.InsertPoint(i,pts[i][0],pts[i][1],pts[i][2] )
	points.InsertPoint(i,xx[i],yy[i],zz[i] )
polydata = vtk.vtkPolyData()
polydata.SetPoints(points)
polydata.GetPointData().SetScalars(colors)
polydata.Update()


  vtkSmartPointer<vtkGaussianSplatter> splatter = 
    vtkSmartPointer<vtkGaussianSplatter>::New();
#if VTK_MAJOR_VERSION <= 5
  splatter->SetInput(polydata);
#else
  splatter->SetInputData(polydata);
#endif
  splatter->SetSampleDimensions(50,50,50);
  splatter->SetRadius(0.5);
  splatter->ScalarWarpingOff();
 
  vtkSmartPointer<vtkContourFilter> surface = 
    vtkSmartPointer<vtkContourFilter>::New();
  surface->SetInputConnection(splatter->GetOutputPort());
  surface->SetValue(0,0.01);
 
  // Create a mapper and actor
  vtkSmartPointer<vtkPolyDataMapper> mapper = 
    vtkSmartPointer<vtkPolyDataMapper>::New();
  mapper->SetInputConnection(surface->GetOutputPort())
surf =vtk.vtkSurfaceReconstructionFilter()
surf.SetInput(polydata)
surf.SetNeighborhoodSize(100)
#surf.SetSampleSpacing(6.0)

contourFilter = vtk.vtkContourFilter()
contourFilter.SetInputConnection(surf.GetOutputPort())
reverse = vtk.vtkReverseSense()
reverse.SetInputConnection(contourFilter.GetOutputPort())
reverse.ReverseCellsOn()
reverse.ReverseNormalsOn()
reverse.Update()


outputPolyData=reverse.GetOutput()
#for i in range(0,pts.shape[0]):
#	dcolor=np.zeros(3)
#	colorLookupTable.GetColor(im[i],dcolor)
#	cc=dcolor*255.0
#	colors.InsertNextTupleValue(cc)
#outputPolyData.GetPointData().SetScalars(polydata.GetPointData().GetScalars() );



newSurf = transform_back( points, reverse.GetOutput());

pts2=np.zeros((newSurf.GetNumberOfPoints(),3))
for i in range(0,newSurf.GetNumberOfPoints()):
	pts2[i,:]=newSurf.GetPoint(i)
r2,t2,z2 = rec2cyl(pts2[:,0],pts2[:,1],pts2[:,2])
im2=getGeomImperfection(r2,z2,np.mean(r2))
#im2-=np.min(im2)
#im2=np.abs(im2)
paint.setValue(np.min(im2))
paint.setValue(np.max(im2))


for i in range(0,newSurf.GetNumberOfPoints()):
	colors.InsertNextTupleValue(paint.getRGB(im2[i]))

newSurf.GetPointData().SetScalars(colors );

mapper = vtk.vtkPolyDataMapper();
mapper.InterpolateScalarsBeforeMappingOn()
#mapper.SetInputConnection(outputPolyData.GetProducerPort())
mapper.SetInputConnection(newSurf.GetProducerPort())
mapper.SetScalarModeToUsePointData()
mapper.ScalarVisibilityOn();

surfaceActor = vtk.vtkActor();
surfaceActor.SetMapper(mapper);

ren = vtk.vtkRenderer();
renWin = vtk.vtkRenderWindow();
renWin.AddRenderer(ren);
iren = vtk.vtkRenderWindowInteractor();
iren.SetRenderWindow(renWin);
style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

ren.AddActor(surfaceActor);
ren.SetBackground(1, 1, 1);
renWin.SetSize(800, 600);

prn=1000.
pc=-prn
plXY = vtk.vtkPlaneSource()
plXY.SetPoint1(prn,-prn,0)
plXY.SetPoint2(-prn,prn,0)
plXY.SetOrigin(pc,pc,0)
plXY.SetCenter(0,0,0)
plXYmap = vtk.vtkPolyDataMapper()
plXYmap.SetInput(plXY.GetOutput())
plXYact = vtk.vtkActor()
plXYact.SetMapper(plXYmap)
plXYact.GetProperty().SetOpacity(0.1)


plYZ = vtk.vtkPlaneSource()
plYZ.SetCenter(0,pc,pc)
plYZ.SetPoint1(0,prn,-prn)
plYZ.SetPoint2(0,-prn,prn)
plYZmap = vtk.vtkPolyDataMapper()
plYZmap.SetInput(plYZ.GetOutput())
plYZact = vtk.vtkActor()
plYZact.SetMapper(plYZmap)
plYZact.GetProperty().SetOpacity(0.1)

plZX = vtk.vtkPlaneSource()
plZX.SetCenter(pc,0,pc)
plZX.SetPoint1(prn,0,-prn)
plZX.SetPoint2(-prn,0,prn)
plZXmap = vtk.vtkPolyDataMapper()
plZXmap.SetInput(plZX.GetOutput())
plZXact = vtk.vtkActor()
plZXact.SetMapper(plZXmap)
plZXact.GetProperty().SetOpacity(0.1)


ren.AddActor(plXYact)
ren.AddActor(plYZact)
ren.AddActor(plZXact)

ax=vtk.vtkAxesActor()
ax.GetXAxisCaptionActor2D().GetProperty().SetColor(0,0,0)
ax.GetYAxisCaptionActor2D().GetProperty().SetColor(0,0,0)
ax.GetZAxisCaptionActor2D().GetProperty().SetColor(0,0,0)
ow=vtk.vtkOrientationMarkerWidget()
ow.SetOrientationMarker(ax)
ow.SetInteractor(iren)
ow.SetViewport( 0.0, 0.0, 0.4, 0.4 )
ow.SetEnabled( 1 )
ow.InteractiveOn()

lut=vtk.vtkLookupTable()
lut.SetHueRange( 0.66667, 0.0 )
lut.SetSaturationRange (1.0, 1.0)
lut.SetNumberOfColors(50)# len(self.plotables))
lut.SetTableRange(paint.getMinValue(),paint.getMaxValue())
lut.Build()
scalar_bar = vtk.vtkScalarBarActor()
scalar_bar.SetOrientationToHorizontal()
scalar_bar.SetLookupTable(lut)
scalar_bar.SetTitle("Imperfection value");
scalar_bar.SetNumberOfLabels(11)

scalar_bar_widget = vtk.vtkScalarBarWidget()
scalar_bar_widget.SetInteractor(iren)
scalar_bar_widget.SetScalarBarActor(scalar_bar)
scalar_bar_widget.On()


iren.Initialize();
renWin.Render();
iren.Start();

