import os
from abaqusConstants import *
# local modules
import abaqus_functions
#
import __main__
session = __main__.session
myv = session.viewports[session.currentViewportName] 
session.graphicsOptions.setValues(backgroundStyle=SOLID, 
    backgroundColor='#FFFFFF')
vp = session.viewports[session.currentViewportName]
session.psOptions.setValues(logo=OFF,
            resolution=DPI_1200,
            shadingQuality=EXTRA_FINE)
session.printOptions.setValues( reduceColors=False )
def save_contour( cc, frame_num = None, sufix = 'change_sufix', closeODB=False):
    odb = cc.attach_results()
    prev = 0.
    if frame_num is None:
        for i in range( len(cc.zload) ):
            zload = cc.zload[i]
            if abs(zload) < abs(prev):
                break
            prev = zload
        incrementNumber = i-1
        for i, frame in enumerate( odb.steps[cc.step2Name].frames ):
            if frame.incrementNumber >= incrementNumber:
                frame_num = i
                incrementNumber = frame.incrementNumber
                break
        print 'Detected: incrementNumber', incrementNumber, 'frame_num', frame_num
        sufix = 'first_buckling'
    if frame_num is None: frame_num = -1
    else:
        frame_num = frame_num
        sufix = sufix
    myv.setValues(displayedObject=odb)
    try:
        myv.odbDisplay.setPrimaryVariable(
            variableLabel='UT', outputPosition=NODAL, refinement=(INVARIANT, 
            'Magnitude'), )
    except:
        myv.odbDisplay.setPrimaryVariable(
            variableLabel='U', outputPosition=NODAL, refinement=(INVARIANT, 
            'Magnitude'), )
    myv.odbDisplay.display.setValues( plotState=CONTOURS_ON_DEF )
    myv.odbDisplay.contourOptions.setValues( contourStyle=CONTINUOUS)
    myv.odbDisplay.basicOptions.setValues( curveRefinementLevel=EXTRA_FINE)
    myv.odbDisplay.setFrame( step=cc.step2Name, frame=frame_num)
    myv.restore()
    myv.view.setViewpoint(
                        viewVector     = (0, 0, 1), 
                        cameraUpVector = (0, 1, 0),)
    myv.setValues(
                origin = (0.,0.), 
                width  = 300,
                height = 300,)
    myv.view.setValues(
        width          = 800,
        height         = 800,
        nearPlane      = 2075.29,
        farPlane       = 2489.33,
        cameraPosition = (0, 0, 2356.81),
        cameraTarget   = (0, 0, 0),)
    contour_name = cc.jobname + '_' + sufix
    session.printToFile( fileName      = contour_name,
                         format        = PNG,
                         canvasObjects = (myv,))
    if closeODB: cc.detach_results( odb )
