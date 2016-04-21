
from stochastic.strFact import *
import json



props0={}
props0['AZ']=0.
props0['AT']=0.
props0['tName']='TBlk'
props0['zName']='ZBlk'
props0['nBlkT']=200
props0['nBlkZ']=110
props0['scalingFactor']=0.02
props0['KT']=np.deg2rad(45.)
props0['KZ']=np.deg2rad(45.)
props0['nt']=400
props0['nz']=100

props1={}
props1['AZ']=0.2
props1['AT']=0.2
props1['tName']='TBlk'
props1['zName']='ZBlk'
props1['nBlkT']=200
props1['nBlkZ']=110
props1['scalingFactor']=0.02
props1['KT']=np.deg2rad(45.)
props1['KZ']=np.deg2rad(45.)
props1['nt']=40
props1['nz']=10

props2={}
props2['AZ']=1.0
props2['AT']=1.0
props2['tName']='TBlk'
props2['zName']='ZBlk'
props2['nBlkT']=200
props2['nBlkZ']=110
props2['scalingFactor']=0.02
props2['KT']=np.deg2rad(70.)
props2['KZ']=np.deg2rad(85.)
props2['nt']=20
props2['nz']=10

props3={}
props3['AZ']=0.
props3['AT']=0.3
props3['tName']='TBlk'
props3['zName']='ZBlk'
props3['nBlkT']=200
props3['nBlkZ']=110
props3['scalingFactor']=0.02
props3['KT']=np.deg2rad(65.)
props3['KZ']=np.deg2rad(85.)
props3['nt']=400
props3['nz']=100

props4={}
props4['AZ']=3.0
props4['AT']=3.0
props4['tName']='TBlk'
props4['zName']='ZBlk'
props4['nBlkT']=20
props4['nBlkZ']=11
props4['scalingFactor']=1.0
props4['KT']=np.deg2rad(30.)
props4['KZ']=np.deg2rad(30.)
props4['nt']=40
props4['nz']=10

propLAY1STRIP1={}
propLAY1STRIP1['AZ']=.0
propLAY1STRIP1['AT']=1.0
propLAY1STRIP1['tName']='TStrip'
propLAY1STRIP1['scalingFactor']=.02
propLAY1STRIP1['KT']=np.deg2rad(24.)
propLAY1STRIP1['t0']=np.deg2rad(0.)
propLAY1STRIP1['t1']=np.deg2rad(88.)
propLAY1STRIP2={}
propLAY1STRIP2['AZ']=0.0
propLAY1STRIP2['AT']=1.0
propLAY1STRIP2['tName']='TStrip'
propLAY1STRIP2['scalingFactor']=.02
propLAY1STRIP2['KT']=np.deg2rad(24.)
propLAY1STRIP2['t0']=np.deg2rad(90.)
propLAY1STRIP2['t1']=np.deg2rad(178.)
propLAY1STRIP3={}
propLAY1STRIP3['AZ']=0.0
propLAY1STRIP3['AT']=1.0
propLAY1STRIP3['tName']='TStrip'
propLAY1STRIP3['scalingFactor']=.02
propLAY1STRIP3['KT']=np.deg2rad(24.)
propLAY1STRIP3['t0']=np.deg2rad(180.)
propLAY1STRIP3['t1']=np.deg2rad(268.)
propLAY1STRIP4={}
propLAY1STRIP4['AZ']=0.0
propLAY1STRIP4['AT']=1.0
propLAY1STRIP4['tName']='TStrip'
propLAY1STRIP4['scalingFactor']=.02
propLAY1STRIP4['KT']=np.deg2rad(24.)
propLAY1STRIP4['t0']=np.deg2rad(270.)
propLAY1STRIP4['t1']=np.deg2rad(358.)

propLAY2STRIP1={}
propLAY2STRIP1['AZ']=.0
propLAY2STRIP1['AT']=1.0
propLAY2STRIP1['tName']='TStrip'
propLAY2STRIP1['scalingFactor']=.02
propLAY2STRIP1['KT']=np.deg2rad(-24.)
propLAY2STRIP1['t0']=np.deg2rad(-45.)
propLAY2STRIP1['t1']=np.deg2rad(43.)
propLAY2STRIP2={}
propLAY2STRIP2['AZ']=0.0
propLAY2STRIP2['AT']=1.0
propLAY2STRIP2['tName']='TStrip'
propLAY2STRIP2['scalingFactor']=.02
propLAY2STRIP2['KT']=np.deg2rad(-24.)
propLAY2STRIP2['t0']=np.deg2rad(45.)
propLAY2STRIP2['t1']=np.deg2rad(133.)
propLAY2STRIP3={}
propLAY2STRIP3['AZ']=0.0
propLAY2STRIP3['AT']=1.0
propLAY2STRIP3['tName']='TStrip'
propLAY2STRIP3['scalingFactor']=.02
propLAY2STRIP3['KT']=np.deg2rad(-24.)
propLAY2STRIP3['t0']=np.deg2rad(135.)
propLAY2STRIP3['t1']=np.deg2rad(223.)
propLAY2STRIP4={}
propLAY2STRIP4['AZ']=0.0
propLAY2STRIP4['AT']=1.0
propLAY2STRIP4['tName']='TStrip'
propLAY2STRIP4['scalingFactor']=.02
propLAY2STRIP4['KT']=np.deg2rad(-24.)
propLAY2STRIP4['t0']=np.deg2rad(225.)
propLAY2STRIP4['t1']=np.deg2rad(313.)


