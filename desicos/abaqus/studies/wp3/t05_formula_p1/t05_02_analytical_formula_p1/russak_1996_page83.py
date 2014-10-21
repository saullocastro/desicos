import sympy
sympy.var( 'y, x, c1' )
y = 1 + x + c1 * x * (1-x)
yx = y.diff( x )
F = yx**2 - y**2 - 2*x*y
I = sympy.integrate(F,(x,0,1))
dIdc1 = I.diff( c1 )
print dIdc1
