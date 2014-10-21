import numpy
import sympy
from sympy import sin, pi
# local modules
import mapy.model.properties.composite as composite
#
laminaprop = (142.5e3, 8.7e3, 0.28, 5.1e3, 5.1e3, 5.1e3, 273.15)
stack = [24.,-24.,41.,-41.]
plyts = [0.125 for i in stack]
R = 400
H = 800.
K = 5/6. # shear correction factor
SPL = 4.
SPLx = H / 2.
SPLy = numpy.pi * R
Nxx = -10.
Nyy = 0.
a = H
b = 2 * numpy.pi * R
n_max = 10
m_max = 10
#
# reading laminate
objL = composite.read_stack( stack = stack,
                             plyts = plyts,
                             laminaprop = laminaprop )
A = objL.A
A11 = A[0][0]
A12 = A[0][1]
A22 = A[1][1]
A16 = A[0][2]
A26 = A[1][2]
A66 = A[2][2]
B = objL.B
B11 = B[0][0]
B12 = B[0][1]
B22 = B[1][1]
B16 = B[0][2]
B26 = B[1][2]
B66 = B[2][2]
D = objL.D
D11 = D[0][0]
D12 = D[0][1]
D22 = D[1][1]
D16 = D[0][2]
D26 = D[1][2]
D66 = D[2][2]
A2 = objL.D
A44 = A2[0][0]
A45 = A2[0][1]
A55 = A2[1][1]
sympy.var('x,y')
# SS1 - simply supported at the 4 edges
# Navier solution Reddy page 380 :
# A16 = 0, A26 = 0, A45 = 0, B16 = 0, B26 = 0, D16 = 0, D26 = 0, I1 = 0
u0 = 0
v0 = 0
w0 = 0
phix = 0
phiy = 0
for n in range( n_max ):
    for m in range( m_max ):
        alpha = (m+1) * numpy.pi / a
        beta  = (n+1) * numpy.pi / b
        s11 = ( A11*alpha**2  + A66*beta**2 )
        s12 = ( A12 + A66 )*alpha*beta
        s14 = ( B11*alpha**2 + B66*beta**2 )
        s15 = ( B12 + B66 )*alpha*beta
        s22 = ( A66*alpha**2 + A22*beta**2 )
        s24 = s15
        s25 = ( B66*alpha**2 + B22*beta**2 )
        s33_1 = K * ( A55*alpha**2 + A44*beta**2 )
        s33_2 = Nxx*alpha**2 + Nyy*beta**2
        s34 = K * A55 * alpha
        s35 = K * A44 * beta
        s44 = ( D11*alpha**2 + D66*beta**2 + K*A55 )
        s45 = ( D12 + D66 )*alpha*beta
        s55 = ( D66*alpha**2 + D22*beta**2 + K*A44 )
        # + terms related to dynamic... here set to zero
        m11 = 0.
        m22 = 0.
        m33 = 0.
        m44 = 0.
        m55 = 0.
        #
        S = numpy.matrix( [ [s11, s12,            0., s14, s15],
                            [s12, s22,            0., s24, s25],
                            [ 0.,  0., s33_1 + s33_2, s34, s35],
                            [s14, s24,           s34, s44, s45],
                            [s15, s25,           s35, s45, s55] ] )
        Qnm = SPL * 4 * sin( pi*(m+1)*SPLx/a ) * sin( pi*(n+1)*SPLy/b ) / (a*b)
        Qmatrix = numpy.matrix( [ [  0. ],
                                  [  0. ],
                                  [ Qnm ],
                                  [  0. ],
                                  [  0. ] ] )
        coeffs = S.I * Qmatrix
        Umn, Vmn, Wmn, Xmn, Ymn = coeffs
        u0   += Umn * sin( alpha*x ) * sin( beta*y )
        v0   += Vmn * sin( alpha*x ) * sin( beta*y )
        w0   += Wmn * sin( alpha*x ) * sin( beta*y )
        phix += Xmn * sin( alpha*x ) * sin( beta*y )
        phiy += Ymn * sin( alpha*x ) * sin( beta*y )

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator
import matplotlib.pyplot as plt

fig = plt.figure()
ax = fig.gca(projection='3d')
num_x = 43
num_y = 43
xcalc = numpy.linspace( 0., a, num_x )
ycalc = numpy.linspace( 0., b, num_y)
xcalc, ycalc = numpy.meshgrid(xcalc, ycalc)
u0calc = numpy.zeros( [num_y, num_x] )
v0calc = numpy.zeros( [num_y, num_x] )
w0calc = numpy.zeros( [num_y, num_x] )
xnew   = numpy.zeros( [num_y, num_x] )
ynew   = numpy.zeros( [num_y, num_x] )
znew   = numpy.zeros( [num_y, num_x] )
for i in range(num_y):
    for j in range(num_x):
        u0calc[i][j] = u0.evalf( subs={ x:xcalc[i][j], y:ycalc[i][j] } )
        v0calc[i][j] = v0.evalf( subs={ x:xcalc[i][j], y:ycalc[i][j] } )
        w0calc[i][j] = w0.evalf( subs={ x:xcalc[i][j], y:ycalc[i][j] } )
        xnew[i][j] = xcalc[i][j] + u0calc[i][j]
        ynew[i][j] = ycalc[i][j] + v0calc[i][j]
        znew[i][j] = w0calc[i][j]

surf = ax.plot_surface(xnew, ynew, znew, rstride=1, cstride=1,
                       color='b')

ax.w_zaxis.set_major_locator(LinearLocator(6))

plt.show()


