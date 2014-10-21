from lam_parameters._lam_family import LamFamily
class Lam(LamFamily):
    def __init__( self ):
        super( Lam, self ).__init__()
        self.family = None
        self.lam_name = ''
        self.plyt = 0.125
        self.stack = []
        self.valid = False
        self.remaining = None
        self.laminaprop = None
        self.store_objL = True
        self.objL = None

    def rebuild( self ):
        self.create_stack( self.stack )
        self.calc_lam()

    def check_balance( self ):
        pos={}
        for theta in self.stack:
            theta = int(theta)
            if theta == 0 or theta == 90:
                continue
            if   theta > 0 and not theta in pos.keys():
                pos[ theta ]  = 1
            elif theta > 0 and theta in pos.keys():
                pos[ theta ] += 1
            elif theta < 0 and not abs(theta) in pos.keys():
                pos[ abs(theta) ] = -1
            elif theta < 0 and abs(theta) in pos.keys():
                pos[ abs(theta) ] -= 1
        balanced = True
        for num in pos.values():
            if num <> 0:
                balanced = False
                break
        return balanced

    def check_dist_ang_plies( self, maxdist = 1 ):
        #TODO make this function more general than 30, 45, 60
        p30 = {}
        p45 = {}
        p60 = {}
        for i in range( len(self.stack) ):
            theta = self.stack[i]
            if   theta == 30:
                p30[ i ] = False
            elif theta == 45:
                p45[ i ] = False
            elif theta == 60:
                p60[ i ] = False
        index_range = range( -maxdist, maxdist+1 )
        index_range.pop( index_range.index(0) )
        for i in range( len(self.stack) ):
            theta = self.stack[i]
            for j in index_range:
                if   theta == -30:
                    if i+j in p30.keys():
                        p30[ i+j ] = True
                elif theta == -45:
                    if i+j in p45.keys():
                        p45[ i+j ] = True
                elif theta == -60:
                    if i+j in p60.keys():
                        p60[ i+j ] = True

        false = False
        if false in p30.values():
            return False
        if false in p45.values():
            return False
        if false in p60.values():
            return False
        return True

    def add_ply( self, theta ):
        if self.remaining > 0:
            if theta == 0 or theta == 90:
                self.remaining -= 1
                self.stack.append(  theta )
            else:
                self.remaining -= 2
                self.stack.append(  theta )
                self.stack.append( -theta )

    def create_stack( self, stack=None, balanced=True ):
        if stack == None:
            stack = self.stack
        else:
            self.stack = stack
        if not self.family == None:
            self.num_plies = self.family.num_plies
        else:
            self.num_plies = len( self.stack )
        if balanced:
            self.valid = self.check_balance()
        else:
            self.valid = True
        if self.valid:
            name = '_'.join([ ('%02d' % theta) for theta in stack ])
            self.name  = name
            self.valid = True
            c_ang = 0
            c_00  = 0
            c_30  = 0
            c_45  = 0
            c_60  = 0
            c_90  = 0
            for theta in stack:
                if   theta      == 0:
                    c_00 += 1
                elif theta      == 90:
                    c_90 += 1
                elif abs(theta) == 30:
                    c_30 += 1
                    c_ang += 1
                elif abs(theta) == 45:
                    c_45 += 1
                    c_ang += 1
                elif abs(theta) == 60:
                    c_60 += 1
                    c_ang += 1
                else:
                    c_ang += 1
            self.params[ 'f_00'  ] = float(c_00)  / self.num_plies
            self.params[ 'f_30'  ] = float(c_30)  / self.num_plies
            self.params[ 'f_45'  ] = float(c_45)  / self.num_plies
            self.params[ 'f_60'  ] = float(c_60)  / self.num_plies
            self.params[ 'f_90'  ] = float(c_90)  / self.num_plies
            self.params[ 'f_ang' ] = float(c_ang) / self.num_plies

    def calc_lam( self ):
        import mapy
        import mapy.model.properties.composite as composite
        objL = composite.read_stack(
                      stack  = self.stack,
                      plyts   = self.plyts,
                      laminaprop = self.laminaprop)
        if self.store_objL:
            self.objL = objL
        self.params['a1'] = objL.xiA[1]
        self.params['a2'] = objL.xiA[2]
        self.params['a3'] = objL.xiA[3]
        self.params['a4'] = objL.xiA[4]
        self.params['b1'] = objL.xiB[1]
        self.params['b2'] = objL.xiB[2]
        self.params['b3'] = objL.xiB[3]
        self.params['b4'] = objL.xiB[4]
        self.params['d1'] = objL.xiD[1]
        self.params['d2'] = objL.xiD[2]
        self.params['d3'] = objL.xiD[3]
        self.params['d4'] = objL.xiD[4]

    def print_lam( self, log=None ):
        params = self.params.keys()
        params.sort()
        tmp = '['
        for i in range( len( self.stack ) ):
            theta = self.stack[i]
            if i == 0:
               tmp +=   '%3s' % str(theta)
            else:
               tmp += ', %3s' % str(theta)
        tmp += ' ]'
        tmp = '%50s' % tmp
        for key in params:
            value = '%1.6f' % self.params[ key ]
            tmp  += '\t%10s' % value
        if log:
            log.write( tmp )
        else:
            print tmp
        return tmp

    def check_bloomfield( self ):
        import bloomfield
        return bloomfield.check_params( self.params )

