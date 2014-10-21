import numpy
numpy.set_printoptions(precision=1, suppress=True)
import sympy
from sympy import sin, pi
# local modules
import mapy.model.properties.composite as composite
#
laminaprop = (25.1e6,4.8e6,0.036,1.36e6,1.2e6,0.47e6, 273.15,0.75e6,0.25,0.171)
stack = [0,90,45,-45,30]
plyts = [1. for i in stack]
#
# reading laminate
objL = composite.read_stack( stack = stack,
                             plyts = plyts,
                             laminaprop = laminaprop,
                             general = True )
print objL.ABD
print objL.ABD_general
