import numpy as np
# local modules
import geom
# local contants
from constants import *
#def rec2cyl( x, y, z):
#    thetarad = np.arctan2( y, x )
#    if abs(thetarad) < TOL:
#        r = abs(x)
#    else:
#        r     = x / np.cos( thetarad )
#    theta = np.rad2deg( thetarad )
#    z     = z
#    return r, theta, z
#
def rec2cyl( x, y, z):
    thetarad = np.arctan2( y, x )
    r = np.sqrt((x**2 + y**2))
    theta = np.rad2deg( thetarad )
    return r, theta, z

def cyl2rec( r, theta, z ):
    x = r * np.cos( np.deg2rad( theta ) )
    y = r * np.sin( np.deg2rad( theta ) )
    z = z
    return x, y, z

def cyl2rec_profi( array ):
    return np.concatenate((array[0] * np.cos( np.deg2rad( array[1] ) ),
                           array[0] * np.sin( np.deg2rad( array[1] ) ),
                           array[2]))
