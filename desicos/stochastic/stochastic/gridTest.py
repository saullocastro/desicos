import numpy as np
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

pts=np.array([
[0,0,0],
[0.5,0,10],
[1,0,0],
[1.25,0,10],
[1.5,0,0],
[0,10,0],
[0.5,10,10],
[1,10,0],
[1.25,10,10],
[1.5,10,0]
])

n,nDim=pts.shape
x=pts[:,0]
y=pts[:,1]
z=pts[:,2]



ipts=np.array([[0.4,4],[1.2,4],[0.6,6],[1.3,6], [0.5,5],[1.25,5]  ])

imLin=griddata( (x,y) ,z,ipts,  method='linear')
imNea=griddata( (x,y) ,z,ipts,  method='nearest')

X,Y=np.meshgrid(x,y)
val=np.zeros((n,n))
for i in range(n):
    for j in range(n):
        val[i][j]=z[j]


fig = plt.figure()
ax = fig.gca(projection='3d')
surf0 = ax.plot_surface(X,Y,val,rstride=1, cstride=1, color='r')
pt0 = ax.plot(x,y,z,'*',markersize=10)
pt2=ax.plot(ipts[:,0],ipts[:,1],imNea,'o',color='r',markersize=10)
pt1=ax.plot(ipts[:,0],ipts[:,1],imLin,'o',color='g',markersize=10)
plt.show()
