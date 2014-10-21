import numpy
import sympy
from sympy import sin, pi
# local modules
import mapy.model.properties.composite as composite
#
laminaprop = (142.5e3  ,   8.7e3,  0.28,   5.1e3,   5.1e3,   5.1e3, 273.15)
stack = [24.,-24.,41.,-41.]
plyts = [0.125 for i in stack]
R = 400
H = 800.
K = 5/6. # shear correction factor
SPL = 4.
SPLx = H / 2.
SPLy = numpy.pi * 400.
Nxx = -10.
Nyy = 0.
a = H
b = 2 * numpy.pi * R
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
# simply supported
sympy.var('u0, v0, w0, phix, phiy')
sympy.var('alpha, x, y, beta')
# alpha = sympy.pi * m / a
# beta  = sympy.pi * n / b
n_max = 2
m_max = 2
#
Umn_list = []
Vmn_list = []
Wmn_list = []
Xmn_list = []
Ymn_list = []
# for CLPT make X = -w0x
#           and Y = -w0y
for n in range( n_max ):
    for m in range(m_max):
        Umn_list.append( 'U%d%d' % ((m+1),(n+1)) )
        Vmn_list.append( 'V%d%d' % ((m+1),(n+1)) )
        Wmn_list.append( 'W%d%d' % ((m+1),(n+1)) )
        Xmn_list.append( 'X%d%d' % ((m+1),(n+1)) )
        Ymn_list.append( 'Y%d%d' % ((m+1),(n+1)) )
sympy.var( ','.join( Umn_list )    )
sympy.var( ','.join( Vmn_list )    )
sympy.var( ','.join( Wmn_list )    )
sympy.var( ','.join( Xmn_list ) )
sympy.var( ','.join( Ymn_list ) )
#
u0 = 0
v0 = 0
w0 = 0
phix = 0
phiy = 0
q = 0
Qnm = {}
# SS1 boundary conditions see Reddy page 379
for n in range( n_max ):
    Qnm[n] = {}
    for m in range( m_max ):
        Qnm[n][m] = SPL * 4 * sin( pi*m*SPLx/a ) * sin( pi*n*SPLy/b ) / (a*b)
        u0   += eval(('U%d%d' % ((m+1),(n+1)))) * sin(pi*m*x/a)*sin(pi*n*y/b*y)
        v0   += eval(('V%d%d' % ((m+1),(n+1)))) * sin(pi*m*x/a)*sin(pi*n*y/b*y)
        w0   += eval(('W%d%d' % ((m+1),(n+1)))) * sin(pi*m*x/a)*sin(pi*n*y/b*y)
        phix += eval(('X%d%d' % ((m+1),(n+1)))) * sin(pi*m*x/a)*sin(pi*n*y/b*y)
        phiy += eval(('Y%d%d' % ((m+1),(n+1)))) * sin(pi*m*x/a)*sin(pi*n*y/b*y)
        q    += Qnm[n][m] * sin(pi*m*x/a)*sin(pi*n*y/b*y)
u0x  = u0.diff(x)
u0y  = u0.diff(y)
u0xx = u0x.diff(x)
u0xy = u0x.diff(y)
u0yy = u0y.diff(y)
v0x  = v0.diff(x)
v0y  = v0.diff(y)
v0xx = v0x.diff(x)
v0xy = v0x.diff(y)
v0yy = v0y.diff(y)
w0x  = w0.diff(x)
w0y  = w0.diff(y)
w0xx = w0x.diff(x)
w0xy = w0x.diff(y)
w0yy = w0y.diff(y)
phixx  = phix.diff(x)
phixy  = phix.diff(y)
phixxx = phixx.diff(x)
phixxy = phixx.diff(y)
phixyy = phixy.diff(y)
phiyx  = phiy.diff(x)
phiyy  = phiy.diff(y)
phiyxx = phiyx.diff(x)
phiyxy = phiyx.diff(y)
phiyyy = phiyy.diff(y)
#
# GENERAL EQUATIONS FSDT
#TODO
# eta
eta = 0
NL = 0 # non-linear
eq1 = A11*( u0xx + NL*w0x*w0xx ) + A12*( v0xy + NL*w0y*w0xy ) +\
      A16*( u0xy + v0xx + NL*w0xx*w0y + NL*w0x*w0xy ) +\
      B11*phixxx + B12*phiyxy + B16*( phixxy + phiyxx ) +\
      A16*( u0xy + NL*w0x*w0xy ) + A26*( v0yy + w0y*w0yy ) +\
      A66*( u0yy + v0xy + NL*w0xy*w0y + NL*w0x*w0yy ) +\
      B16*phixxy + B26*phiyyy + B66*( phixyy + phiyxy ) # + T, P terms

