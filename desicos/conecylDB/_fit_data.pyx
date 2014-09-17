#cython: wraparound=False
#cython: boundscheck=False
#cython: cdivision=True
#cython: nonecheck=False
#cython: profile=False
#cython: infer_types=False
import numpy as np
cimport numpy as np

from cython.parallel import prange

ctypedef np.double_t cDOUBLE
DOUBLE = np.float64

ctypedef void *cftype(int size, int m0, int n0, int num,
                      double *zs, double *thetas, double *a) nogil

cdef extern from "math.h":
    double cos(double t) nogil
    double sin(double t) nogil

cdef double pi = 3.141592653589793

def fa(m0, n0, np.ndarray[cDOUBLE, ndim=1] zs,
              np.ndarray[cDOUBLE, ndim=1] thetas, funcnum):

    cdef np.ndarray[cDOUBLE, ndim=2] a
    cdef cftype *cf

    num = zs.shape[0]

    TOL = 1.e-3
    if abs(zs.min()) > TOL or abs(1 - zs.max()) > TOL:
        raise ValueError('The zs array must be normalized!')

    if funcnum==1:
        size = 2
        cf = &cf1
    elif funcnum==2:
        size = 2
        cf = &cf2
    elif funcnum==3:
        size = 4
        cf = &cf3

    a = np.zeros((num, size*n0*m0), DOUBLE)
    cf(size, m0, n0, num, &zs[0], &thetas[0], &a[0, 0])

    return a

cdef void *cf1(int size, int m0, int n0, int num,
               double *zs, double *thetas, double *a) nogil:
    cdef double z, theta
    cdef int l, i, j, col

    for l in prange(num, chunksize=num/20, num_threads=4, schedule='static'):
        theta = thetas[l]
        z = zs[l]
        for i in range(1, m0+1):
            for j in range(n0):
                col = (i-1)*size + j*m0*size
                a[l*(size*m0*n0) + (col+0)] = sin(i*pi*z)*sin(j*theta)
                a[l*(size*m0*n0) + (col+1)] = sin(i*pi*z)*cos(j*theta)

cdef void *cf2(int size, int m0, int n0, int num,
               double *zs, double *thetas, double *a) nogil:
    cdef double z, theta
    cdef int l, i, j, col

    for l in prange(num, chunksize=num/20, num_threads=4, schedule='static'):
        theta = thetas[l]
        z = zs[l]
        for i in range(m0):
            for j in range(n0):
                col = i*size + j*m0*size
                a[l*(size*m0*n0) + (col+0)] = cos(i*pi*z)*sin(j*theta)
                a[l*(size*m0*n0) + (col+1)] = cos(i*pi*z)*cos(j*theta)

cdef void *cf3(int size, int m0, int n0, int num,
               double *zs, double *thetas, double *a) nogil:
    cdef double z, theta
    cdef int l, i, j, col

    for l in prange(num, chunksize=num/20, num_threads=4, schedule='static'):
        theta = thetas[l]
        z = zs[l]
        for i in range(m0):
            for j in range(n0):
                col = i*size + j*m0*size
                a[l*(size*m0*n0) + (col+0)] = sin(i*pi*z)*sin(j*theta)
                a[l*(size*m0*n0) + (col+1)] = sin(i*pi*z)*cos(j*theta)
                a[l*(size*m0*n0) + (col+2)] = cos(i*pi*z)*sin(j*theta)
                a[l*(size*m0*n0) + (col+3)] = cos(i*pi*z)*cos(j*theta)

def fw0(int m0, int n0,
        np.ndarray[cDOUBLE, ndim=1] c0,
        np.ndarray[cDOUBLE, ndim=1] xs,
        np.ndarray[cDOUBLE, ndim=1] ts, funcnum):
    cdef int ix, i, j, col, size
    cdef double x, t, sinix, cosix, sinjt, cosjt, w0
    cdef np.ndarray[cDOUBLE, ndim=1] w0s
    w0s = np.zeros_like(xs)
    size = np.shape(xs)[0]

    TOL = 1.e-3
    if abs(xs.min()) > TOL or abs(1 - xs.max()) > TOL:
        raise ValueError('The xs array must be normalized!')

    if funcnum==1:
        for ix in range(size):
            x = xs[ix]
            t = ts[ix]
            w0 = 0
            for j in range(n0):
                sinjt = sin(j*t)
                cosjt = cos(j*t)
                for i in range(1, m0+1):
                    sinix = sin(i*pi*x)
                    col = (i-1)*2 + j*m0*2
                    w0 += c0[col+0]*sinix*sinjt
                    w0 += c0[col+1]*sinix*cosjt
            w0s[ix] = w0
    elif funcnum==2:
        for ix in range(size):
            x = xs[ix]
            t = ts[ix]
            w0 = 0
            for j in range(n0):
                sinjt = sin(j*t)
                cosjt = cos(j*t)
                for i in range(m0):
                    cosix = cos(i*pi*x)
                    col = i*2 + j*m0*2
                    w0 += c0[col+0]*cosix*sinjt
                    w0 += c0[col+1]*cosix*cosjt
            w0s[ix] = w0
    elif funcnum==3:
        for ix in range(size):
            x = xs[ix]
            t = ts[ix]
            w0 = 0
            for j in range(n0):
                sinjt = sin(j*t)
                cosjt = cos(j*t)
                for i in range(m0):
                    sinix = sin(i*pi*x)
                    cosix = cos(i*pi*x)
                    col = i*4 + j*m0*4
                    w0 += c0[col+0]*sinix*sinjt
                    w0 += c0[col+1]*sinix*cosjt
                    w0 += c0[col+2]*cosix*sinjt
                    w0 += c0[col+3]*cosix*cosjt
            w0s[ix] = w0

    return w0s
