import numpy as np

import desicos.abaqus.geom as geom
import desicos.abaqus.coords as coords
from desicos.abaqus.constants import *

def append_edges_meridian( cc, meridian, theta, objname ):
    cc_h = cc.h
    z1 =  0.01*cc_h
    z2 =  0.99*cc_h
    zs = np.linspace( z1, z2, 10 )
    edges = []
    for z in zs:
        pt =  z / float( cc_h )
        cc_r,z = cc.r_z_from_pt( pt )
        x,y,z = coords.cyl2rec( cc_r, theta, z )
        if   objname == 'part':
            tmp = cc.part.edges.findAt( ((x, y, z),) , printWarning=False)
        elif objname == 'instance':
            tmp = cc.inst.edges.findAt( ((x, y, z),) , printWarning=False)
        if len(tmp) > 0:
            edge = tmp[0]
            if not edge in edges:
                edges.append( edge )
    if objname == 'part':
        meridian.part_edges = []
    if objname == 'instance':
        meridian.inst_edges = []
    for edge in edges:
        if   objname == 'part':
            meridian.part_edges.append( edge )
        elif objname == 'instance':
            meridian.inst_edges.append( edge )

def append_edges_cross_section( cc, cs, z, objname ):
    cc_h = cc.h
    x1 = -1.e6
    y1 = -1.e6
    z1 = z - 0.01*cc_h
    x2 = 1.e6
    y2 = 1.e6
    z2 = z + 0.01*cc_h
    if   objname == 'part':
        cs.part_edges = []
        edges = cc.part.edges.getByBoundingBox(x1,y1,z1,x2,y2,z2)
    elif objname == 'instance':
        cs.inst_edges = []
        edges = cc.inst.edges.getByBoundingBox(x1,y1,z1,x2,y2,z2)
    for edge in edges:
        if   objname == 'part':
            cs.part_edges.append( edge )
        elif objname == 'instance':
            cs.inst_edges.append( edge )

def _map_edges( self, objname = 'part' ):
    if   objname == 'part':
        obj = self.part
    elif objname == 'instance':
        obj = self.mod.rootAssembly.instances['InstanceCylinder']
    for i in range( len( self.cross_zs) ):
        cs = self.cross_sections[ i ]
        z = cs.z
        append_edges_cross_section( self, cs, z, objname )

    for i in range( len(self.thetas) ):
        theta    = self.thetas[ i ]
        meridian = self.meridians[ i ]
        append_edges_meridian(self, meridian, theta, objname)

def _read_and_map_nodes( cc ):
    cc.nodes = {}
    for entity in cc.cross_sections + cc.meridians:
        if not entity.part_edges:
            continue
        else:
            nodes = []
            for edge in entity.part_edges:
                nodes += edge.getNodes()
            entity.nodes = []
            for node in nodes:
                #TODO this "iF" slows down the process
                keys = cc.nodes.keys()
                node_label = node.label
                if not node_label in keys:
                    newNode             = geom.Node()
                    newNode.obj         = node
                    newNode.rebuild()
                    cc.nodes[ node_label ] = newNode
                else:
                    newNode = cc.nodes[ node_label ]
                newNode.sortattr = entity.sortattr
                #TODO the creation of ids and the if using this ids below
                #     slows down the process
                ids = [ node.id for node in entity.nodes ]
                if not newNode.id in ids:
                    entity.nodes.append( newNode )
            entity.nodes.sort()
    for imp in cc.impconf.imperfections:
        imp.get_node()
