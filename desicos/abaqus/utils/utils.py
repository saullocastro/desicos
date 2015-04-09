import os

import numpy as np
from numpy import sin, cos

import geom
from desicos.abaqus.constants import *


def add2list(lst, value, tol=TOL):
    """Adds a value to a list if it doesn't exist within a given tolerance

    Performs more or less like the Python build-in ``set()``, but with a
    tolerance associated.

    Parameters
    ----------
    lst : list
        The input list.
    value : float
        The value to be compared with each element of the input list.

    Returns
    -------
    out : list
        Extended input list.

    """
    append_check = True
    for v in lst:
        if abs(value - v) < tol:
            append_check = False
            break
    if append_check:
        lst.append(value)


def get_book_sheet(excel_name, sheet_name):
    """Gets an Excel Worksheet from a given file name

    Parameters
    ----------
    excel_name : str
        The full path for the desired Excel file.
    sheet_name : str
        The name of the desired Excel Worksheet.

    Returns
    -------
    workbook, sheet : tuple
        A tuple with an ``xlwt.Workbook`` and an ``xlwt.Worksheet``
        object.

    """
    from desicos.xlrd import open_workbook
    from desicos.xlutils.copy import copy
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
        from desicos.xlwt import Workbook
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
        new_array[i] = ndarray[int(line)]

    return new_array


def index_within_linspace(a, value):
    """Returns the index where the value fits better

    Parameters
    ----------
    a : np.ndarray or list
        The values where the best index will be found.
    value : float
        The value to be compared with each value in ``a``.

    Returns
    -------
    i : int
        The index where ``value`` fits better in ``a``.

    """
    return np.absolute(np.asarray(a)-value).argmin()


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
    nodes = []
    for elem in elements:
        nodes += elem.getNodes()
    if len(nodes) == 0:
        return np.empty((0, 4), dtype=FLOAT)
    nodes_per_el = len(elem.getNodes())
    coords = np.array([node.coordinates for node in nodes])
    cgs = coords.reshape(-1, nodes_per_el, 3).mean(axis=1)
    labels = np.array([elem.label for elem in elements])
    return np.hstack((cgs, labels[:, None]))


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
    """
    taken from Wang et al. (2008). An empirical formula for the critical
    perturbation load
    """
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


def rec2cyl(x, y, z):
    thetarad = np.arctan2(y, x)
    r = np.sqrt((x**2 + y**2))
    theta = np.rad2deg(thetarad)

    return r, theta, z


def cyl2rec(r, theta, z):
    x = r * np.cos(np.deg2rad(theta))
    y = r * np.sin(np.deg2rad(theta))
    z = z

    return x, y, z


def cyl2rec_profi(array):
    return np.concatenate((array[0] * np.cos(np.deg2rad(array[1])),
                           array[0] * np.sin(np.deg2rad(array[1])),
                           array[2]))
