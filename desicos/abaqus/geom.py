class SortMaster(object):
    def __init__( self ):
        self.sortattr = None

    def __lt__( self, other ):
        if other <> None:
            return getattr(self, self.sortattr, None) < \
                   getattr(other, other.sortattr, None)
        else:
            return getattr(self, self.sortattr, None) < None

    def __eq__( self, other ):
        if other <> None:
            return getattr(self, self.sortattr, None) == \
                   getattr(other, other.sortattr, None)
        else:
            return getattr(self, self.sortattr, None) == None

class CrossSection(SortMaster):
    def __init__( self ):
        super( CrossSection, self ).__init__()
        self.prefix = 'CROSS_SECTION'
        self.sortattr = 'z'
        self.index = None
        self.z = None
        self.nodes = []
        self.ploads = []
        self.part_edges  = []
        self.inst_edges  = []

class Meridian(SortMaster):
    def __init__( self ):
        super( Meridian, self ).__init__()
        self.prefix = 'MERIDIAN'
        self.sortattr = 'theta'
        self.index = None
        self.theta = None
        self.nodes = []
        self.ploads = []
        self.part_edges  = []
        self.inst_edges  = []

class Node(SortMaster):
    def __init__( self ):
        super( Node, self ).__init__()
        self.sortattr = 'z'
        self.odb_index = None
        self.meridian = None
        self.cross_section = None
        self.id = None
        self.x  = None
        self.y  = None
        self.z  = None
        self.theta = None
        self.pload = None
        self.r  = None
        self.dx = {}
        self.dy = {}
        self.dz = {}
        self.dr = {}
        self.fx = {}
        self.fy = {}
        self.fz = {}
        self.obj = None

    def rebuild( self ):
        import coords
        if self.obj <> None:
            x,     y, z = self.obj.coordinates
            r, theta, z = coords.rec2cyl( x, y, z )
            self.id     = self.obj.label
            self.x      = x
            self.y      = y
            self.z      = z
            self.r      = r
            self.theta  = theta
        else:
            self.r = (self.x**2 + self.y**2)**0.5

class Plane(object):

    def __init__( self ):
        self.theta = None
        self.p1 = None
        self.p2 = None
        self.p3 = None
        self.datum = None
        self.feature = None
        self.part = None

    def create( self ):
        self.feature = self.part.DatumPlaneByThreePoints( point1 = self.p1,
                                                          point2 = self.p2,
                                                          point3 = self.p3 )
        tmp = self.part.datums.keys()
        tmp.sort()
        self.datum = self.part.datums[ tmp[-1] ]

    def __getattr__( self, attr ):
        try:
            return getattr( self, attr )
        except:
            return getattr( self.datum, attr )

# trash
#
#class Edge(SortMaster):
#    def __init__( self ):
#        raise
#        super( Edge, self ).__init__()
#        self.sortattr = 'theta'
#        self.theta    = None
#        self.mid      = None
#        self.mid2     = None
#        self.bot      = None
#        self.top      = None
#
#class Face(SortMaster):
#    def __init__( self ):
#        raise
#        super( Face, self ).__init__()
#        self.sortattr = 'theta'
#        self.theta = None
#        self.feature = None
#
