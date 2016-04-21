#!/usr/bin/env python
import sys
sys.path.append( '../stochastic')
from  st_utils.coords import *
import vtk
import numpy as np
from scipy import interpolate
from vtk.util.colors import *


class DesicosViewer3D(object):

	def __init__(self):
		self.outputs=[]
		self.scalingFactor=1.0
		self.showCompass=True
		self.showAxes=True
		self.showScalarBar=True
		self.showCaption=True
		self.showXYPlane=True
		self.showYZPlane=True
		self.showZXPlane=True
		self.xlabel='x'
		self.ylabel='y'
		self.zlabel='z'
		self.xrange=None
		self.yrange=None
		self.zrange=None
		self.nbSize=80
		self.sampleSpacing=8.0
		self.caption=''
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
		self.close()


	def close(self):
		self.renWin.Finalize()
		self.iren.TerminateApp(); 
		del self.ren
		del self.renWin 
		del self.iren

	def setCaption(self,text):
		self.caption=text
		self.renWin.SetWindowName("DESICOS-viewer v0.1 " +str(text))

	def setScalingFactor(self,sf):
		self.scalingFactor=sf

	def setNeighborhoodSize(self,nbSize):
		self.nbSize=nbSize

	def setSampleSpacing(self,sampleSpacing):
		self.sampleSpacing=sampleSpacing

	def writeVTP(self,fname,i=0):
		writer=vtk.vtkXMLPolyDataWriter()
		writer.SetFileName(fname)
		writer.SetInput(self.outputs[i])
		writer.Write()

	def addCSVFile(self,fname,mode='folded',csvDelimiter=None):
		self.setCaption(r' File:'+str(fname))
		pts=np.loadtxt(fname,csvDelimiter)
				
		points = vtk.vtkPoints()
		r,t,z = rec2cyl(pts[:,0],pts[:,1],pts[:,2])
		im_g=getGeomImperfection(r,z,np.mean(r))

		if pts.shape[1] == 4:
			useThickImp=True
		else:
			useThickImp=False

		if useThickImp:
			im_t=pts[:,3]
		else:
			im_t=np.zeros(pts.shape[0])

		rid=r-im_g
		if mode == 'unfolded':
			tt=t*r.mean()
			rr=im_g*self.scalingFactor
			for i in range(0,pts.shape[0]):
				points.InsertPoint(i,tt[i],z[i],rr[i] )
		else:
			xx,yy,zz=cyl2rec(rid+im_g*self.scalingFactor,t,z)
			for i in range(0,pts.shape[0]):
				points.InsertPoint(i,xx[i],yy[i],zz[i] )
		
        	
		polydata = vtk.vtkPolyData()
		polydata.SetPoints(points)
		polydata.Update()

		if useThickImp:
			imps=im_t
		else:
			imps=im_g
#		imps=vtk.vtkFloatArray()
#		if useThickImp:
#			for i in range(0,polydata.GetNumberOfPoints()):
#				imps.InsertNextValue(im_t[i])
#		else:
#				imps.InsertNextValue(im_g[i])
#		polydata.GetPointData().SetScalars(imps);
#
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

				
		kDTree = vtk.vtkKdTreePointLocator()
		kDTree.SetDataSet(polydata)
		kDTree.BuildLocator()

		colors=vtk.vtkFloatArray()
			
		for i in range(0,len(pts2)):
			kid=kDTree.FindClosestPoint(pts2[i])
			colors.InsertNextValue(imps[kid])	


#		if mode == 'folded':
#				im2=getGeomImperfection(r2,z2,np.mean(r2))/self.scalingFactor
#
#		if mode == 'unfolded':
#			im2=pts2[:,2]/self.scalingFactor
#
#		colors=vtk.vtkFloatArray()
#		for i in range(0,newSurf.GetNumberOfPoints()):
#			colors.InsertNextValue(im2[i])

		newSurf.GetPointData().SetScalars(colors);
        
		self.scalarRange=colors.GetRange()
        
		self.lut=vtk.vtkLookupTable()
		self.lut.SetNumberOfTableValues(100)
		self.lut.SetTableRange(self.scalarRange)
		self.lut.SetHueRange(0.667, 0.0)
		self.lut.Build()

		
		self.resP=newSurf.GetProducerPort()
		self.colors=colors
		self.outputs.append(newSurf)

		mapper = vtk.vtkPolyDataMapper();
		mapper.SetLookupTable(self.lut)
		mapper.InterpolateScalarsBeforeMappingOn()
		mapper.SetInputConnection(newSurf.GetProducerPort())
		mapper.SetScalarModeToUsePointData()
		mapper.ScalarVisibilityOn();
		mapper.SetScalarRange(colors.GetRange())
		surfaceActor = vtk.vtkActor();
		surfaceActor.SetMapper(mapper);

		self.boundBox=newSurf.GetBounds()
		self.ren.AddActor(surfaceActor);

	def addArray2d(self,x,y,zz,mode='real'):
		if mode == 'square':
			xr=x.max()-x.min()
			yr=y.max()-y.min()
			xmul=1.0
			ymul=1.0
			if xr >= yr:
				ymul=xr/yr
			if xr <= yr:
				xmul=yr/xr
			x*=xmul
			y*=ymul
	
		points = vtk.vtkPoints();

		for i in range(y.shape[0]):
			for j in range(x.shape[0]):
				points.InsertNextPoint(x[j], y[i], zz[i][j]*self.scalingFactor);

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

		self.lut=vtk.vtkLookupTable()
		self.lut.SetNumberOfTableValues(100)
		self.lut.SetTableRange(minz, maxz)
		self.lut.SetHueRange(0.667, 0.0)
		self.lut.Build()

		colors=vtk.vtkFloatArray()
		for i in range(0,outputPolyData.GetNumberOfPoints()):
			colors.InsertNextValue(outputPolyData.GetPoint(i)[2])

		outputPolyData.GetPointData().SetScalars(colors);
		self.outputs.append(outputPolyData)

		mapper = vtk.vtkPolyDataMapper();
		mapper.SetLookupTable(self.lut)
		mapper.InterpolateScalarsBeforeMappingOn()
		mapper.SetInputConnection(outputPolyData.GetProducerPort())
		mapper.SetScalarModeToUsePointData()
		mapper.ScalarVisibilityOn();
		mapper.SetScalarRange(colors.GetRange())
		surfaceActor = vtk.vtkActor();
		surfaceActor.SetMapper(mapper);

		self.boundBox=bounds
		self.ren.AddActor(surfaceActor);

	def addVTPFile(self,fname):
		reader=vtk.vtkXMLPolyDataReader()
		reader.SetFileName(fname)
		reader.Update()

		self.boundBox=reader.GetOutput().GetBounds()
		self.scalarRange=reader.GetOutput().GetPointData().GetScalars().GetRange()
		self.lut=vtk.vtkLookupTable()
		self.lut.SetNumberOfTableValues(100)
		self.lut.SetTableRange(self.scalarRange)
		self.lut.SetHueRange(0.667, 0.0)
		self.lut.Build()
		mapper = vtk.vtkPolyDataMapper();
		mapper.SetLookupTable(self.lut)
