import numpy as np
class Parameter(object):
    def __init__(self):
        self.name = ''
        self.keys_default = ['a1','a3','d1','d2','d3','d4',
                                       'b1','b2','b3','b4',
                             'f_00','f_90','f_45','f_ang'   ]
        self.value = None
        self.fig = None
        self.functions = {}
        self.family = None
        self.fig = None
        self.mng = None
        self.constr_order =\
            ['a2','a4','a1','a3','d1','d3','d2','d4','b1','b2','b3','b4']
        self.constr = { 'a1':None, 'a2':None, 'a3':None, 'a4':None,
                        'd1':None, 'd2':None, 'd3':None, 'd4':None,
                        'b1':None, 'b2':None, 'b3':None, 'b4':None  }

    def calc_feasible_range( self ):
        ans_minv = -1.
        ans_maxv =  1.
        for key in self.constr_order:
            cons_v = self.constr[ key ]
            if cons_v <> None:
                minv,maxv = self.functions[ key ].calc_limits( cons_v )
                if minv > ans_minv:
                    ans_minv = minv
                if maxv < ans_maxv:
                    ans_maxv = maxv
        return ans_minv, ans_maxv

    def calc_constr_value( self, f ):
        minv, maxv = self.calc_feasible_range()
        ans = (f+1) * (minv-maxv)/2 + minv
        return ans

    def rebuild( self ):
        for func in self.functions.values():
            func.rebuild()

    def plot( self, keys = 'default',
                    savefig=True,
                    ext='png',
                    fit_plots=False ):
        import matplotlib.pyplot as plt
        if self.fig == None:
            self.fig = plt.figure()
        if self.family == None:
            self.fig.canvas.set_window_title('parameter_%s' % self.name)
        else:
            self.fig.canvas.set_window_title('%s_parameter_%s' \
                                             % (self.family.name, self.name) )
        if keys == 'default':
            keys = self.keys_default
        elif keys == 'all':
            keys = self.functions.keys()
        else:
            pass # user supplied list of keys
        for key in keys:
            if key <> self.name\
            and not key in self.functions.keys():
                keys.pop( keys.index(key) )
        nums = [1,4,9,16,25,36,49,64,81]
        for i in range( 1, len( nums ) ):
            num_1 = nums[ i-1 ]
            num   = nums[  i  ]
            if len( keys ) > num_1 and len( keys ) <= num:
                row = num**0.5
                col = num**0.5
                break
        keys.sort()
        for i in range( len( keys ) ):
            key = keys[i]
            if key == self.name:
                continue
            func = self.functions[ key ]
            func.subplot = self.fig.add_subplot( row, col, i+1 )
            func.subplot.set_xlabel( func.name )
            #func.subplot.set_xticklabels([])
            if func.name[:2] == 'f_':
                func.subplot.set_xlim(-0.1,1.1)
            else:
                func.subplot.set_xlim(-1.1,1.1)
            if self.name[:2] == 'f_':
                func.subplot.set_ylim(-0.1,1.1)
            else:
                func.subplot.set_ylim(-1.1,1.1)
            if fit_plots:
                func.fit_data()
                func.subplot.scatter( func.xfit, func.ymins,
                                      marker='.' )
                func.subplot.scatter( func.xfit, func.ymaxs,
                                      marker='.' )
                func.subplot.plot( func.xplot, func.yminplot )
                func.subplot.plot( func.xplot, func.ymaxplot )
            else:
                func.subplot.scatter( func.x, func.y,
                                      marker='.' )
        self.fig.show()
        self.mng = plt.get_current_fig_manager()
        self.mng.window.state('zoomed')
        self.fig.show()
        if savefig:
            if self.family == None:
                self.fig.savefig(r'c:\Temp\parameter_%s.%s' % (self.name, ext))
            else:
                self.fig.savefig(r'c:\Temp\%s_parameter_%s.%s' \
                                % ( self.family.name, self.name, ext))
            self.mng.window.state('withdrawn')
