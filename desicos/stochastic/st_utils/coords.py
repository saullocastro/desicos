import numpy as np
from scipy.interpolate import griddata

TOL = 0.001

def rec2cyl( x, y, z):
    theta = np.arctan2( y, x )
    r = np.sqrt(x**2+y**2)
    return r, theta, z

def cyl2rec( r, theta, z ):
    x = r * np.cos( theta  )
    y = r * np.sin( theta  )
    z = z
    return x, y, z


def getGeomImperfection(r,z,RB,RT=None):
    if RT == None:
        RT=RB
    return r -(RB+ (RT-RB)*z)

def getImperfectionArray(tht,z,IM,fx,fy):
    X,Y=np.meshgrid(fx,fy)
    return griddata( (tht,z),IM,(X,Y),method='linear')


def getImperfectionArray3D(data,nx,ny,H,RB,RT=None):
    if RT == None:
        RT=RB

    x,y,z=data[0],data[1],data[2]
    r,tht,z=rec2cyl(x,y,z)
    fx=np.linspace(0.0,2.0*np.pi,nx)
    fy=np.linspace(0.0 ,H ,ny)
    thti=np.tile(fx,ny)
    zi=np.tile( fy,ny)
    ri=(RB+ (RT-RB)*zi)

    rPerf=(RB+ (RT-RB)*z)

    xP,yP,zP=cyl2rec(rPerf,tht,z)
    pP=np.array([xP,yP,zP]).transpose()

    xi,yi,zi=cyl2rec(ri,thti,zi)
    pI=np.array([xi,yi,zi]).transpose()

    im0=getGeomImperfection(r,z,RB,RT)
    imNew=griddata( pP ,im0, pI, method='nearest' )

    return fx,fy,imNew.reshape(nx,ny)

    #return getImperfectionArray(thti,zi,imNew,fx,np.linspace(0.0 ,H ,ny))







def cyl2plate(r,theta,z):
    return r*theta, z

def plate2cyl(r,x,z):
    return r, x/r, z

def plate2rec(r,x,z):
    rc,tc,zc=plate2cyl(r,x,z)
    return cyl2rec(rc,tc,zc)

def rec2plate(x,y,z):
    r,theta,z=rec2cyl( x, y, z)
    return cyl2plate(r,theta,z)
