import os
import __main__

import numpy as np
from numpy import sin, cos

import desicos.abaqus.geom as geom
import desicos.abaqus.coords as coords
from desicos.abaqus.constants import *
#

#TODO compatibility solution
# a better solution should be used with __getattr__, hasattr and so forth
def check_attribute(obj, attr, default=None):
    try:
        getattr(obj, attr)
    except:
        setattr(obj, attr, default)

#TODO end of compatibility solution

def add2list(lst, value, tol=TOL):
    '''
    Does more or less like the Python set(), bur with a tolerance associated
    '''
    append_check = True
    for v in lst:
        if abs(value - v) < tol:
            append_check = False
            break
    if append_check:
        lst.append(value)

def get_book_sheet(excel_name, sheet_name):
    from xlrd import open_workbook
    from xlutils.copy import copy
    if os.path.isfile(excel_name):
        rb = open_workbook(excel_name, formatting_info=True)
        sheet_names = [s.name for s in rb.sheets()]
        #rs = rb.sheet_by_index(0)
        book = copy(rb)
        sheet = book.get_sheet(0)
        count = -1
        while True:
            count += 1
            new_sheet_name = sheet_name + '_%02d' % count
            if not new_sheet_name in sheet_names:
                sheet = book.add_sheet(new_sheet_name)
                break
    else:
        from xlwt import Workbook
        book = Workbook()
        sheet = book.add_sheet(sheet_name + '_00')
    return book, sheet

def sample_array(ndarray, sample):
    lines = np.round((len(ndarray)-1)*np.random.random_sample(sample))
    lines.sort()
    new_shape = list(ndarray.shape)
    new_shape[0] = sample
    new_array = np.zeros(new_shape, dtype = ndarray.dtype)
    for i,line in enumerate(lines):
        new_array[ i ] = ndarray[ int(line) ]
    return new_array

def index_within_linspace(linspace, t):
    ''' Returns the index where the value fits better
    '''
    return np.absolute(np.asarray(linspace)-t).argmin()

def create_sketch_plane(cc, entity):
    for plane in cc.sketch_planes:
        if abs(plane.theta - entity.theta) < TOL:
            return plane
    part = cc.part
    x1, y1, z1 = coords.cyl2rec(1.05*cc.r, entity.theta,   0.)
    v1 = np.array([x1, y1, z1], dtype=FLOAT)
    x2, y2, z2 = coords.cyl2rec(1.05*cc.r2, entity.theta, cc.h)
    v2 = np.array([x2, y2, z2], dtype=FLOAT)
    v3 = np.cross(v2, v1)
    if abs(v3.max()) > abs(v3.min()):
        v3 = v3/v3.max() * cc.h/2.
    else:
        v3 = v3/abs(v3.min()) * cc.h/2.
    x3, y3, z3 = v2 + v3
    pt = part.DatumPointByCoordinate(coords = (x1, y1, z1))
    p1 = part.datums[ pt.id ]
    pt = part.DatumPointByCoordinate(coords = (x2, y2, z2))
    p2 = part.datums[ pt.id ]
    pt = part.DatumPointByCoordinate(coords = (x3, y3, z3))
    p3 = part.datums[ pt.id ]
    plane = geom.Plane()
    plane.p1 = p1
    plane.p2 = p2
    plane.p3 = p3
    plane.part = part
    plane.create()
    plane.theta = entity.theta
    cc.sketch_planes.append(plane)
    return plane

def find_fb_load(cczload):
    frmlen = len(cczload)
    fb_load = 0.
    found_fb_load = False
    for i in range(frmlen):
        zload = cczload[i]
        if abs(zload) < abs(fb_load):
            found_fb_load = True
            break
        if not found_fb_load:
            fb_load = zload
    return fb_load

def set_colors_ti(cc):
    from abaqusConstants import ON
    session = __main__.session
    viewport = session.viewports[ session.currentViewportName ]
    cmap = viewport.colorMappings['Set']
    viewport.setColor(colorMapping=cmap)
    viewport.enableMultipleColors()
    viewport.setColor(initialColor='#BDBDBD')
    keys = cc.part.sets.keys()
    names = [k for k in keys if k.find('Set_measured_imp_t') > -1]
    overrides = dict([[names[i],(True,COLORS[i],'Default',COLORS[i])]
                      for i in range(len(names))])
    dummylen = len(keys)-len(overrides)
    new_COLORS = tuple([COLORS[-1]]*dummylen + list(COLORS))
    session.autoColors.setValues(colors=new_COLORS)
    cmap.updateOverrides(overrides=overrides)
    viewport.partDisplay.setValues(mesh=ON)
    viewport.partDisplay.geometryOptions.setValues(referenceRepresentation=ON)
    viewport.disableMultipleColors()

