import numpy as np
import numpy.ma as ma
import sys
import os
import json
import logging
#sys.path.append( '../')
from st_utils.coords import *


class StructurePattern(object):
    def __init__(self):
        props={}
        props['AZ']=0.0
        props['AT']=0.0
        props['tName']='TBlk'
        props['zName']='ZBlk'
        props['nBlkT']=200
        props['nBlkZ']=110
        props['scalingFactor']=0.02
        props['KT']=np.deg2rad(45.)
        props['KZ']=np.deg2rad(45.)
        props['nt']=400
        props['nz']=100
        self.props=props
        for key in self.props.keys():
            self.__setattr__(key,self.props[key])

    def setProps(self):
        for key in self.props.keys():
            self.__setattr__(key,self.props[key])

    def setScalingFactor(self,sf):
        self.scalingFactor=sf

    def setGeometry(self,R,H,a):
        self.setProps()
        self.H=H
        self.R=R
        self.alpha=a

    def connectOutputArray(self,ar):
        self.setProps()
        self.nz, self.nt = ar.shape

    def setTPattern(self,**kwargs):
        if self.tName == 'TBlk':
            self.tpi= self._getPatternTBlk(self.nBlkT)

        if self.tName == 'TStrip':
            self.tpi= self._getPatternTStrip(self.t0,self.t1)

    def setZPattern(self,**kwargs):
        if self.zName == 'ZBlk':
            self.zpi= self._getPatternZBlk(self.nBlkZ)

        if self.tName == 'ZStrip':
            self.zpi= self._getPatternZStrip(self.z0,self.z1)



    def _getPatternTStrip(self,tsStart,tsStop):
        ntpat=800
        t0=np.mod(tsStart,2.0*np.pi)
        t1=np.mod(tsStop,2.0*np.pi)

        tpat=np.zeros((2,ntpat))
        tpat[0]=np.linspace(0,2.0*np.pi,tpat.shape[1])

        m1=ma.masked_greater_equal(tpat[0],t0).mask
        m2=ma.masked_less_equal(tpat[0],t1).mask

        mm=m1*m2
        if tsStop > 2.0*np.pi or tsStart<0.0:
            mm=m1+m2

#        tpat[1]=mm*(self.AT*np.random.random(ntpat))   #((self.AT)/2.0 + 0.5*self.AT*np.random.random(ntpat))

        st=self.AT*np.ones(ntpat)
        zeroKeys=np.random.randint(0,ntpat,70)
        st[zeroKeys]=0.3*self.AT
        tpat[1]=st*mm

        tpi=np.hstack((tpat,tpat,tpat))
        tpi[0,0:tpat.shape[1]]=tpat[0]-2*np.pi
        tpi[0,2*tpat.shape[1]:]=tpat[0]+2*np.pi
        return tpi

    def _getPatternZStrip(self,zsStart,zsStop):
        H=self.H
        nzpat=600

        t0=np.mod(zsStart,2.0*np.pi)
        t1=np.mod(zsStop,2.0*np.pi)


        zpat=np.zeros((2,nzpat))
        zpat[0]=np.linspace(0,H,zpat.shape[1])

        m1=ma.masked_greater_equal(zpat[0],zsStart).mask
        m2=ma.masked_less_equal(tpat[0],zsStop).mask
        mm=m1*m2
        zpat[1]=mm*(self.AZ/2.0 + 0.5*self.AZ*np.random.random(nzpat))

        zpi=np.hstack((zpat,zpat,zpat))

        zpi[0][0:zpat.shape[1]]=(zpat[0]-H)
        zpi[0][(2*zpat.shape[1]):]=(zpat[0]+H)
        return zpi



    def _getPatternTBlk(self,nBlkT):
        ntpat=800
        tpat=np.zeros((2,ntpat))
        tpat[0]=np.linspace(0,2.0*np.pi,tpat.shape[1])
        nBlk=nBlkT
        blkSize=ntpat/nBlk
        for i in range(0,nBlk):
            pos=i*blkSize
            tpat[1][pos:pos+blkSize/2]=self.AT

        tpi=np.hstack((tpat,tpat,tpat))
        tpi[0,0:tpat.shape[1]]=tpat[0]-2*np.pi
        tpi[0,2*tpat.shape[1]:]=tpat[0]+2*np.pi
        return tpi

    def _getPatternZBlk(self,nBlkZ):
        H=self.H
        nzpat=600
        zpat=np.zeros((2,nzpat))
        zpat[0]=np.linspace(0,H,zpat.shape[1])
        nBlk=nBlkZ
        blkSize=nzpat/nBlk
        for i in range(0,nBlk):
            pos=i*blkSize
            zpat[1][pos:pos+blkSize/2]=self.AZ

        zpi=np.hstack((zpat,zpat,zpat))

        zpi[0][0:zpat.shape[1]]=(zpat[0]-H)
        zpi[0][(2*zpat.shape[1]):]=(zpat[0]+H)
        return zpi

    def getPattern(self,mode='add'):
        self.setTPattern()
        self.setZPattern()

        tpi=self.tpi
        zpi=self.zpi

        t=np.linspace(0,2*np.pi,self.nt)
        z=np.linspace(0,self.H,self.nz)
        kz=np.linspace(0,np.tan(self.KZ)*self.H,self.nt)
        kt=np.linspace(0,self.KT,self.nz)

        imt=np.zeros((self.nz,self.nt))
        imz=np.zeros((self.nz,self.nt))

        for j in range(0,self.nt):
            ofs=np.mod(kz[j],self.H)
            zi=np.linspace(ofs,ofs+self.H,self.nz)
            imz[:,j]=np.interp(zi, zpi[0], zpi[1])

        for i in range(0,self.nz):
            ofs=np.mod(kt[i],2.0*np.pi)
            ti=np.linspace(ofs,ofs+2.0*np.pi,self.nt)
            imt[i,:]=np.interp(ti, tpi[0], tpi[1])
        if mode == 'add':
            im=imz+imt
        if mode == 'mul':
            im=imz*imt
        if mode == 'grt':
            im=imt
            for i in range(0,imz.shape[0]):
                for j in range(0,imz.shape[1]):
                    if im[i][j] <= 0.0:
                        if imz[i][j] < im[i][j]:
                            im[i][j]= imz[i][j]
                    if im[i][j] >= 0.0:
                        if imz[i][j] > im[i][j]:
                            im[i][j]= imz[i][j]
        return im*self.scalingFactor

class StructureWithLayers(object):

    def __init__(self,name):
        self.name=name
        self.db={}

    def addLayer(self,i,props):
        self.db[i]=StructurePattern()
        self.db[i].props=props
        self.db[i].setProps()

    def getLayer(self,key):
        return self.db[key]

class StructureManager(object):
    def __init__(self):
        self.db={}

    def addStructure(self,structure):
        self.db[structure.name]=structure

    def getStructureList(self):
        return self.db.keys()

    def getStructure(self,key):
        return self.db[key]

    def addFromJSONFiles(self,jsList):
        for s in jsList:
            try:
                fp=open(s,'r')
                jd=''
                for line in fp:
                    jd+=line
                fp.close()
                jlist=json.loads(jd)

                name=os.path.basename(s).split('.')[0]
                st=StructureWithLayers(name)
                nStrip=0
                for j in jlist:
                    nStrip+=1
                    st.addLayer('srtip'+str(nStrip),j)
                self.addStructure(st)
            except:
                logging.warning('Structure file '+str(s)+' not found')
