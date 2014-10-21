nu = 0.3


w =

e2 = 1/(E*h) * (Nphi - nu*Nx) # (2)
e1 = 1/(E*h) * (Nx - nu*Nphi) # (3)
gamma = 2 * Nxphi /(E*h)      # (4)
chix = w
D = E*h**3/(12*(1-nu**2))
Vbend    = D/2 * (chiphi ** 2  + chix ** 2 + 2*chix*chiphi)
Vtwist   = D * (1-nu) * chixphi ** 2
Vshear   = 0.5 * (E * h /( 2 * (1+nu) ) ) * ( gamaxz ** 2 + gamaphiz ** 2 )
Vstretch = 0.5 * (Nx * ex + Nphi * ephi + Nxphi * gamaxphi)
V = Vbend + Vtwist + Vshear + Vstretch  # (20)

