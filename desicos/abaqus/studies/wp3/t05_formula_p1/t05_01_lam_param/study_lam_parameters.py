import lam_param_range
lam_param_range = reload( lam_param_range )
p1s = [0,-30,30,-45,45,-60,60,90]
p2s = [0,-30,30,-45,45,-60,60,90]
p3s = [0,-30,30,-45,45,-60,60,90]
p4s = [0,-30,30,-45,45,-60,60,90]
p5s = [0,-30,30,-45,45,-60,60,90]
p6s = [0,-30,30,-45,45,-60,60,90]
p7s = [0,-30,30,-45,45,-60,60,90]
p8s = [0,-30,30,-45,45,-60,60,90]
lam = {}
lam[4] = {}
lam[5] = {}
lam[6] = {}
lam[7] = {}
lam[8] = {}
for p1 in p1s:
    for p2 in p2s:
        for p3 in p3s:
            for p4 in p4s:
                lam_param_range.create_stack( lam, 4, p1, p2, p3, p4)
                for p5 in p5s:
                    lam_param_range.create_stack( lam, 5, p1, p2, p3, p4, p5)
                    for p6 in p6s:
                        lam_param_range.create_stack( lam, 6, p1, p2, p3, p4, p5, p6)
                        for p7 in p7s:
                            lam_param_range.create_stack( lam, 7, p1, p2, p3, p4, p5, p6, p7)
                            for p8 in p8s:
                                lam_param_range.create_stack( lam, 8, p1, p2, p3, p4,
                                                      p5, p6, p7, p8)
#                                for p9 in thetas:
#                                    create_stack( lam, 9, p1, p2, p3, p4,
#                                                          p5, p6, p7, p8,
#                                                          p9)
#                                    for p10 in thetas:
#                                        create_stack( lam, 10, p1, p2, p3, p4,
#                                                               p5, p6, p7, p8,
#                                                               p9, p10)
#                                        for p11 in thetas:
#                                            create_stack( lam, 11, p1, p2, p3, p4,
#                                                                   p5, p6, p7, p8,
#                                                                   p9, p10, p11)
#                                            for p12 in thetas:
#                                                create_stack( lam, 12, p1, p2, p3, p4,
#                                                                       p5, p6, p7, p8,
#                                                                       p9, p10, p11, p12)
lam = lam_param_range.calc_lamination_parameters( lam )
#
