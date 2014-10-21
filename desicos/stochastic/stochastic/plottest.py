import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


a=np.loadtxt('imp1.txt',delimiter=',')
R = 101.6;
L = 203.2;

[Nx,Ny]=a.shape
x=np.linspace(0,L,Nx)
y=np.linspace(0,2*R*np.pi,Ny)
[X,Y]=np.meshgrid(x,y)

[X,Y]=np.mgrid[0:L:complex(0,Nx) , -0:2*R*np.pi:complex(0,Ny) ]
fig = plt.figure()
ax = fig.gca(projection='3d')

surf = ax.plot_surface(X,Y,a,alpha=0.3)
plt.show()