def printLBmodes():
    from abaqusConstants import DPI_1200,EXTRA_FINE,OFF,PNG
    session = __main__.session
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

def remove_special_characters(input_str):
    output_str = input_str.replace('/','_')
    output_str = output_str.replace(' ','_')
    others = ['$','{','}','|','!','%','&','(',')','=','?','+','*',
              ':',';',',','[',']','"']
    for other in others:
        output_str = output_str.replace(other,'')
    output_str = output_str.replace("'","")
    return output_str

def calc_elem_cg(elem):
    coords = np.array([0.,0.,0.,0.], dtype=FLOAT)
    nodes = elem.getNodes()
    for node in nodes:
        coords[:3] += node.coordinates
    coords[:3] /= float(len(nodes))
    coords[3] = elem.label
    return coords

def vec_calc_elem_cg(elements):
    vec_tmp = np.vectorize(calc_elem_cg, otypes=[object])
    return  np.array(tuple(vec_tmp(elements)), dtype=FLOAT)



def func_sin_cos(n_terms=10):
    guess = np.array(range(1,2*n_terms+2))
    n_terms += 1
    s = 'lambda x,a00,'+','.join(['a%02d,b%02d' % (i,i) for i in range(1,n_terms)])\
                +': a00+' + '+'.join(['a%02d*sin(%d*x)+b%02d*cos(%d*x)' \
                                      % (i,i,i,i) for i in range(1,n_terms)])

    return eval(s), guess

def func_sin(n_terms=10):
    guess = np.array(range(1,n_terms+2))
    n_terms += 1
    s = 'lambda x,a00,'+','.join(['a%02d' % i for i in range(1,n_terms)])\
                +': a00+' + '+'.join(['a%02d*sin(%d*x)' \
                                      % (i,i) for i in range(1,n_terms)])

    return eval(s), guess

def func_cos(n_terms=10):
    guess = np.array(range(1,n_terms+2))
    n_terms += 1
    s = 'lambda x,a00,'+','.join(['a%02d' % i for i in range(1,n_terms)])\
                +': a00+' + '+'.join(['a%02d*cos(%d*x)' \
                                      % (i,i) for i in range(1,n_terms)])

    return eval(s), guess

def empirical_P1_isotropic(r, t, E, nu):
    '''
    taken from Wang et al. (2008). An empirical formula for the critical
    perturbation load
    '''
    if r/t <  300: print 'WARNING - r/t ratio smaller than 300'
    if r/t > 2000: print 'WARNING - r/t ratio bigger than 2000'
    if 0 < t and t < 0.8:
        return 0.81 * E*t**3 /(12*(1-nu**2)*r**0.8)
    elif  0.8 <= t:
        if t > 1.5: print 'WARNING - thickness beyond 1.5'
        return 0.69 * E*t**3 /(12*(1-nu**2)*r**0.8)

def calc_nasaKDF(mapy_laminate, r, r2=None, alphadeg=None):
    if alphadeg > 0. :
        rm = (r + r2)/2.
        req = rm/numpy.cos(alpharad)
    else:
        req = r
    Ex = mapy_laminate.A[0,0]
    Ey = mapy_laminate.A[1,1]
    Dx = mapy_laminate.D[0,0]
    Dy = mapy_laminate.D[1,1]
    teq = 3.4689* (Dx*Dy/(Ex*Ey))**0.25
    phi = 1/16. * (req/teq)**0.5
    return 1. - 0.901*(1-numpy.e**-phi)

def get_odbdisplay():
    session = __main__.session
    viewport = session.viewports[session.currentViewportName]
    try:
        name = viewport.odbDisplay.name
        return viewport.odbDisplay
    except:
        return None

def get_current_odb():
    session = __main__.session
    viewport = session.viewports[session.currentViewportName]
    odbdisplay = get_odbdisplay()
    if odbdisplay:
        return session.odbs[odbdisplay.name]
    else:
        return None

def get_current_step_name():
    odbdisplay = get_odbdisplay()
    if odbdisplay:
        return odbdisplay.fieldSteps[0][0]
    else:
        return None

def get_current_frame():
    odbdisplay = get_odbdisplay()
    if not odbdisplay:
        return None
    step_name = get_current_step_name()
    step_num, frame_num = odbdisplay.fieldFrame
    odb = get_current_odb()
    step = odb.steps[step_name]
    return step.frames[frame_num]



