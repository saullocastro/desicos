import json
import logging
import copy
import os
import numpy as np

class ConeCylDB(object):
	def __init__(self,configFile='conecylDB.json'):
		self.entries={}
		self.paths={}
		self.path=''
		self.configFile=''
		try:
			fp=open(configFile,'r')
			fd=''
			for line in fp:
				fd+=line
			fp.close()
			jd=json.loads(fd)
			self.version=jd['conecylDB']
			self.files=jd['files']
			self.configFile=configFile
			self.path=os.path.dirname(configFile)
			logging.info('using conecylDB version: '+str(self.version))
		except:
			logging.warning(str(configFile)+' invalid')
		try:
			self.populate()
		except:
			logging.warning('Can`t populate')


	def update(self):
		try:
			fp=open(str(self.configFile),'w')
			fp.writelines(json.dumps({'conecylDB':self.version, 'files':self.files },indent=4))
			fp.close()
		except:
			logging.warning('Can not write to file: '+str(self.configFile))
			return
	

	def populate(self):
		for f in self.files.keys():
			path=os.path.dirname(os.path.abspath(self.configFile))
			curFile=path+'/'+self.files[f]
			self.entries[f]=ConeCylDBEntry(f)
			self.entries[f].setConfigFromFile(curFile)
			self.paths[f]=os.path.dirname(os.path.abspath(self.files[f]))

	def copy(self,oldName,newName):
		self.entries[newName]=copy.copy(self.entries[oldName])
		self.entries[newName].name=newName
		self.entries[newName].config['name']=newName
		oldConfigFile=self.entries[newName].configFile
		oldBasename=os.path.basename(oldConfigFile)
		newConfigFile=oldConfigFile.replace(oldBasename,newName+'.json')
		self.entries[newName].configFile=str(newConfigFile)
		self.entries[newName].update()
		self.files[newName]=os.path.relpath(newConfigFile,self.path)
		self.update()

	def getEntry(self,key):
		if key in self.entries.keys():
			return self.entries[key]
		else:
			return None

	def getEntryList(self):
		return self.entries.keys()


class ConeCylDBEntry(object):

	def __init__(self,name):
		self.name=name
		self.config={}
		self.configFile=''
		self.abspath=''

	def update(self):
		try:
			fp=open(str(self.configFile),'w')
			fp.writelines(json.dumps(self.config,indent=4))
			fp.close()
			
			self.setConfigFromFile(self.configFile)
		except:
			logging.warning('Can not write to file: '+str(self.configFile))
			return
	def getProperty(self,key):
		if key in self.config.keys():
			return self.config[key]
		else:
			logging.warning('Property: '+str(key)+' not found')
			return None

	def setProperty(self,key,val):
		self.config[key]=val

		
	def setConfigFromFile(self,configFile):
		try:
			fp=open(configFile,'r')
			fd=''
			for line in fp:
				fd+=line
			fp.close()
			jd=json.loads(fd)
			self.config=jd
			self.configFile=configFile
			self.abspath=os.path.dirname(os.path.abspath(configFile))
		except:
			logging.warning(str(configFile)+' invalid')
			return

# specific conecyl methods:
	def setGeometry(self,H,R,a):
		self.setProperty('H',H)
		self.setProperty('R',R)
		self.setProperty('alpha',a)

	def getGeometry(self):
		return (self.getProperty('H'),self.getProperty('R'),self.getProperty('alpha'))

	def getGeometricImperfection(self):
		inType=type(self.getProperty('imp_geom')) 
		if not inType in [unicode, str]:
			return self.getProperty('imp_geom')
		else:
			return np.loadtxt(self.abspath+'/'+self.getProperty('imp_geom'))
		
	
	def getThicknessImperfection(self):
		inType=type(self.getProperty('imp_thick')) 
		if not inType in [unicode, str]:
			return self.getProperty('imp_thick')
		else:
			return np.loadtxt(self.abspath+'/'+self.getProperty('imp_thick'))
			
	def setGeometricImperfection(self,data,name=None):
		if type(data) in [str,unicode]:
			self.setProperty('imp_geom',data)
		else:
			outPath=self.abspath+'/'+self.name
			if not os.path.exists(outPath):
				os.mkdir(outPath)
			outFile=outPath+'/'+self.name+'_imp_geom.txt'
			np.savetxt(outFile,data)
			self.setProperty('imp_geom',self.name+'/'+self.name+'_imp_geom.txt')
		self.update()
		
			
	def setThicknessImperfection(self,data,name=None):
		if type(data) in [str,unicode]:
			self.setProperty('imp_thick',data)
		else:
			outPath=self.abspath+'/'+self.name
			if not os.path.exists(outPath):
				os.mkdir(outPath)
			outFile=outPath+'/'+self.name+'_imp_thick.txt'
			np.savetxt(outFile,data)
			self.setProperty('imp_geom',self.name+'/'+self.name+'_imp_thick.txt')
		self.update()
	
















	
