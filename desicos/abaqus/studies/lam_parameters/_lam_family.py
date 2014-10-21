class LamFamily(object):
    def __init__( self ):
        self.family_name = ''
        self.num_plies = None
        self.angles = []
        self.lams = []
        self.params = {}
        self.param_names = [ 'a1','a2','a3','a4',
                             'b1','b2','b3','b4',
                             'd1','d2','d3','d4',
                             'f_00','f_90','f_ang',
                             'f_30','f_45','f_60'  ]
    def add_lam( self, lam ):
        lam.family = self
        self.lams.append( lam )

    def rebuild( self ):
        import lam_parameters._parameter
        import lam_parameters._function
        # parameters
        self.params = {}
        for param_name in self.param_names:
            param = lam_parameter._parameter.Parameter()
            param.family = self
            param.name = param_name
            for func_name in self.param_names:
                if func_name <> param_name:
                    func = lam_parameters._function.Function()
                    func.name = func_name
                    param.functions[ func_name ] = func
            self.params[ param_name ] = param
        # name
        self.name = 'LamFamily_'
        tmp = ''
        for theta in self.angles:
            self.name += '_%02d_' % theta
        self.name += 'num_plies_%02d' % self.num_plies

    def create_family( self, balanced=True, use_iterator=False ):
        self.rebuild()
        import lam_parameters.stack_calculator
        stacks = lam_parameters.stack_calculator.calc_stacks(
                    angles = self.angles,
                    num_plies = self.num_plies,
                    use_iterator = use_iterator )
        # validating stacks
        import lam_parameters._lam
        self.lams = []
        for stack in stacks:
            lam = lam_parameters._lam.Lam()
            lam.family = self
            lam.store_objL = False
            lam.create_stack( stack, balanced=balanced )
            if lam.valid:
                lam.calc_lam()
                self.add_lam( lam )
        for lam in self.lams:
            lam.calc_lam()
            for param_name, param in self.params.iteritems():
                yi = lam.params[ param_name ]
                for func_name, func in param.functions.iteritems():
                    xi = lam.params[ func_name ]
                    func.x.append( xi )
                    func.y.append( yi )

    def plot( self, keys='default',
              savefig=True,
              ext='png',
              fit_plots=False ):
        for param in self.params.values():
            param.plot( keys      = keys       ,
                        savefig   = savefig    ,
                        ext       = ext        ,
                        fit_plots = fit_plots  )

    def rebuild_params( self ):
        for param in self.params.values():
            param.rebuild()

    def load( self, path, append=False ):
        import copy
        import cPickle as pickle
        if not os.path.isfile( path ):
            print 'LamFamily pickle %s does not exist!' % path
            return
        tmp = open( path, 'r' )
        tmpfam = pickle.load( tmp )
        tmp.close()
        if not append:
            self = copy.deepcopy( tmpfam )
            del tmpfam
            return self
        else:
            for lam in tmpfam.lams:
                self.lams.append( lam )
            for k,v in tmpfam.params.iteritems():
                self.params[k] = v
            self.name = 'appended_' + self.name

    def save( self, path ):
        # deleting some objects:
        for param in self.params.values():
            del param.fig
            del param.mng
            for func in param.functions.values():
                del func.subplot

        import cPickle as pickle
        tmp = open( path, 'w' )
        pickle.dump( self, tmp )
        tmp.close()
        print 'LamFamily saved at %s' % path
        return path

