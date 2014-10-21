import sys
sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')
from analytical.linear_buckling import shadmehri
from conecylDB import ccs
from conecyl import ConeCyl
cc = ConeCyl()
cc.fromDB('zimmermann_1992_z33')
eigvals, eigvecs= shadmehri( cc, m=4, n=4 )

import sys
sys.exit()
eigvals, eigvecs = shadmehri( cc, m=4, n=4 )
