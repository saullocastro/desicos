import numpy as np
class Function(object):
    def __init__(self):
        self.name = ''
        self.plot_interval = 40
        self.subplot = None
        self.x = []
        self.y = []
        self.xfit = []
        self.ymins = []
        self.ymaxs = []
        self.poly_min = None
        self.poly_max = None
        self.xplot = None
        self.yminplot = None
        self.ymaxplot = None

    def rebuild(self):
        pass

    def fit_data( self ):
        import lam_parameters._linear_intervals
        self.calc_ymins_ymaxs()
        self.poly_min = lam_parameters._linear_intervals.LinearIntervals()
        self.poly_min.calc_coeffs( self.xfit, self.ymins )
        self.poly_max = lam_parameters._linear_intervals.LinearIntervals()
        self.poly_max.calc_coeffs( self.xfit, self.ymaxs )
        use_xfit = False
        if not use_xfit:
            p = float(self.plot_interval)
            if self.name[:2] == 'f_':
                self.xplot = np.array([ i*1./p for i in range(p + 1) ])
            else:
                self.xplot = np.array([ i*1./p for i in range(-p, p + 1) ])
        else:
            self.xplot = self.xfit
        self.yminplot = self.poly_min.calc_y( self.xplot )
        self.ymaxplot = self.poly_max.calc_y( self.xplot )

    def calc_ymins_ymaxs( self ):
        ymin = {}
        ymax = {}
        for i in range( len(self.x) ):
            xi = self.x[i]
            import numpy as np
            yi = self.y[i]
            key = float('%2.6f' % xi)
            if key in ymin.keys():
                if yi < ymin[key]:
                    ymin[key] = yi
            else:
                ymin[key] = yi
            if key in ymax.keys():
                if yi > ymax[key]:
                    ymax[key] = yi
            else:
                ymax[key] = yi
        self.xfit = []
        self.ymins = []
        self.ymaxs = []
        sortk = [k for k in ymin.keys()]
        sortk.sort()
        for k in sortk:
            self.xfit.append( k )
            self.ymins.append( ymin[k] )
        sortk = [k for k in ymax.keys()]
        sortk.sort()
        for k in sortk:
            self.ymaxs.append( ymax[k] )

    def calc_limits(self, value):
        return self.poly_min.calc_y( value ),\
               self.poly_max.calc_y( value )
