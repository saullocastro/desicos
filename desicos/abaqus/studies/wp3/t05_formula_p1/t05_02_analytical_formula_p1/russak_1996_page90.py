import sympy
import numpy
def calc( n ):
    lim_inf = 0
    lim_sup = 2
    dx = float(lim_sup - lim_inf) / (n+1)
    x = numpy.linspace( lim_inf, lim_sup, n+2 )
    yinit = 0
    yfinal = 4
    ystr = ''
    eqstr = ''
    for i in range(n):
        ystr += 'y%02d,' % (i+1)
        eqstr += 'eq%02d,' % i
    sympy.var( ystr )
    sympy.var( eqstr )
    y0 = yinit
    y = [y0]
    eq = []
    for i in range(n):
        y.append( eval('y%02d' % (i+1)) )
        eq.append( eval('eq%02d' % i) )
    y.append( yfinal )
    for i in range(1,len(x)-1):
        eq[i-1] = 6*x[i]**2 - ( 2*(y[i+1]-y[i])/dx - 2*(y[i]-y[i-1])/dx)/dx
    ans = sympy.solve( eq, y[1:-1] )
    keys = ans.keys()
    keys.sort()
    values = [y0] + [ans[k] for k in keys] + [yfinal]
    return x, values

if __name__ == '__main__':
    import matplotlib.pyplot as pyplot
    for n in [1,2,3,4,5,10]:
        x,y = calc( n )
        pyplot.plot( x, y )
    pyplot.show()