eq2 = A16*( u0xx + NL*w0x*w0xx ) + A26*( v0xy + NL*w0y*w0xy ) +\
      A66*( u0xy + v0xx + NL*w0xx*w0y + NL*w0x*w0xy ) +\
      B16*phixxx + B26*phiyxy + B66*( phixxy + phiyxx ) +\
      A12*( u0xy + NL*w0x*w0xy ) + A22*( v0yy + NL*w0y*w0yy ) +\
      A26*( u0yy + v0xy + NL*w0xy*w0y + NL*w0x*w0yy ) +\
      B12*phixxy + B22*phiyyy + B26*( phixyy + phiyxy ) # + T, P terms

eq3 = K*A55*( w0xx + phixx) + K*A45*( w0xy + phiyx) +\
      K*A45*( w0xy + phixy) + K*A44*( w0yy + phiyy) +\
      eta + q # + terms

eq4 = B11*( u0xx + NL*w0x*w0xx ) + B12*( v0xy + NL*w0y*w0xy ) +\
      B16*( u0xy + v0xx + NL*w0xx*w0y + NL*w0x*w0xy ) +\
      D11*phixxx + D12*phiyxy + D16*(phixxy + phiyxx) +\
      B16*( u0xy + NL*w0x*w0xy ) + B26*( v0yy + NL*w0y*w0yy ) +\
      B66*( u0yy + v0xy + NL*w0xy*w0y + NL*w0x*w0yy ) +\
      D16*phixxy + D26*phiyyy + D66*(phixyy + phiyxy) +\
      K*A55*( w0x + phix ) - K*A45*(w0y + phiy) # + T, P terms

eq5 = B16*( u0xx + NL*w0x*w0xx ) + B26*( v0xy + NL*w0y*w0xy ) +\
      B66*( u0xy + v0xx + NL*w0xx*w0y + NL*w0x*w0xy ) +\
      D16*phixxx + D26*phiyxy + D66*( phixxy + phiyxx ) +\
      B12*( u0xy + NL*w0x*w0xy ) + B22*( v0yy + NL*w0y*w0yy ) +\
      B26*( u0yy + v0xy + NL*w0xy*w0y + NL*w0x*w0yy ) +\
      D12*phixxy + D22*phiyyy + D26*( phixyy + phiyxy ) +\
      K*A45*( w0x + phix ) + K*A44*(w0y + phiy)
#
eqs = []
varlist = []
for n in range( n_max ):
    for m in range( m_max ):
        # varlist.append( eval(('U%d%d' % ((m+1),(n+1)) ) ) )
        # varlist.append( eval(('V%d%d' % ((m+1),(n+1)) ) ) )
        # varlist.append( eval(('W%d%d' % ((m+1),(n+1)) ) ) )
        # varlist.append( eval(('X%d%d' % ((m+1),(n+1)) ) ) )
        # varlist.append( eval(('Y%d%d' % ((m+1),(n+1)) ) ) )
        eqs.append( eq1 )
        eqs.append( eq2 )
        eqs.append( eq3 )
        eqs.append( eq4 )
        eqs.append( eq5 )
varlist.append( U22 )
varlist.append( V22 )
varlist.append( W22 )
varlist.append( X22 )
varlist.append( Y22 )
#ans = sympy.solve( eqs, varlist )


# Navier solution Reddy page 380 :
# A16 = 0, A26 = 0, A45 = 0, B16 = 0, B26 = 0, D16 = 0, D26 = 0, I1 = 0
# SS1 - simply supported in the 4 edges
u0 = 0
v0 = 0
w0 = 0
phix = 0
phiy = 0
n_max = 10
m_max = 10
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
num_x = 40
num_y = int( 2 * numpy.pi * R * num_x / H )
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
        Rlocal = R + 100*w0calc[i][j]
        xnew[i][j] = Rlocal * numpy.cos( ( ycalc[i][j] + v0calc[i][j] ) / R )
        ynew[i][j] = Rlocal * numpy.sin( ( ycalc[i][j] + v0calc[i][j] ) / R )
        znew[i][j] = xcalc[i][j] + u0calc[i][j]

surf = ax.plot_surface(xnew, ynew, znew,
                       rstride=1, cstride=1, color='b')

ax.w_zaxis.set_major_locator(LinearLocator(6))

plt.show()


