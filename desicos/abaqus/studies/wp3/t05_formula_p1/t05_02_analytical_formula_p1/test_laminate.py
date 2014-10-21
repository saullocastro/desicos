import numpy
numpy.set_printoptions(precision=1, suppress=True)
import sympy
from sympy import sin, pi
# local modules
import mapy.model.properties.composite as composite
#
laminaprop = (135e3, 13e3, 0.38, 6.4e3, 6.4e3, 4.3e3, 273.15,13e3,0.38,0.38)
stack = [45,-45,90,0,90]
ply_t = [0.142 for i in stack]
#
# reading laminate
objL = composite.read_stack( stack = stack,
                             plyts = plyts,
                             laminaprop = laminaprop,
                             general = True )
print 'slicing matrices to compare'
A = objL.A
B = objL.B
D = objL.D
E = objL.E
print objL.D_general

