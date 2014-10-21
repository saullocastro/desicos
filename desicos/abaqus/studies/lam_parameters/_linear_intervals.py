import numpy as np
class LinearIntervals(object):
    def __init__(self):
        self.a0 = None
        self.a1 = None
        self.x  = None
        self.y  = None

    def calc_coeffs( self, x, y ):
        self.x = x
        self.y = y
        self.a0 = np.zeros(len(x)-1,dtype='float16')
        self.a1 = np.zeros(len(x)-1,dtype='float16')
        for i in range( len(x)-1 ):
            y1 = y[i]
            y2 = y[i+1]
            x1 = x[i]
            x2 = x[i+1]
            self.a1[i] = (y2-y1)/(x2-x1)
            self.a0[i] = (x2*y1-x1*y2)/(x2-x1)
    def aux_calc_x( self, x):
        if x < self.x[0]:
            return self.a0[0] + self.a1[0]*x
        for i in range( len(self.x) - 1 ):
            xi  = self.x[i]
            xi1 = self.x[i+1]
            if x >= xi and x < xi1:
                return self.a0[i] + self.a1[i]*x
                break
        if x >= self.x[-1]:
            return self.a0[-1] + self.a1[-1]*x

    def calc_y( self, x ):
        if x.__class__.__name__ == 'list'\
        or x.__class__.__name__.find('array') > -1:
            y = np.zeros(len(x),dtype='float16')
            for i in range(len(x)):
                xi   = x[i]
                y[i] = self.aux_calc_x( xi )
            return y
        else:
            return self.aux_calc_x( x )

