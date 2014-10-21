def calc_stacks( angles, num_plies, use_iterator=False ):
    if not use_iterator:
        import numpy as np
        lines = len(angles)**num_plies
        stacks = np.zeros(( lines, num_plies),dtype='int8')
        c4=-1
        c5=-1
        c6=-1
        c7=-1
        c8=-1
        c9=-1
        c10=-1
        c11=-1
        c12=-1
        c13=-1
        c14=-1
        c15=-1
        c16=-1
        for p1 in angles:
            for p2 in angles:
                for p3 in angles:
                    for p4 in angles:
                        if num_plies == 4:
                            c4 += 1
                            stacks[c4] = [ p1,p2,p3,p4 ]
                            continue
                        for p5 in angles:
                            if num_plies == 5:
                                c5 += 1
                                stacks[c5] =  [ p1,p2,p3,p4,p5 ]
                                continue
                            for p6 in angles:
                                if num_plies == 6:
                                    c6 += 1
                                    stacks[c6] = [ p1,p2,p3,p4,p5,p6 ]
                                    continue
                                for p7 in angles:
                                    if num_plies == 7:
                                        c7 += 1
                                        stacks[c7] = [ p1,p2,p3,p4,p5,p6,p7 ]
                                        continue
                                    for p8 in angles:
                                        if num_plies == 8:
                                            c8 += 1
                                            stacks[c8] = [ p1,p2,p3,p4,p5,p6,p7,p8 ]
                                            continue
                                        for p9 in angles:
                                            if num_plies == 9:
                                                c9 += 1
                                                stacks[c9] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9 ]
                                                continue
                                            for p10 in angles:
                                                if num_plies == 10:
                                                    c10 += 1
                                                    stacks[c10] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10 ]
                                                    continue
                                                for p11 in angles:
                                                    if num_plies == 11:
                                                        c11 += 1
                                                        stacks[c11] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11 ]
                                                        continue
                                                    for p12 in angles:
                                                        if num_plies == 12:
                                                            c12 += 1
                                                            stacks[c12] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12 ]
                                                            continue
                                                        for p13 in angles:
                                                            if num_plies == 13:
                                                                c13 += 1
                                                                stacks[c13] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13 ]
                                                                continue
                                                            for p14 in angles:
                                                                if num_plies == 14:
                                                                    c14 += 1
                                                                    stacks[c14] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14 ]
                                                                    continue
                                                                for p15 in angles:
                                                                    if num_plies == 15:
                                                                        c15 += 1
                                                                        stacks[c15] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15 ]
                                                                        continue
                                                                    for p16 in angles:
                                                                        if num_plies == 16:
                                                                            c16 += 1
                                                                            stacks[c16] = [ p1,p2,p3,p4,p5,p6,p7,p8,p9,p10,p11,p12,p13,p14,p15,p16 ]
                                                                            continue
        return stacks

    else:
        import itertools
        stacks = itertools.product( angles, repeat = num_plies )
        return stacks


