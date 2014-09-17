from stochastic.imperfCC import *
from stochastic.filWin import FilterWindows2D
from stochastic.strFact import *
import logging
import json
#import time
import copy

class ImperfFactory(object):
    def __init__(self,conecylDBFile):
        self.conecylDBFile=conecylDBFile
        self.sm=StructureManager()
        self.sThick=SamplesCC(self.conecylDBFile)
        self.sMidS=SamplesCC(self.conecylDBFile)
        self.inputs=[]
        self.outputs=[]
        self.solveMSI=False
        self.solveTII=False
        try:
            self.setMaterialPatterns('materials.json')
        except:
            logging.warning('materials.json not found')

    def reset(self):
        self.sm=StructureManager()
        self.sThick=SamplesCC(self.conecylDBFile)
        self.sMidS=SamplesCC(self.conecylDBFile)
        self.inputs=[]
        self.outputs=[]
        self.solveMSI=False
        self.solveTII=False
        try:
            self.setMaterialPatterns('materials.json')
        except:
            logging.warning('materials.json not found')

    def setCCDB(self,fname):
        self.sMidS.setCCDB(fname)
        self.sMidS.ccdb.populate()
        self.sThick.setCCDB(fname)
        self.sThick.ccdb.populate()

    def setRadialSampling(self,val):
        self.sMidS.setRadialSampling(val)
        self.sThick.setRadialSampling(val)

    def setAxialSampling(self,val):
        self.sMidS.setAxialSampling(val)
        self.sThick.setAxialSampling(val)

    def getFilterList(self):
        return FilterWindows2D.filters.keys()

    def getOutputs(self):
        return self.outputs

    def setAmplitudeThreshold(self,val):
        if self.solveTII:
            self.sThick.setAmplitudeThreshold(val)
        if self.solveMSI:
            self.sMidS.setAmplitudeThreshold(val)
    def setFreqRng(self,xrng,yrng):
        self.sMidS.setFreqRng('x',xrng)
        self.sMidS.setFreqRng('y',yrng)
        self.sThick.setFreqRng('x',xrng)
        self.sThick.setFreqRng('y',yrng)

    def setMaterialPatterns(self,fname):
        fp=open(fname,'r')
        jd=''
        for line in fp:
            jd+=line
        fp.close()
        jlist=json.loads(jd)
        self.sm.addFromJSONFiles(jlist)


    def getMaterialPatternList(self):
        return self.sm.getStructureList()

    def applyMaterialPattern(self,name):
        factory=self.sm.getStructure(name)
        for key in factory.db.keys():
            fl=factory.getLayer(key)
            if self.solveTII:
                self.sThick.addSurfacePatternFactory(fl)
            if self.solveMSI:
                self.sMidS.addSurfacePatternFactory(fl)

    def compute(self):
        if self.solveTII:
            self.sThick.compute()
        if self.solveMSI:
            self.sMidS.compute()


    def setFilters(self,name):
        fil=('none',())
        if name == 'hamming':
            fil=('hamming',(0.53836,-0.46164,0.53836,-0.46164) )
        if fil == 'none':
            fil=('none',())
        if fil == 'trapezoid':
            fil=('trapezoid',(0.1,0.1))

        self.sThick.setFilter(fil[0],fil[1])
        self.sMidS.setFilter(fil[0],fil[1])
#        self.compute()

    def setScalingFactor(self,sf):
        self.sThick.scalingFactor=sf
        self.sMidS.scalingFactor=sf

    ### DESICOS-CONECYLDB BLOCK::::::::::::::::::
    def addInputsFromCCDB(self,inp):
        if type(inp) == list:
            self.inputs.extend(inp)
        if type(inp) == str:
            self.inputs.append(a)

#        self.sThick=SamplesCC()
#        self.sMidS=SamplesCC()

        for name in self.inputs:
            self.sThick.importFromCCDB(name,'thick')
            self.sMidS.importFromCCDB(name,'ms')

        if self.sMidS.getInputsCount() > 2:
            self.solveMSI = True
        if self.sThick.getInputsCount() > 2:
            self.solveTII = True

    def _putNewToCCDB(self,name):
        self.sThick.setOutputName(str(name))
        self.sMidS.setOutputName(str(name))

        self.sThick.compute()
        self.sMidS.compute()

        self.sThick.putNewSampleToCCDB()
        self.sMidS.putNewSampleToCCDB()

    def putListToCCDB(self,ll):
        for l in ll:
            self._putNewToCCDB(l)
            self.outputs.append(l)

    def putAutogenToCCDB(self,base,n):
        for i in range(0,n):
            aname=str(base+'_'+time.strftime("%d_%B_%Y_%H_%M_%S_UTC",time.gmtime()))
            self._putNewToCCDB(aname)
            self.outputs.append(aname)

    ### DESICOS-STOCHASTIC-STANDALONE BLOCK:::::::::::::::::::;
    def copyPropsFromCCDB(self,imp_name):
        self.sThick.copyPropsFromCCDB(imp_name)
        self.sMidS.copyPropsFromCCDB(imp_name)


    def addInputsFromTxts(self,H,RB,alpha,msList,tiList):
        self.txtListMS=msList
        self.txtListTI=tiList
        self.sThick.setImpType('thick')
        self.sMidS.setImpType('ms')
        if len(msList) > 2:
            for b in msList:
                try:
                    self.sMidS.importFromXYZ(np.loadtxt(b),H,RB,alpha)
                except:
                    pass
        if len(tiList) > 2:
            for b in tiList:
                try:
                    self.sThick.importFromXYZ(np.loadtxt(b),H,RB,alpha)
                except:
                    pass

        if self.sMidS.getInputsCount() > 2:
            self.solveMSI = True
        if self.sThick.getInputsCount() > 2:
            self.solveTII = True

    def _putNewToFolder(self,path,name):

        if self.solveMSI :
            self.sMidS.setOutputName(str(name)+'_inner_surf.txt')
            self.sMidS.compute()
            self.sMidS.putNewSampleToFolder(path)
        if self.solveTII:
            self.sThick.setOutputName(str(name)+'_thick.txt')
            self.sThick.compute()
            self.sThick.putNewSampleToFolder(path)



    def putListToFolder(self,path,ll):
        for l in ll:
            self._putNewToFolder(path,l)
            self.outputs.append(l)

    def putAutogenToFolder(self,path,name,n):
        for i in range(0,n):
            aname=str(name+'_'+time.strftime("%d_%B_%Y_%H_%M_%S_UTC",time.gmtime()))
            self._putNewToFolder(path,aname)
            self.outputs.append(aname)

