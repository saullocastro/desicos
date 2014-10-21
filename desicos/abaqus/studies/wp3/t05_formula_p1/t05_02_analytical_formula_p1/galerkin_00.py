import sympy
import numpy
def calc(trial_str, n):
    x = sympy.var( 'x' )
    nplot = 100
    lim_inf = 0
    lim_sup = 1
    phi0 = 0
    #
    cstr = ''
    ytrial = phi0
    for i in range(1,n+1):
        cstr += 'c%02d,' % i
    sympy.var( cstr )
    c = []
    for i in range(1,n+1):
        c.append( eval( 'c%02d' % i ) )
        ytrial += c[i-1] * eval( trial_str )
    ytrialx = ytrial.diff(x)
    ytrialxx = ytrialx.diff(x)
    Dapprox = ytrialxx + ytrial + 2*x*(1-x)
    integrals = [ phi0 ]
    for i in range(1,n+1):
        function = eval(trial_str) * Dapprox
        integral = sympy.integrate(function, (x, lim_inf, lim_sup))
        integrals.append( integral )
    ans = sympy.solve( integrals, c )
    keys = ans.keys()
    keys.sort()
    cvalues = [ ans[k] for k in keys ]

    x = numpy.linspace( lim_inf, lim_sup, nplot )
    yapprox = phi0
    for i in range(1,n+1):
        yapprox += cvalues[i-1] *eval( trial_str )
        trial_str = 'x**i*(x-1)**i'
    return x, yapprox

if __name__ == '__main__':
    import matplotlib.pyplot as pyplot
    trial_str = 'x**i*(x-1)**i'
    n = 5
    x, y = calc( trial_str, n )
    pyplot.plot( x, y )
    trial_str = 'x*(x-1)**i'
    n = 5
    x, y = calc( trial_str, n )
    pyplot.plot( x, y )
    trial_str = 'x**i*(x-1)'
    n = 2
    x, y = calc( trial_str, n )
    pyplot.plot( x, y )
    trial_str = 'x**i*(x-1)'
    n = 10
    x, y = calc( trial_str, n )
    pyplot.plot( x, y )
    pyplot.show()