propLAY3STRIP1={}
propLAY3STRIP1['AZ']=.0
propLAY3STRIP1['AT']=1.0
propLAY3STRIP1['tName']='TStrip'
propLAY3STRIP1['scalingFactor']=.02
propLAY3STRIP1['KT']=np.deg2rad(41.)
propLAY3STRIP1['t0']=np.deg2rad(30.)
propLAY3STRIP1['t1']=np.deg2rad(121.)
propLAY3STRIP2={}
propLAY3STRIP2['AZ']=0.0
propLAY3STRIP2['AT']=1.0
propLAY3STRIP2['tName']='TStrip'
propLAY3STRIP2['scalingFactor']=.02
propLAY3STRIP2['KT']=np.deg2rad(40.5)
propLAY3STRIP2['t0']=np.deg2rad(120.)
propLAY3STRIP2['t1']=np.deg2rad(206.)
propLAY3STRIP3={}
propLAY3STRIP3['AZ']=0.0
propLAY3STRIP3['AT']=1.0
propLAY3STRIP3['tName']='TStrip'
propLAY3STRIP3['scalingFactor']=.02
propLAY3STRIP3['KT']=np.deg2rad(40.5)
propLAY3STRIP3['t0']=np.deg2rad(210.)
propLAY3STRIP3['t1']=np.deg2rad(295.)
propLAY3STRIP4={}
propLAY3STRIP4['AZ']=0.0
propLAY3STRIP4['AT']=1.0
propLAY3STRIP4['tName']='TStrip'
propLAY3STRIP4['scalingFactor']=.02
propLAY3STRIP4['KT']=np.deg2rad(41.)
propLAY3STRIP4['t0']=np.deg2rad(300.)
propLAY3STRIP4['t1']=np.deg2rad(390.)


propLAY4STRIP1={}
propLAY4STRIP1['AZ']=.0
propLAY4STRIP1['AT']=1.0
propLAY4STRIP1['tName']='TStrip'
propLAY4STRIP1['scalingFactor']=.02
propLAY4STRIP1['KT']=np.deg2rad(-41.)
propLAY4STRIP1['t0']=np.deg2rad(10.)
propLAY4STRIP1['t1']=np.deg2rad(98.)
propLAY4STRIP2={}
propLAY4STRIP2['AZ']=0.0
propLAY4STRIP2['AT']=1.0
propLAY4STRIP2['tName']='TStrip'
propLAY4STRIP2['scalingFactor']=.02
propLAY4STRIP2['KT']=np.deg2rad(-41.)
propLAY4STRIP2['t0']=np.deg2rad(100.)
propLAY4STRIP2['t1']=np.deg2rad(188.)
propLAY4STRIP3={}
propLAY4STRIP3['AZ']=0.0
propLAY4STRIP3['AT']=1.0
propLAY4STRIP3['tName']='TStrip'
propLAY4STRIP3['scalingFactor']=.02
propLAY4STRIP3['KT']=np.deg2rad(-41.)
propLAY4STRIP3['t0']=np.deg2rad(190.)
propLAY4STRIP3['t1']=np.deg2rad(278.)
propLAY4STRIP4={}
propLAY4STRIP4['AZ']=0.0
propLAY4STRIP4['AT']=1.0
propLAY4STRIP4['tName']='TStrip'
propLAY4STRIP4['scalingFactor']=.02
propLAY4STRIP4['KT']=np.deg2rad(-41.)
propLAY4STRIP4['t0']=np.deg2rad(280.)
propLAY4STRIP4['t1']=np.deg2rad(368.)

propOnes={}
propOnes['scalingFactor']=.02*4




snone=StructureWithLayers('none')
snone.addLayer('l1',props0)

sOnes08=StructureWithLayers('ones 0.8mm')
sOnes08.addLayer('l1',propOnes)

sr1=StructureWithLayers('example1')
sr1.addLayer('l1',props1)
sr1.addLayer('l2',props2)
sr1.addLayer('l3',props3)


sr2=StructureWithLayers('example2')
sr2.addLayer('l4',props4)

srd=StructureWithLayers('desicos1')
srd.addLayer('l1_1:+24deg',propLAY1STRIP1)
srd.addLayer('l1_2:+24deg',propLAY1STRIP2)
srd.addLayer('l1_3:+24deg',propLAY1STRIP3)
srd.addLayer('l1_4:+24deg',propLAY1STRIP4)

srd.addLayer('l2_1:-24deg',propLAY2STRIP1)
srd.addLayer('l2_2:-24deg',propLAY2STRIP2)
srd.addLayer('l2_3:-24deg',propLAY2STRIP3)
srd.addLayer('l2_4:-24deg',propLAY2STRIP4)

srd.addLayer('l3_1:+41deg',propLAY3STRIP1)
srd.addLayer('l3_2:+41deg',propLAY3STRIP2)
srd.addLayer('l3_3:+41deg',propLAY3STRIP3)
srd.addLayer('l3_4:+41deg',propLAY3STRIP4)

srd.addLayer('l4_1:-41deg',propLAY4STRIP1)
srd.addLayer('l4_2:-41deg',propLAY4STRIP2)
srd.addLayer('l4_3:-41deg',propLAY4STRIP3)
srd.addLayer('l4_4:-41deg',propLAY4STRIP4)




sm=StructureManager()
sm.addStructure(snone)
sm.addStructure(sr1)
sm.addStructure(sr2)
sm.addStructure(srd)
sm.addStructure(sOnes08)


