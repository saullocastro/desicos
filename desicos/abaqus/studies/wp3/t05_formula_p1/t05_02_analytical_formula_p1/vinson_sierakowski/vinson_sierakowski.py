import sys
sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')
sys.path.append(r'C:\Users\pfh-castro\programming\python\modeling-analysis-python')
import conecyl
cc = conecyl.ConeCyl()
cc.fromDB( 'huehne_2008_z07' )
import analytical_BL._vinson_sierakowski as vs
# m = axial_directin
# n = circumferential direction
for m in [1,2,3,4]:
    for n in range(4,18):
        print 'm',m,'\tn',n, ('\tBL % 9d' % int(vs.calc_BL( cc, m, n )) )
