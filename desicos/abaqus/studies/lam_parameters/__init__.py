import numpy as np
import os
def lam( stack, plyts=[0.125], laminaprop='default' ):
    import lam_parameters._lam
    ans = lam_parameters._lam.Lam()
    ans.plyts = plyts
    ans.stack = stack
    if laminaprop == 'default'\
    or len( laminaprop ) <> 7:
        #laminaProp = ( e1, e2, nu12, g12, g13, g23, tempref )
        laminaprop  = (125.774e3,10.03e3,0.271,5.555e3,5.555e3,3.4e3,273.15)
        ans.laminaprop = laminaprop
    return ans

def print_lamination_parameters( lam_families ):
    num_plies = lam_families.keys()
    num_plies.sort()
    xiA = {1:[],2:[],3:[],4:[]}
    xiB = {1:[],2:[],3:[],4:[]}
    xiD = {1:[],2:[],3:[],4:[]}
    xiE = {1:[],2:[],3:[],4:[]}
    log = open(r'c:\users\pfh-castro\desktop\lam.txt', 'w')
    log.write( ('%50s' % 'plies') + '\tf_00\tf_90\tf_ang\tf_30\tf_45\tf_60\ta1\ta2\ta3\ta4\tb1\tb2\tb3\tb4\td1\td2\td3\td4\n' )
    for num_ply in num_plies:
        L = lam_families[ num_ply ]
        for dictL in L.values():
            pass
    log.close()
    for i in range(1,5):
        xiA[i].sort()
        xiB[i].sort()
        xiD[i].sort()
        xiE[i].sort()
    for i in range(1,5):
        print 'xi A %d\tMIN\t%f\tMAX\t%f' %( i, xiA[i][0], xiA[i][-1] )
    for i in range(1,5):
        print 'xi B %d\tMIN\t%f\tMAX\t%f' %( i, xiB[i][0], xiB[i][-1] )
    for i in range(1,5):
        print 'xi D %d\tMIN\t%f\tMAX\t%f' %( i, xiD[i][0], xiD[i][-1] )
    for i in range(1,5):
        print 'xi E %d\tMIN\t%f\tMAX\t%f' %( i, xiE[i][0], xiE[i][-1] )
    return True

