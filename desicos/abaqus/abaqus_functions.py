import numpy as np
import __main__

from abaqusConstants import *
from desicos.abaqus.constants import *

def static_step( model, name, previous, damping=False,
                 maxNumInc = None,
                 initialInc = None,
                 minInc = None,
                 maxInc = None,
                 damping_factor = None,
                 adaptiveDampingRatio = None):
    if initialInc == None:
        initialInc = INITIALINC
    if maxNumInc == None:
        maxNumInc = MAXNUMINC
    if minInc == None:
        minInc = MININC
    if maxInc == None:
        maxInc = MAXINC
    if damping_factor == None:
        damping_factor = DAMPING_FACTOR_value
    if adaptiveDampingRatio == None or adaptiveDampingRatio == True:
        adaptiveDampingRatio = ADAPTIVEDAMPINGRATIO
    elif adaptiveDampingRatio == 0  or adaptiveDampingRatio == False:
        adaptiveDampingRatio = 0
    # consistency checks
    if initialInc > maxInc:
        initialInc = maxInc
    #
    if not damping:
        model.StaticStep( name=name,
                          previous=previous,
                          description = '',
                          timePeriod = 1.,
                          nlgeom=ON,
                          stabilizationMethod = NONE,
                          timeIncrementationMethod = AUTOMATIC,
                          maxNumInc = maxNumInc,
                          initialInc = initialInc,
                          minInc = minInc,
                          maxInc = maxInc,
                          matrixSolver = DIRECT,
                          matrixStorage = SOLVER_DEFAULT,
                          amplitude = RAMP, # RAMP or STEP
                          extrapolation = PARABOLIC,
                          solutionTechnique = FULL_NEWTON,
                          adaptiveDampingRatio = adaptiveDampingRatio,
                          continueDampingFactors = OFF,
                        )
    elif damping:
        model.StaticStep( name=name,
                          previous=previous,
                          description = '',
                          timePeriod = 1.,
                          nlgeom=ON,
                          stabilizationMethod = DAMPING_FACTOR,
                          stabilizationMagnitude = damping_factor,
                          timeIncrementationMethod = AUTOMATIC,
                          maxNumInc = maxNumInc,
                          initialInc = initialInc,
                          minInc = minInc,
                          maxInc = maxInc,
                          matrixSolver = DIRECT,
                          matrixStorage = SOLVER_DEFAULT,
                          amplitude = RAMP, # RAMP or STEP
                          extrapolation = PARABOLIC,
                          solutionTechnique = FULL_NEWTON,
                          adaptiveDampingRatio = adaptiveDampingRatio,
                          continueDampingFactors = OFF,
                        )
def displacementBC( model, name, createStepName, region,
                    u1, u2, u3, ur1, ur2, ur3,
                    localCsys ):
    model.DisplacementBC( name=name,
                          createStepName=createStepName,
                          region = region,
                          u1=u1,
                          u2=u2,
                          u3=u3,
                          ur1=ur1,
                          ur2=ur2,
                          ur3=ur3,
                          amplitude = UNSET,
                          distributionType = UNIFORM,
                          fieldName = '',
                          localCsys = localCsys,
                          #buckleCase=BUCKLING_MODES
                        ) #NOT_APPLICABLE


