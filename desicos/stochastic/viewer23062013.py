#!/usr/bin/env python
import sys
sys.path.append( '../stochastic')
from  st_utils.coords import *
import vtk
import numpy as np

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

class DesicosViewer3D(object):

	def __init__(self):
		self.outputs=[]
		self.paint=rgbPainter()
		self.scalingFactor=1.0
		self.showAxes=True
		self.showScalarBar=True
		self.showCaption=True
		self.showXYPlane=True
		self.showYZPlane=True
		self.showZXPlane=True
		self.nbSize=80
		self.sampleSpacing=8.0
	
		self.camera = vtk.vtkCamera()

		self.ren = vtk.vtkRenderer();
		self.renWin = vtk.vtkRenderWindow();
		self.renWin.AddRenderer(self.ren);
		self.renWin.SetWindowName("DESICOS-viewer v0.1 ")
		self.iren = vtk.vtkRenderWindowInteractor();
		self.iren.SetRenderWindow(self.renWin);
		style1 = vtk.vtkInteractorStyleTrackballCamera()
		self.iren.SetInteractorStyle(style1)
		self.ren.SetBackground(1, 1, 1);
		self.renWin.SetSize(800, 600);

	def show(self):
		self.ren.ResetCamera()
		self.iren.Initialize();
		self.renWin.Render();
		self.iren.Start();
	def close(self):
		self.renWin.Finalize()

	def setCaption(self,text):
		self.caption=text
		self.renWin.SetWindowName("DESICOS-viewer v0.1 " +str(text))

	def writeVTP(self,fname,i=0):
		writer=vtk.vtkXMLPolyDataWriter()
		writer.SetFileName(fname)
		writer.SetInput(self.outputs[i])
		writer.Write()

	def addCSVFile(self,fname,csvDelimiter=None):
		self.setCaption(r' File:'+str(fname))
		pts=np.loadtxt(fname,csvDelimiter)
		r,t,z = rec2cyl(pts[:,0],pts[:,1],pts[:,2])
		sf=self.scalingFactor

		if pts.shape[1] == 4:
			im=pts[:,3]
		else:
			im=getGeomImperfection(r,z,np.mean(r))
		rid=r-im
		xx,yy,zz=cyl2rec(rid+im*sf,t,z)
		points = vtk.vtkPoints()

		colors =vtk.vtkUnsignedCharArray()
		colors.SetNumberOfComponents(3);
		colors.SetName("Colors");

		for i in range(0,pts.shape[0]):
			points.InsertPoint(i,xx[i],yy[i],zz[i] )
		polydata = vtk.vtkPolyData()
		polydata.SetPoints(points)
		polydata.GetPointData().SetScalars(colors)
		polydata.Update()

		surf =vtk.vtkSurfaceReconstructionFilter()
		surf.SetInput(polydata)
		surf.SetNeighborhoodSize(self.nbSize)
		surf.SetSampleSpacing(self.sampleSpacing)

		contourFilter = vtk.vtkContourFilter()
		contourFilter.SetInputConnection(surf.GetOutputPort())
		reverse = vtk.vtkReverseSense()
		reverse.SetInputConnection(contourFilter.GetOutputPort())
		reverse.ReverseCellsOn()
		reverse.ReverseNormalsOn()
		reverse.Update()

		outputPolyData=reverse.GetOutput()

		newSurf = self.transform_back( points, reverse.GetOutput());

		pts2=np.zeros((newSurf.GetNumberOfPoints(),3))
		for i in range(0,newSurf.GetNumberOfPoints()):
			pts2[i,:]=newSurf.GetPoint(i)

		r2,t2,z2 = rec2cyl(pts2[:,0],pts2[:,1],pts2[:,2])
		im2=getGeomImperfection(r2,z2,np.mean(r2))
		self.paint.setValue(np.min(im2))
		self.paint.setValue(np.max(im2))

		for i in range(0,newSurf.GetNumberOfPoints()):
			colors.InsertNextTupleValue(self.paint.getRGB(im2[i]))

		newSurf.GetPointData().SetScalars(colors );
		self.outputs.append(newSurf)

		mapper = vtk.vtkPolyDataMapper();
		mapper.InterpolateScalarsBeforeMappingOn()
		mapper.SetInputConnection(newSurf.GetProducerPort())
		mapper.SetScalarModeToUsePointData()
		mapper.ScalarVisibilityOn();

		surfaceActor = vtk.vtkActor();
		surfaceActor.SetMapper(mapper);

		self.ren.AddActor(surfaceActor);

	def addVTPFile(self,fname):
		reader=vtk.vtkXMLPolyDataReader()
		reader.SetFileName(fname)
		mapper = vtk.vtkPolyDataMapper();
		mapper.InterpolateScalarsBeforeMappingOn()
		mapper.SetInputConnection(reader.GetOutputPort())
		mapper.SetScalarModeToUsePointData()
		mapper.ScalarVisibilityOn();

		surfaceActor = vtk.vtkActor();
		surfaceActor.SetMapper(mapper);

		self.ren.AddActor(surfaceActor);

	def addWidgets(self):
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

		ax=vtk.vtkAxesActor()
		ax.GetXAxisCaptionActor2D().GetProperty().SetColor(0,0,0)
		ax.GetYAxisCaptionActor2D().GetProperty().SetColor(0,0,0)
		ax.GetZAxisCaptionActor2D().GetProperty().SetColor(0,0,0)

		lut=vtk.vtkLookupTable()
		lut.SetHueRange( 0.66667, 0.0 )
		lut.SetSaturationRange (1.0, 1.0)
		lut.SetNumberOfColors(20)# len(self.plotables))
		lut.SetTableRange(self.paint.getMinValue(),self.paint.getMaxValue())
		lut.Build()

		self.ow=vtk.vtkOrientationMarkerWidget()
		self.scalar_bar = vtk.vtkScalarBarActor()
		self.scalar_bar.SetOrientationToHorizontal()
		self.scalar_bar.SetLookupTable(lut)
		self.scalar_bar.SetTitle("Imperfection value");
		self.scalar_bar.SetNumberOfLabels(11)

		self.scalar_bar_widget = vtk.vtkScalarBarWidget()

		textActor = vtk.vtkTextActor()
		textActor.GetTextProperty().SetFontSize ( 22 )
		textActor.SetPosition2( 100, 100 )
		textActor.SetInput(r'DESICOS VIEWER: '+r'Scaling: '+str(self.scalingFactor)+r' File:'+str(self.caption))
		textActor.GetTextProperty().SetColor ( 0.0,0.0,0.0 )
		
		if self.showXYPlane:
			self.ren.AddActor(plXYact)
		if self.showYZPlane:
			self.ren.AddActor(plYZact)
		if self.showZXPlane:
			self.ren.AddActor(plZXact)
		if self.showCaption:
			self.ren.AddActor2D( textActor )
		if self.showScalarBar:
			self.scalar_bar_widget.SetInteractor(self.iren)
			self.scalar_bar_widget.SetScalarBarActor(self.scalar_bar)
			self.scalar_bar_widget.On()
		if self.showAxes:
			self.ow.SetOrientationMarker(ax)
			self.ow.SetInteractor(self.iren)
#			self.ow.SetViewport( 0.0, 0.0, 0.4, 0.4 )
			self.ow.SetEnabled( 1 )
			self.ow.InteractiveOn()



	def transform_back(self,pt,pd):
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


