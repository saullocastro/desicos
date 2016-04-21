import numpy as np

class FilterWindows2D(object):
    filters={}

    filters['none']= lambda *args : FilterWindows2D._ones(*args)
    filters['hamming']= lambda *args : FilterWindows2D._hammingWindow(*args)
    filters['hamming_X']= lambda *args : FilterWindows2D._hammingWindow_x(*args)
    filters['hamming_Y']= lambda *args : FilterWindows2D._hammingWindow_y(*args)
    filters['trapezoid']= lambda *args : FilterWindows2D._trapWindow(*args)

    @classmethod
    def setInputArray(cls,x,y):
        cls.x=x
        cls.y=y
        cls.nx=len(x)
        cls.ny=len(y)
        cls.lx=x[-1:][0]
        cls.ly=y[-1:][0]
        qx1=np.linspace(-cls.lx/2.0,cls.lx/2.0,cls.nx)
        qy1=np.linspace(-cls.ly/2.0,cls.ly/2.0,cls.ny)
        qx=(qx1 + cls.lx/2.)/cls.lx
        qy=(qy1 + cls.ly/2.)/cls.ly
        cls.qx,cls.qy=qx,qy

    @classmethod
    def _ones(cls):
        return np.ones((cls.nx,cls.ny))

    @classmethod
    def _hammingWindow(cls,cx1,cx2,cy1,cy2):

        wx=cx1+cx2*np.cos(2.0*np.pi*cls.qx)
        wy=cy1+cy2*np.cos(2.0*np.pi*cls.qy)
        w=np.array([wx]).T*wy
        return w

    @classmethod
    def _hammingWindow_x(cls,cx1,cx2):
        wx=cx1+cx2*np.cos(2.0*np.pi*cls.qx)
        wy=np.ones(cls.qy.shape)
        w=np.array([wx]).T*wy
        return w

    @classmethod
    def _hammingWindow_y(cls,cy1,cy2):
        wx=np.ones(cls.qx.shape)
        wy=cy1+cy2*np.cos(2.0*np.pi*cls.qy)
        w=np.array([wx]).T*wy
        return w

    @classmethod
    def _trapWindow(cls,ex,ey):
        wx=np.ones(cls.qx.shape)
        wy=np.ones(cls.qy.shape)

        if (ex > 0.0):
            for i in range(len(cls.qx)):
                if cls.qx[i] <= ex:
                    wx[i]=1.0/ex * cls.qx[i]
                if cls.qx[i] >= 1-ex:
                    wx[i]=1.0 - 1.0/ex*( cls.qx[i] -(1-ex))
        if (ey > 0.0):
            for i in range(len(cls.qy)):
                if cls.qy[i] <= ey:
                    wy[i]=1.0/ey * cls.qy[i]
                if cls.qy[i] >= 1-ey:
                    wy[i]=1.0 - 1.0/ey*( cls.qy[i] -(1-ey))


        w=np.array([wx]).T*wy
        return w