def configure_session( session=None ):
    if session == None:
        session = __main__.session
    plot_names = session.xyDataObjects.keys()
    if not 'XYPlot-1' in session.xyPlots.keys():
        xyp = session.XYPlot('XYPlot-1')
    else:
        xyp = session.xyPlots['XYPlot-1']
    chartName = xyp.charts.keys()[0]
    chart = xyp.charts[chartName]
    tmp = session.xyDataObjects.keys()
    if len(tmp) == 0:
        return
    xy1 = session.xyDataObjects[ tmp[0] ]
    c1 = session.Curve(xyData=xy1)
    chart.setValues(curvesToPlot=(c1, ), )
    session.viewports['Viewport: 1'].setValues(displayedObject=xyp)

    chart = session.charts['Chart-1']
    chart.minorAxis1GridStyle.setValues( show  = True   )
    chart.majorAxis1GridStyle.setValues( show  = True   )
    chart.majorAxis1GridStyle.setValues( style = DASHED )
    chart.minorAxis2GridStyle.setValues( show  = True   )
    chart.majorAxis2GridStyle.setValues( show  = True   )
    chart.majorAxis2GridStyle.setValues( style = DASHED )
    chart.gridArea.style.setValues( fill = False )
    chart.legend.setValues( show = False ) # necessary to update legend values
    chart.legend.setValues( show = True  )
    chart.legend.area.setValues( inset = True )
    chart.legend.area.setValues( originOffset=(0.,0.) )
    chart.legend.area.style.setValues( fill = True )
    chart.legend.textStyle.setValues(
            font='-*-arial narrow-medium-r-normal-*-*-480-*-*-p-*-*-*')
    for name in plot_names:
        c = session.Curve(xyData=session.xyDataObjects[name])
        chart = session.xyPlots['XYPlot-1'].charts['Chart-1']
        chart.setValues(curvesToPlot=(c,))
        chart.fitCurves( fitAxes1=True, fitAxes2=True )
        curve = session.charts['Chart-1'].curves[name]
        curve.curveOptions.setValues(showSymbol = ON)
        curve.curveOptions.setValues(symbolSize = SMALL)
        curve.lineStyle.setValues( thickness = 1.6 )
        curve.symbolStyle.setValues( size   = 5,
                                     marker = HOLLOW_CIRCLE )
        ax = chart.axes1[0]
        ay = chart.axes2[0]
        ax.labelStyle.setValues(
            font  = '-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color = COLOR_BLACK )
        ax.titleStyle.setValues(
            font  = '-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color = COLOR_BLACK )
        ay.labelStyle.setValues(
            font  = '-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color = COLOR_BLACK )
        ay.titleStyle.setValues(
            font  = '-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color = COLOR_BLACK)
        ax.setValues(tickPlacement=OUTSIDE)
        ax.axisData.setValues(
                               labelFormat=DECIMAL,
                               labelNumDigits = 0,
                               minorTickCount = 4,
                             )
        ay.setValues(tickPlacement=OUTSIDE)
        ay.axisData.setValues(
                               labelFormat=DECIMAL,
                               labelNumDigits = 0,
                             )
        if ax.axisData.title.find('ispl') > -1:
            ax.axisData.setValues( labelNumDigits = 1 )
        if name.find('circumference') > -1:
            ax.axisData.setValues(
                                   tickMode       = INCREMENT,
                                   tickIncrement  = 20,
                                   minorTickCount = 0,
                                   minAutoCompute = False,
                                   minValue       = -180,
                                   maxAutoCompute = False,
                                   maxValue       =  185,
                                 )
        #
        if name.find('FI_HSNFCCRT') > -1 or name.find('FI_HSNFTCRT') > -1\
        or name.find('FI_HSNMCCRT') > -1 or name.find('FI_HSNMTCRT') > -1:
            ay.axisData.setValues( labelNumDigits = 1,
                                   minAutoCompute = False,
                                   minValue       = 0,
                                   maxAutoCompute = False,
                                   maxValue       = 2 )
            curve.lineStyle.setValues(
                                   thickness = 1.6,
                                   color     = COLOR_WHINE )
            curve.curveOptions.setValues(showSymbol = OFF)
            ay.titleStyle.setValues( color = COLOR_WHINE )
            ay.labelStyle.setValues( color = COLOR_WHINE )
        #
        if name.find('MS_HSNFCCRT') > -1 or name.find('MS_HSNFTCRT') > -1\
        or name.find('MS_HSNMCCRT') > -1 or name.find('MS_HSNMTCRT') > -1\
        or name.find('MS_MAX')      > -1 or name.find('MS_MIN')      > -1:
            ay.axisData.setValues( labelNumDigits = 1,
                                   minAutoCompute = False,
                                   minValue       = -0.5,
                                   maxAutoCompute = False,
                                   maxValue       =  1.0   )
            curve.lineStyle.setValues(
                                   thickness = 1.6,
                                   color     = COLOR_DARK_BLUE )
            curve.curveOptions.setValues(showSymbol = OFF)
            ay.titleStyle.setValues( color = COLOR_DARK_BLUE )
            ay.labelStyle.setValues( color = COLOR_DARK_BLUE )

def print_png( contour_name ):
    session = __main__.session
    viewport = session.viewports[ session.currentViewportName ]
    session.printToFile( fileName      = contour_name,
                         format        = PNG,
                         canvasObjects = (viewport,))

def set_default_view( cc ):
    odb = cc.attach_results()
    if not odb:
        print 'No .odb file found for %s!' % cc.jobname
        return
    dtm = odb.rootAssembly.datumCsyses[\
              'ASSEMBLY__T-INSTANCECYLINDER-CSYSCYLINDER']
    viewport = session.viewports[ session.currentViewportName ]
    viewport.odbDisplay.basicOptions.setValues(
        averageElementOutput=False, transformationType=USER_SPECIFIED,
        datumCsys=dtm)
    viewport.odbDisplay.setPrimaryVariable(
                        variableLabel='U',
                        outputPosition=NODAL,
                        refinement=(COMPONENT, 'U1'), )
    viewport.obasicOptions.setValues( averageElementOutput=True,
                      curveRefinementLevel=EXTRA_FINE )
    viewport.odbDisplay.commonOptions.setValues( visibleEdges=FREE,
                         deformationScaling=UNIFORM,
                         uniformScaleFactor=5 )
    viewport.odbDisplay.contourOptions.setValues( contourStyle=CONTINUOUS )
    viewport.restore()
    viewport.viewportAnnotationOptions.setValues( compass=OFF)
    viewport.viewportAnnotationOptions.setValues(triad=ON)
    viewport.viewportAnnotationOptions.setValues(title=OFF)
    viewport.viewportAnnotationOptions.setValues(state=OFF)
    viewport.viewportAnnotationOptions.setValues(legend=ON)
    viewport.viewportAnnotationOptions.setValues( legendTitle=OFF)
    viewport.viewportAnnotationOptions.setValues( legendBox=OFF)
    viewport.viewportAnnotationOptions.setValues( legendFont='-*-arial narrow-bold-r-normal-*-*-140-*-*-p-*-*-*')
    viewport.viewportAnnotationOptions.setValues( legendFont='-*-arial narrow-bold-r-normal-*-*-180-*-*-p-*-*-*')
    viewport.viewportAnnotationOptions.setValues( legendPosition=(1, 99))
    viewport.viewportAnnotationOptions.setValues( legendDecimalPlaces=1)
    viewport.setValues(
        origin=(0.0, -1.05833435058594),
        height=188.030563354492,
        width=203.452590942383,
        )
    viewport.view.setValues(
        viewOffsetX=-2.724,
        viewOffsetY=-52.6898,
        cameraUpVector=(-0.453666, -0.433365, 0.778705),
        nearPlane=1192.17,
        farPlane=2323.39,
        width=750.942,
        height=665.183,
        cameraPosition=(1236.44, 1079.87, 889.94),
        cameraTarget=( 27.3027, -54.758, 306.503),
        )

def edit_keywords( model, text, before_pattern=None, insert=False ):
    model.keywordBlock.synchVersions( storeNodesAndElements = False )
    sieBlocks = model.keywordBlock.sieBlocks
    if before_pattern == None:
        index = len( sieBlocks ) - 2
    else:
        index = None
        for i in range(len( sieBlocks )):
            sieBlock = sieBlocks[ i ]
            if sieBlock.find( before_pattern ) > -1:
                index = i-1
                break
        if index == None:
            print 'WARNING - *edit_keywords failed !'
            print '          %s pattern not found !' % before_pattern
            #TODO better error handling here...
            return False
    if insert:
        model.keywordBlock.insert( index, text )
    else:
        model.keywordBlock.replace( index, text )
    return True

def old_create_composite_layup( name,
                            stack,
                            ply_t,
                            region,
                            part,
                            part_local_csys_datum = None,
                            symmetric = False,
                          ):
        #CREATING A COMPOSITE LAYUP
        myLayup = part.CompositeLayup(\
                          name=name,
                          description='stack from inside to outside',
                          offsetType = MIDDLE_SURFACE,
                          symmetric = False,
                          thicknessAssignment = FROM_SECTION,
                          elementType = SHELL,
                        )
        myLayup.Section(\
                         preIntegrate = OFF,
                         integrationRule = SIMPSON,
                         thicknessType = UNIFORM,
                         poissonDefinition = DEFAULT,
                         temperature = GRADIENT,
                         useDensity = OFF,
                       )
        myLayup.ReferenceOrientation(\
                         orientationType = SYSTEM,
                         localCsys = part_local_csys_datum,
                         fieldName = '',
                         additionalRotationType = ROTATION_NONE,
                         angle = 0.,
                         additionalRotationField = '',
                         axis = AXIS_2,
                       )
        #CREATING ALL PLIES
        icount = 0
        jcount = 0
        for angle in stack:
            jcount += 1
            myLayup.CompositePly(\
                suppressed       = False,
                plyName          = 'face_' + str(icount) +\
                                   '_ply_' + str(jcount),
                region           = region,
                material         = 'carbonfiber',
                thicknessType    = SPECIFY_THICKNESS,
                thickness        = ply_t,
                orientationValue = angle,
                orientationType  = SPECIFY_ORIENT,
                numIntPoints     = 3 )

def create_composite_layup( name,
                            stack,
                            plyts,
                            mat_names,
                            region,
                            part,
                            part_local_csys_datum = None,
                            symmetric = False,
                            scaling_factor = 1.
                          ):
        #CREATING A COMPOSITE LAYUP
        myLayup = part.CompositeLayup(\
                          name=name,
                          description='stack from inside to outside',
                          offsetType = MIDDLE_SURFACE,
                          symmetric = False,
                          thicknessAssignment = FROM_SECTION,
                          elementType = SHELL,
                        )
        myLayup.Section(\
                         preIntegrate = OFF,
                         integrationRule = SIMPSON,
                         thicknessType = UNIFORM,
                         poissonDefinition = DEFAULT,
                         temperature = GRADIENT,
                         useDensity = OFF,
                       )
        myLayup.ReferenceOrientation(\
                         orientationType = SYSTEM,
                         localCsys = part_local_csys_datum,
                         fieldName = '',
                         additionalRotationType = ROTATION_NONE,
                         angle = 0.,
                         additionalRotationField = '',
                         axis = AXIS_2,
                       )
        #CREATING ALL PLIES
        numIntPoints = 3
        if len(stack) == 1:
            numIntPoints = 5
        for i, angle in enumerate(stack):
            plyt = plyts[i]
            mat_name = mat_names[i]
            myLayup.CompositePly(\
                suppressed       = False,
                plyName          = 'ply_%02d' % (i+1),
                region           = region,
                material         = mat_name,
                thicknessType    = SPECIFY_THICKNESS,
                thickness        = plyt * scaling_factor,
                orientationValue = angle,
                orientationType  = SPECIFY_ORIENT,
                numIntPoints     = numIntPoints )

def createDiscreteField( model, odb, step_name, frame_num ):
    u  = odb.steps[ step_name ].frames[ frame_num ].fieldOutputs['U']
    ur = odb.steps[ step_name ].frames[ frame_num ].fieldOutputs['UR']
    datas = []
    for u_value, ur_value in zip(u.values, ur.values):
        id = u_value.nodeLabel
        data = np.concatenate( (u_value.data, ur_value.data) )
        datas.append( [id, data] )
    datas.sort( key = lambda x: x[0] )
    list_ids = []
    list_dof_values = []
    for data in datas:
        list_ids += [ data[0] for i in xrange(6) ]
        for dof in xrange(1,7):
            list_dof_values += [ float(dof), data[1][dof-1] ]
    tuple_ids        = tuple( list_ids )
    tuple_dof_values = tuple( list_dof_values )
    model.DiscreteField( name='discreteField',
                         description='',
                         location = NODES,
                         fieldType = PRESCRIBEDCONDITION_DOF,
                         dataWidth = 2,
                         defaultValues= (0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                         data = ( ('', 2,
                                   tuple_ids,
                                   tuple_dof_values), ) )
