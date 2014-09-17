import numpy as np
n=1024
H=100
x=np.linspace(-np.pi,np.pi,n)

y=np.sin(x)

for i in range(y.shape[0]):
	if y[i] < 0.0:
		y[i] = 0

import matplotlib.pyplot as plt
sp = np.fft.fft(y,n)

A=np.sqrt( sp.real**2.0 +sp.imag**2.0)
phi = np.arctan2(sp.imag,sp.real) 

freq=np.fft.fftfreq(n)
res=np.ones(n)*abs(sp[0])/2.
#res=np.zeros(n)
for i in range(0,n):
#	res+=( sp[i].real*np.cos(i*x) + sp[i].imag*np.sin(i*x) )/n
#	res[i]=np.sum(A*np.cos(2*np.pi*x[i]/2./n+phi))
	res+=(A[i]*np.cos(2*np.pi*x[i]/n/2.+phi[i]))
plt.plot(x,res)
plt.show()