#		mapper.InterpolateScalarsBeforeMappingOn()
		mapper.SetInputConnection(reader.GetOutputPort())
		mapper.SetScalarModeToUsePointData()
		mapper.ScalarVisibilityOn();
		mapper.SetScalarRange(self.scalarRange)
		surfaceActor = vtk.vtkActor();
		surfaceActor.SetMapper(mapper);

		self.ren.AddActor(surfaceActor);

	def addWidgets(self,opt=None):
		if opt is not None:
			if opt.has_key('caption'):
				self.caption=opt['caption']
			if opt.has_key('showAxes'):
				self.showAxes=opt['showAxes']
			if opt.has_key('showCompass'):
				self.showCompass=opt['showCompass']
			if opt.has_key('showScalarBar'):
				self.showScalarBar=opt['showScalarBar']
			if opt.has_key('showXYPlane'):
				self.showXYPlane=opt['showXYPlane']
			if opt.has_key('showYZPlane'):
				self.showYZPlane=opt['showYZPlane']
			if opt.has_key('showZXPlane'):
				self.showZXPlane=opt['showZXPlane']
			if opt.has_key('xlabel'):
				self.xlabel=opt['xlabel']
			if opt.has_key('ylabel'):
				self.ylabel=opt['ylabel']
			if opt.has_key('ylabel'):
				self.zlabel=opt['zlabel']
			if opt.has_key('xrange'):
				self.xrange=opt['xrange']
			if opt.has_key('yrange'):
				self.yrange=opt['yrange']
			if opt.has_key('zrange'):
				self.zrange=opt['zrange']


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

		xa=vtk.vtkAxisActor()
		xa.SetPoint1(0,0,0)
		xa.SetPoint2(1000,0,0)
		xa.SetRange((0,1000))
		xa.SetBounds(-1.0, 1000.0, -1.0, 1.0, -1.0, 1.0)

		self.ow=vtk.vtkOrientationMarkerWidget()
		textActor = vtk.vtkTextActor()
		textActor.GetTextProperty().SetFontSize ( 22 )
		textActor.SetPosition2( 100, 100 )
		textActor.SetInput(r'DESICOS VIEWER: '+str(self.caption)+r' Scaling: '+str(self.scalingFactor))
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
			self.scalar_bar = vtk.vtkScalarBarActor()
			self.scalar_bar.SetOrientationToHorizontal()
			self.scalar_bar.SetLookupTable(self.lut)
			self.scalar_bar.SetTitle("Imperfection value");
			self.scalar_bar.SetNumberOfLabels(11)
			self.scalar_bar.GetProperty().SetColor ( 0.0,0.0,0.0 )
			self.scalar_bar_widget = vtk.vtkScalarBarWidget()
			self.scalar_bar_widget.SetInteractor(self.iren)
			self.scalar_bar_widget.SetScalarBarActor(self.scalar_bar)
			self.scalar_bar_widget.On()
		if self.showCompass:
			self.ow.SetOrientationMarker(ax)
			self.ow.SetInteractor(self.iren)
#			self.ow.SetViewport( 0.0, 0.0, 0.4, 0.4 )
			self.ow.SetEnabled( 1 )
			self.ow.InteractiveOn()
		if self.showAxes:
			c=vtk.vtkCubeAxesActor()
			c.SetBounds(self.boundBox)
			c.SetXTitle(self.xlabel)
			c.SetYTitle(self.ylabel)
			c.SetZTitle(self.zlabel)

			if self.xrange is not None:
				c.SetXAxisRange(self.xrange)
			if self.yrange is not None:
				c.SetYAxisRange(self.yrange)
			if self.zrange is not None:
				c.SetZAxisRange(self.zrange)
			c.GetProperty().SetColor(0., 0., 0.)
			c.SetCamera(self.ren.GetActiveCamera())
			self.ren.AddActor(c)

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


