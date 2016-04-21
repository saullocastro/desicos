r"""
=========================================================
Utilities Abaqus (:mod:`desicos.abaqus.abaqus_functions`)
=========================================================

.. currentmodule:: desicos.abaqus.abaqus_functions

Includes all utilities functions that must be executed from Abaqus.

"""
import math

import numpy as np

from constants import (TOL, FLOAT, COLORS, COLOR_WHINE, COLOR_DARK_BLUE,
        COLOR_BLACK)


def configure_session():
    """Improve layout and colors of the current figures in visualization

    """
    from abaqus import session
    from abaqusConstants import (ON, OFF, SMALL, DASHED, OUTSIDE,
            HOLLOW_CIRCLE, DECIMAL, INCREMENT)

    plot_names=session.xyDataObjects.keys()
    if not 'XYPlot-1' in session.xyPlots.keys():
        xyp=session.XYPlot('XYPlot-1')
    else:
        xyp=session.xyPlots['XYPlot-1']
    chartName=xyp.charts.keys()[0]
    chart=xyp.charts[chartName]
    tmp=session.xyDataObjects.keys()
    if len(tmp)==0:
        return
    xy1=session.xyDataObjects[tmp[0]]
    c1=session.Curve(xyData=xy1)
    chart.setValues(curvesToPlot=(c1,),)
    session.viewports['Viewport: 1'].setValues(displayedObject=xyp)

    chart=session.charts['Chart-1']
    chart.minorAxis1GridStyle.setValues(show=True)
    chart.majorAxis1GridStyle.setValues(show=True)
    chart.majorAxis1GridStyle.setValues(style=DASHED)
    chart.minorAxis2GridStyle.setValues(show=True)
    chart.majorAxis2GridStyle.setValues(show=True)
    chart.majorAxis2GridStyle.setValues(style=DASHED)
    chart.gridArea.style.setValues(fill=False)
    chart.legend.setValues(show=False) # necessary to update legend values
    chart.legend.setValues(show=True)
    chart.legend.area.setValues(inset=True)
    chart.legend.area.setValues(originOffset=(0.,0.))
    chart.legend.area.style.setValues(fill=True)
    chart.legend.textStyle.setValues(
            font='-*-arial narrow-medium-r-normal-*-*-480-*-*-p-*-*-*')
    for name in plot_names:
        c=session.Curve(xyData=session.xyDataObjects[name])
        chart=session.xyPlots['XYPlot-1'].charts['Chart-1']
        chart.setValues(curvesToPlot=(c,))
        chart.fitCurves(fitAxes1=True, fitAxes2=True)
        curve=session.charts['Chart-1'].curves[name]
        curve.curveOptions.setValues(showSymbol=ON)
        curve.curveOptions.setValues(symbolSize=SMALL)
        curve.lineStyle.setValues(thickness=1.6)
        curve.symbolStyle.setValues(size=5,
                                     marker=HOLLOW_CIRCLE)
        ax=chart.axes1[0]
        ay=chart.axes2[0]
        ax.labelStyle.setValues(
            font='-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color=COLOR_BLACK)
        ax.titleStyle.setValues(
            font='-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color=COLOR_BLACK)
        ay.labelStyle.setValues(
            font='-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color=COLOR_BLACK)
        ay.titleStyle.setValues(
            font='-*-arial narrow-bold-r-normal-*-*-480-*-*-p-*-*-*',
            color=COLOR_BLACK)
        ax.setValues(tickPlacement=OUTSIDE)
        ax.axisData.setValues(labelFormat=DECIMAL,
                              labelNumDigits=0,
                              minorTickCount=4,)
        ay.setValues(tickPlacement=OUTSIDE)
        ay.axisData.setValues(labelFormat=DECIMAL,
                              labelNumDigits=0,)
        if ax.axisData.title.find('ispl')>-1:
            ax.axisData.setValues(labelNumDigits=1)
        if name.find('circumference') > -1:
            ax.axisData.setValues(tickMode=INCREMENT,
                                  tickIncrement=20,
                                  minorTickCount=0,
                                  minAutoCompute=False,
                                  minValue=-180,
                                  maxAutoCompute=False,
                                  maxValue=185)
        #
        if (name.find('FI_HSNFCCRT') > -1 or name.find('FI_HSNFTCRT') > -1
         or name.find('FI_HSNMCCRT') > -1 or name.find('FI_HSNMTCRT') > -1
         or name.find('FI_TSAIW')    > -1):
            ay.axisData.setValues(labelNumDigits=1,
                                  minAutoCompute=False,
                                  minValue=0,
                                  maxAutoCompute=False,
                                  maxValue=2)
            curve.lineStyle.setValues(thickness=1.6,
                                      color=COLOR_WHINE)
            curve.curveOptions.setValues(showSymbol=OFF)
            ay.titleStyle.setValues(color=COLOR_WHINE)
            ay.labelStyle.setValues(color=COLOR_WHINE)
        #
        if (name.find('MS_HSNFCCRT') > -1 or name.find('MS_HSNFTCRT') > -1
         or name.find('MS_HSNMCCRT') > -1 or name.find('MS_HSNMTCRT') > -1
         or name.find('MS_TSAIW')    > -1
         or name.find('MS_MAX')      > -1 or name.find('MS_MIN')      > -1):
            ay.axisData.setValues(labelNumDigits=1,
                                  minAutoCompute=False,
                                  minValue=-0.5,
                                  maxAutoCompute=False,
                                  maxValue=1.0)
            curve.lineStyle.setValues(thickness=1.6,
                                      color=COLOR_DARK_BLUE)
            curve.curveOptions.setValues(showSymbol=OFF)
            ay.titleStyle.setValues(color=COLOR_DARK_BLUE)
            ay.labelStyle.setValues(color=COLOR_DARK_BLUE)


def print_png(filename):
    """Print a png file from the current viewport

    Parameters
    ----------
    filename : str
        The name of the output png file.

    """
    from abaqus import session
    from abaqusConstants import PNG

    viewport=session.viewports[session.currentViewportName]
    session.printToFile(fileName=filename,
                         format=PNG,
                         canvasObjects=(viewport,))


def set_default_view(cc):
    """Set a default view in order to compare figures from different models

    Parameters
    ----------
    cc : :class:`.ConeCyl` object

    """
    from abaqusConstants import (USER_SPECIFIED, NODAL, COMPONENT, EXTRA_FINE,
            FREE, UNIFORM, CONTINUOUS, ON, OFF)
    odb=cc.attach_results()
    if not odb:
        print 'No .odb file found for %s!' % cc.jobname
        return
    dtm=odb.rootAssembly.datumCsyses[
              'ASSEMBLY__T-INSTANCECYLINDER-CSYSCYLINDER']
    viewport=session.viewports[session.currentViewportName]
    viewport.odbDisplay.basicOptions.setValues(
        averageElementOutput=False, transformationType=USER_SPECIFIED,
        datumCsys=dtm)
    viewport.odbDisplay.setPrimaryVariable(
                        variableLabel='U',
                        outputPosition=NODAL,
                        refinement=(COMPONENT, 'U1'),)
    viewport.obasicOptions.setValues(averageElementOutput=True,
                      curveRefinementLevel=EXTRA_FINE)
    viewport.odbDisplay.commonOptions.setValues(visibleEdges=FREE,
                         deformationScaling=UNIFORM,
                         uniformScaleFactor=5)
    viewport.odbDisplay.contourOptions.setValues(contourStyle=CONTINUOUS)
    viewport.restore()
    viewport.viewportAnnotationOptions.setValues(compass=OFF)
    viewport.viewportAnnotationOptions.setValues(triad=ON)
    viewport.viewportAnnotationOptions.setValues(title=OFF)
    viewport.viewportAnnotationOptions.setValues(state=OFF)
    viewport.viewportAnnotationOptions.setValues(legend=ON)
    viewport.viewportAnnotationOptions.setValues(legendTitle=OFF)
    viewport.viewportAnnotationOptions.setValues(legendBox=OFF)
    viewport.viewportAnnotationOptions.setValues(
            legendFont='-*-arial narrow-bold-r-normal-*-*-140-*-*-p-*-*-*')
    viewport.viewportAnnotationOptions.setValues(
            legendFont='-*-arial narrow-bold-r-normal-*-*-180-*-*-p-*-*-*')
    viewport.viewportAnnotationOptions.setValues(legendPosition=(1, 99))
    viewport.viewportAnnotationOptions.setValues(legendDecimalPlaces=1)
    viewport.setValues(origin=(0.0, -1.05833435058594),
                       height=188.030563354492,
                       width=203.452590942383)
    viewport.view.setValues(viewOffsetX=-2.724,
                            viewOffsetY=-52.6898,
                            cameraUpVector=(-0.453666, -0.433365, 0.778705),
                            nearPlane=1192.17,
                            farPlane=2323.39,
                            width=750.942,
                            height=665.183,
                            cameraPosition=(1236.44, 1079.87, 889.94),
                            cameraTarget=(27.3027, -54.758, 306.503))


def edit_keywords(mod, text, before_pattern=None, insert=False):
    """Edit the keywords to add commands not available in Abaqus CAE

    Parameters
    ----------
    mod : Abaqus Model object
        The model for which the keywords will be edited.
    text : str
        The text to be included.
    before_pattern : str, optional
        One pattern used to find where to put the given text.
    insert : bool, optional
        Insert the text instead of replacing it.

    """
    mod.keywordBlock.synchVersions(storeNodesAndElements=False)
    sieBlocks=mod.keywordBlock.sieBlocks
    if before_pattern is None:
        index=len(sieBlocks) - 2
    else:
        index=None
        for i in range(len(sieBlocks)):
            sieBlock=sieBlocks[i]
            if sieBlock.find(before_pattern) > -1:
                index=i-1
                break
        if index is None:
            print 'WARNING - *edit_keywords failed !'
            print '          %s pattern not found !' % before_pattern
            #TODO better error handling here...
    if insert:
        mod.keywordBlock.insert(index, text)
    else:
        mod.keywordBlock.replace(index, text)


def create_composite_layup(name, stack, plyts, mat_names, region, part,
                           part_csys, symmetric=False, scaling_factor=1.,
                           axis_normal=2):
    r"""Creates a composite layup

    Parameters
    ----------
    name : str
        Name of the new composite layup.
    stack : list
        Stacking sequence represented by a list of orientations in degress.
        The stacking sequence starts inwards a ends outwards. The 0 degree
        angle is along the axial direction and the angles are measured using
        the right-hand rule with the normal direction being normal to the
        shell surface pointing outwards.
    plyts : list
        List containing the ply thicknesses.
    mat_names : list
        List containing the material name for each ply.
    region : an Abaqus Region object
        The region consisting of geometric faces, where this laminate will be
        assigned to.
    part : an Abaqus part Object
        A part object where the layup will be created.
    part_csys : a valid Datum object
        The cylindrical coordinate system of the part object.
    symmetric : bool, optional
        A boolean telling whether the laminate is symmetric.
    scaling_factor : float, optional
        A scaling factor to be applied to each ply thickness. Used to apply
        thickness imperfection in some cases.
    axis_normal : int, optional
        Reference

    """
    from abaqusConstants import (MIDDLE_SURFACE, FROM_SECTION, SHELL, ON, OFF,
            DEFAULT, UNIFORM, SIMPSON, GRADIENT, SYSTEM, ROTATION_NONE,
            AXIS_1, AXIS_2, AXIS_3, SPECIFY_THICKNESS, SPECIFY_ORIENT,
            SINGLE_VALUE)
    myLayup=part.CompositeLayup(name=name,
                            description='stack from inside to outside',
                            offsetType=MIDDLE_SURFACE,
                            symmetric=False,
                            thicknessAssignment=FROM_SECTION,
                            elementType=SHELL)
    myLayup.Section(preIntegrate=OFF,
                    integrationRule=SIMPSON,
                    thicknessType=UNIFORM,
                    poissonDefinition=DEFAULT,
                    temperature=GRADIENT,
                    useDensity=OFF)
    if axis_normal == 1:
        axis = AXIS_1
    elif axis_normal == 2:
        axis = AXIS_2
    elif axis_normal == 3:
        axis = AXIS_3
    else:
        raise ValueError('Invalid value for `axis_normal`')
    myLayup.ReferenceOrientation(orientationType=SYSTEM,
                                 localCsys=part_csys,
                                 fieldName='',
                                 additionalRotationType=ROTATION_NONE,
                                 angle=0.,
                                 additionalRotationField='',
                                 axis=axis)
    #CREATING ALL PLIES
    numIntPoints=3
    if len(stack)==1:
        numIntPoints=5
    for i, angle in enumerate(stack):
        plyt=plyts[i]
        mat_name=mat_names[i]
        myLayup.CompositePly(suppressed=False,
                             plyName='ply_%02d' % (i+1),
                             region=region,
                             material=mat_name,
                             thicknessType=SPECIFY_THICKNESS,
                             thickness=plyt*scaling_factor,
                             orientationValue=angle,
                             orientationType=SPECIFY_ORIENT,
                             numIntPoints=numIntPoints)

def create_isotropic_section(name, mat_names, region, part, model,T,Sect_name,OFFTS):
    """Creates an isotropic section
   
    """

    from abaqusConstants import (MIDDLE_SURFACE, FROM_SECTION, SHELL, ON, OFF,
            DEFAULT, UNIFORM, SIMPSON, GRADIENT, SYSTEM, ROTATION_NONE,
            AXIS_1, AXIS_2, AXIS_3, SPECIFY_THICKNESS, SPECIFY_ORIENT,NO_IDEALIZATION,
            SINGLE_VALUE)

    model.HomogeneousShellSection(name=name, 
        preIntegrate=OFF, material=mat_names[0], 
        thicknessType=UNIFORM, thickness=T, thicknessField='', 
        idealization=NO_IDEALIZATION, poissonDefinition=DEFAULT, 
        thicknessModulus=None, temperature=GRADIENT, useDensity=OFF, 
        integrationRule=SIMPSON, numIntPts=5)

    region = region
    if OFFTS==0.0:
        part.SectionAssignment(region=region, sectionName=Sect_name, 
                               offset=OFFTS,offsetType=MIDDLE_SURFACE, 
                               offsetField='', 
                               thicknessAssignment=FROM_SECTION)
    else:
        part.SectionAssignment(region=region, sectionName=Sect_name, 
                               offset=OFFTS,offsetType=SINGLE_VALUE, 
                               offsetField='', 
                               thicknessAssignment=FROM_SECTION)

def modify_composite_layup(part, layup_name, modify_func):
    """Modify plies within a composite layup

    Directly modififying plies within a CompositeLayup is not possible, as
    the plies are read-only after creation. This function emulates modifying,
    by deleting and then re-creating plies, with modifications.

    Parameters
    ----------
    part : an Abaqus part object
        The part that the to-be-modified layup is attached to.
    layup_name : str
        Name of the layup that is to be modified.
    modify_func : function
        Function that will be called for each ply. It should take as arguments
        the ply index and a dictionary of keyword arguments. This dictionary
        contains all keyword arguments that would re-create the original ply,
        if passed to the ``CompositePly``-constructor. This function should
        should make the necessary changes this dictionary and then return it.
        The returned dictionary will then be used to create the new ply.

    """
    from abaqusConstants import SPECIFY_ORIENT, CSYS
    layup = part.compositeLayups[layup_name]

    ply_data = []
    STORE_PLY_ATTRS = ['additionalRotationField', 'additionalRotationType',
        'angle', 'axis', 'material', 'numIntPoints', 'orientation',
        'orientationType', 'orientationValue', 'plyName', 'region',
        'suppressed', 'thickness', 'thicknessType']
    for ply in layup.plies.values():
        ply_data.append(dict((attr, getattr(ply, attr)) for attr in STORE_PLY_ATTRS))
    layup.deletePlies()

    for i, kwargs in enumerate(ply_data):
        kwargs['region'] = part.sets[kwargs['region'][0]]
        if kwargs['orientationType'] != SPECIFY_ORIENT:
            kwargs.pop('orientationValue')
        if kwargs['orientationType'] != CSYS:
            kwargs.pop('orientation')
        kwargs = modify_func(i, kwargs)
        layup.CompositePly(**kwargs)


def createDiscreteField(mod, odb, step_name, frame_num):
    from abaqusConstants import (NODES, PRESCRIBEDCONDITION_DOF)
    u=odb.steps[step_name].frames[frame_num].fieldOutputs['U']
    ur=odb.steps[step_name].frames[frame_num].fieldOutputs['UR']
    datas=[]
    for u_value, ur_value in zip(u.values, ur.values):
        id=u_value.nodeLabel
        data=np.concatenate((u_value.data, ur_value.data))
        datas.append([id, data])
    datas.sort(key=lambda x: x[0])
    list_ids=[]
    list_dof_values=[]
    for data in datas:
        list_ids += [data[0] for i in xrange(6)]
        for dof in xrange(1,7):
            list_dof_values += [float(dof), data[1][dof-1]]
    tuple_ids=tuple(list_ids)
    tuple_dof_values=tuple(list_dof_values)
    mod.DiscreteField(name='discreteField',
                      description='',
                      location=NODES,
                      fieldType=PRESCRIBEDCONDITION_DOF,
                      dataWidth=2,
                      defaultValues=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
                      data=(('', 2, tuple_ids, tuple_dof_values),))


def create_sketch_plane(cc, entity):
    """Creates a sketch plane tangent to the shell surface

    Parameters
    ----------
    cc : :class:`.ConeCyl` object

    entity : object
        Any object with the attribute: ``thetadeg``, usually a
        :class:`.Imperfection`.

    Returns
    -------
    plane : :class:`.Plane` object

    """
    from abaqus import mdb

    part = mdb.models[cc.model_name].parts[cc.part_name_shell]
    for plane in cc.sketch_planes:
        if abs(plane.thetadeg - entity.thetadeg) < TOL:
            return plane
    x1, y1, z1 = utils.cyl2rec(1.05*cc.r, entity.thetadeg,   0.)
    v1 = np.array([x1, y1, z1], dtype=FLOAT)
    x2, y2, z2 = utils.cyl2rec(1.05*cc.r2, entity.thetadeg, cc.h)
    v2 = np.array([x2, y2, z2], dtype=FLOAT)
    v3 = np.cross(v2, v1)
    if abs(v3.max()) > abs(v3.min()):
        v3 = v3/v3.max() * cc.h/2.
    else:
        v3 = v3/abs(v3.min()) * cc.h/2.
    x3, y3, z3 = v2 + v3
    pt = part.DatumPointByCoordinate(coords=(x1, y1, z1))
    p1 = part.datums[pt.id]
    pt = part.DatumPointByCoordinate(coords=(x2, y2, z2))
    p2 = part.datums[pt.id]
    pt = part.DatumPointByCoordinate(coords=(x3, y3, z3))
    p3 = part.datums[pt.id]
    plane = geom.Plane()
    plane.p1 = p1
    plane.p2 = p2
    plane.p3 = p3
    plane.part = part
    plane.create()
    plane.thetadeg = entity.thetadeg
    cc.sketch_planes.append(plane)
    return plane


def set_colors_ti(cc):
    from abaqus import mdb, session
    from abaqusConstants import ON

    part = mdb.models[cc.model_name].parts[cc.part_name_shell]
    viewport = session.viewports[session.currentViewportName]
    if viewport.displayedObject is None:
        viewport.setValues(displayedObject=part)
    cmap = viewport.colorMappings['Set']
    viewport.setColor(colorMapping=cmap)
    viewport.enableMultipleColors()
    viewport.setColor(initialColor='#BDBDBD')
    keys = part.sets.keys()
    names = [k for k in keys if 'Set_measured_imp_t' in k]

    # If there are not enough colors for all thicknesses,
    # repeat the same color for multiple subsequent thickness sets
    repeat = int(math.ceil(max(len(names), 1.0) / float(len(COLORS))))
    overrides = dict((name, (True, COLORS[i//repeat], 'Default',
        COLORS[i//repeat])) for i, name in enumerate(names))
    dummylen = len(keys)-len(overrides)
    new_COLORS = tuple([COLORS[-1]]*dummylen + list(COLORS))
    session.autoColors.setValues(colors=new_COLORS)
    cmap.updateOverrides(overrides=overrides)

    keys_to_hide = set(keys) - set(names)
    overrides = dict([[k, (False, )] for k in keys_to_hide])
    cmap.updateOverrides(overrides=overrides)

    viewport.partDisplay.setValues(mesh=ON)
    viewport.partDisplay.geometryOptions.setValues(referenceRepresentation=ON)
    viewport.disableMultipleColors()


def printLBmodes():
    from abaqus import session
    from abaqusConstants import DPI_1200, EXTRA_FINE, OFF, PNG

    vp = session.viewports[session.currentViewportName]
    session.psOptions.setValues(logo=OFF,
                                resolution=DPI_1200,
                                shadingQuality=EXTRA_FINE)
    session.printOptions.setValues(reduceColors=False)
    for i in xrange(1,51):
        vp.odbDisplay.setFrame(step=0, frame=i)
        session.printToFile(fileName='mode %02d.png'%i,
                             format=PNG,
                             canvasObjects=(vp,))


def get_current_odbdisplay():
    from abaqus import session

    viewport = session.viewports[session.currentViewportName]
    try:
        name = viewport.odbDisplay.name
    except:
        return None

    return viewport.odbDisplay


def get_current_odb():
    from abaqus import session

    viewport = session.viewports[session.currentViewportName]
    odbdisplay = get_current_odbdisplay()
    if odbdisplay:
        return session.odbs[odbdisplay.name]
    else:
        return None


def get_current_step_name():
    odbdisplay = get_current_odbdisplay()
    if odbdisplay:
        index, frame_num = odbdisplay.fieldFrame
        return odbdisplay.fieldSteps[index][0]
    else:
        return None


def get_current_frame():
    odbdisplay = get_current_odbdisplay()
    if not odbdisplay:
        return None
    step_name = get_current_step_name()
    step_num, frame_num = odbdisplay.fieldFrame
    odb = get_current_odb()
    step = odb.steps[step_name]
    return step.frames[frame_num]
