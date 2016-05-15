# -*- coding: utf-8 -*-
"""
Corugated shell sketch points creation

@author: loza_em
"""

import numpy as np
#import matplotlib.pyplot as plt
#cc=1
#[X_plot, Y_plot]=cor_shell(cc)

#plt.figure()
#line, = plt.plot(X_plot, Y_plot, '-', linewidth=1)
#plt.axes().set_aspect('equal', 'datalim')
#plt.show()
    
def cor_shell(cc):
    #Re=2.7
    #Nc=100
    #alphadeg=1;
    Re=cc.rbot
    Nc=int(cc.geo_cs[0])
    alphadeg=cc.geo_cs[1];
    alpha=alphadeg*2*np.pi/360
    a_b_ratio=cc.geo_cs[2]

    Ri=[]
    G1=[]
    G2=[]
    G4=[]
    fg=[]
    y=[]
    temp=[]
#Increment for the solution
    incre=0.01  
    for ii in range (1,10000):
        temp.append(1+incre*ii)

    i=0
    for a in temp:
        b=a/a_b_ratio
        #Internal radius & angles calculation
        Ri.append(np.sqrt((b*np.sin(alpha))**2+(Re-b*np.cos(alpha))**2))
        G1.append(np.arccos((Re-b*np.cos(alpha))/(Ri[i])))
        G2.append(2*np.arcsin(a/(2*Ri[i])))
        G4.append(2*np.arcsin(a/(2*Re)))
        y.append(i)
        fg.append(2*G1[i]+G2[i]+G4[i]-(2*np.pi)/Nc);
    
        if i>1 and ((fg[i]*fg[i-1])!=abs(fg[i]*fg[i-1])):
            #check=(2*G1[i]+G2[i]+G4[i])*Nc/(2*np.pi)
            #print(check)
            G1_sol=G1[i]
            G2_sol=G2[i]
            Ri_sol=np.sqrt(((a/a_b_ratio)*np.sin(alpha))**2+(Re-(a/a_b_ratio)*np.cos(alpha))**2)

            break
        
        i=i+1
    
#Points
    Points1=[]
    Points2=[]
    Points3=[]
    Points4=[]
    X_cor=[]
    Y_cor=[]
#Create the points to rotate  
    for i in range (0,Nc+1):
        Points1.append([Re*np.cos((i)*2*np.pi/Nc),Re*np.sin((i)*2*np.pi/Nc)]);
        X_cor.append(Points1[i][0])
        Y_cor.append(Points1[i][1])
        Points2.append([Ri_sol*np.cos((G1_sol+(i)*(2*np.pi/Nc))),Ri_sol*np.sin((G1_sol+(i)*(2*np.pi/Nc)))]);
        X_cor.append(Points2[i][0])
        Y_cor.append(Points2[i][1])
        Points3.append([Ri_sol*np.cos((G1_sol+G2_sol+(i)*(2*np.pi/Nc))),Ri_sol*np.sin((G1_sol+G2_sol+(i)*(2*np.pi/Nc)))]);
        X_cor.append(Points3[i][0])
        Y_cor.append(Points3[i][1])
        Points4.append([Re*np.cos((2*G1_sol+G2_sol+(i)*(2*np.pi/Nc))),Re*np.sin((2*G1_sol+G2_sol+(i)*(2*np.pi/Nc)))]);
        X_cor.append(Points4[i][0])
        Y_cor.append(Points4[i][1])
    cor_shell.X_cor=X_cor
    cor_shell.Y_cor=Y_cor

    cor_shell.A_cor=a
    cor_shell.B_cor=b
    #return (X_cor ,Y_cor)
