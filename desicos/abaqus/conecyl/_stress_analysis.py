import __main__

import numpy as np

def get_allow(cc, s11, s22):
    #TODO allowables for each ply
    As11t,As11c,As22t,As22c,As12,As13 = cc.allowables[0]
    if   s11 <  0 and s22 <  0:
        return As11c, As22c, As12
    elif s11 <  0 and s22 >= 0:
        return As11c, As22t, As12
    elif s11 >= 0 and s22 <  0:
        return As11t, As22c, As12
    elif s11 >= 0 and s22 >= 0:
        return As11t, As22t, As12

def nap(cc, pos):
    num = int(pos/3) +1
    angle = cc.stack[num-1]
    tmp = ['bot','mid','top']
    pos = tmp[int(pos) % 3]
    return num, angle, pos

def envelope_values(values_dict, positions_dict, minmax):
    ans = dict([[k,None] for k in values_dict.keys()])
    ans_pos = dict([[k,None] for k in values_dict.keys()])
    for key in values_dict.keys():
        values = values_dict[key].values
        positions = positions_dict[key].values
        if   minmax == 'min':
            minvalue =  1.e6
            minvalue_pos = -1
            for i in range(len(values)):
                v = values[i]
                if minvalue > v.data:
                    minvalue = v.data
                    pos = positions[i]
                    minvalue_pos = pos.data
            ans[key] = minvalue
            ans_pos[key] = minvalue_pos
        elif minmax == 'max':
            maxvalue = -1.e6
            maxvalue_pos = -1
            for i in range(len(values)):
                v = values[i]
                if maxvalue < v.data:
                    maxvalue = v.data
                    pos = positions[i]
                    maxvalue_pos = pos.data
            ans[key] = maxvalue
            ans_pos[key] = maxvalue_pos
    # solution to avoid division by zero when calculating the margin of
    # safeties below, in case there are some zero stresses
    for k,v in ans.iteritems():
        if abs(v) < 1.e-12:
            ans[k] = 1.e-12
    return ans, ans_pos

def calc_frame(cc, frame, frame_i, max_id, check_print_report = True):
    import abaqus

    #TODO allowables for each ply
    As11t,As11c,As22t,As22c,As12,As13 = cc.allowables[0]
    f = frame
    f_i = frame_i
    frame_id = frame.frameId
    print 'processing frame % 4d / % 4d, axial displ = %1.3f, reaction load = %1.2f' \
          % (frame_id, max_id, cc.zdisp[frame_i], cc.zload[frame_i])
    hashin = {'HSNFCCRT':None, 'HSNFTCRT':None, 'HSNMCCRT':None, 'HSNMTCRT':None}
    hashin_max = {'HSNFCCRT':None, 'HSNFTCRT':None, 'HSNMCCRT':None, 'HSNMTCRT':None}
    hashin_max_ms = {'HSNFCCRT':None, 'HSNFTCRT':None, 'HSNMCCRT':None, 'HSNMTCRT':None}
    hashin_max_pos = {'HSNFCCRT':None, 'HSNFTCRT':None, 'HSNMCCRT':None, 'HSNMTCRT':None}
    hashin_pts = {'HSNFCCRT':None, 'HSNFTCRT':None, 'HSNMCCRT':None, 'HSNMTCRT':None}
    hashin_fields = {'HSNFCCRT':[]  , 'HSNFTCRT':[]  , 'HSNMCCRT':[]  , 'HSNMTCRT':[]  }
    stress = {'S11':None, 'S22':None, 'S12':None }
    stress_min = {'S11':None, 'S22':None, 'S12':None }
    stress_min_ms = {'S11':None, 'S22':None, 'S12':None }
    stress_min_pos = {'S11':None, 'S22':None, 'S12':None }
    stress_max = {'S11':None, 'S22':None, 'S12':None }
    stress_max_ms = {'S11':None, 'S22':None, 'S12':None }
    stress_max_pos = {'S11':None, 'S22':None, 'S12':None }
    stress_pts = {'S11':None, 'S22':None, 'S12':None }
    stress_fields = {'S11':[]  , 'S22':[]  , 'S12':[]   }
    for key in hashin.keys():
        hashin[key] = f.fieldOutputs[key]
        hashin_pts[key] = f.fieldOutputs[key].locations[0].sectionPoints
    for key in stress.keys():
        stress[key] = f.fieldOutputs['S'].getScalarField(componentLabel=key)
        stress_pts[key] = f.fieldOutputs['S'].locations[0].sectionPoints
    for key in hashin.keys():
        for pt in hashin_pts[key]:
            hashin_fields[key].append(hashin[key].getSubset(sectionPoint=pt))
        hashin_max[key], hashin_max_pos[key] =\
            abaqus.maxEnvelope(hashin_fields[key])
    for key in stress.keys():
        for pt in stress_pts[key]:
            stress_fields[key].append(stress[key].getSubset(sectionPoint=pt))
        print 'DEBUG', key, stress_fields[key]
        stress_min[key], stress_min_pos[key] = \
            abaqus.minEnvelope(stress_fields[key])
        stress_max[key], stress_max_pos[key] = \
            abaqus.maxEnvelope(stress_fields[key])
    stress_min_num, stress_min_pos_num =\
        envelope_values(stress_min, stress_min_pos, 'min')
    stress_max_num, stress_max_pos_num =\
        envelope_values(stress_max, stress_max_pos, 'max')
    hashin_max_num, hashin_max_pos_num =\
        envelope_values(hashin_max, hashin_max_pos, 'max')
    As11, As22, As12 = get_allow(cc, stress_min_num['S11'], stress_min_num['S22'])
    stress_min_ms['S11'] = abs(As11 / stress_min_num['S11']) - 1.
    stress_min_ms['S22'] = abs(As22 / stress_min_num['S22']) - 1.
    stress_min_ms['S12'] = abs(As12 / stress_min_num['S12']) - 1.
    As11, As22, As12 = get_allow(cc, stress_max_num['S11'], stress_max_num['S22'])
    stress_max_ms['S11'] = abs(As11 / stress_max_num['S11']) - 1.
    stress_max_ms['S22'] = abs(As22 / stress_max_num['S22']) - 1.
    stress_max_ms['S12'] = abs(As12 / stress_max_num['S12']) - 1.
    for key in hashin_max_num.keys():
        hashin_max_ms[key] = 1./np.sqrt(hashin_max_num[key]) - 1.
    cc.stress_min_num    [frame_id] = stress_min_num
    cc.stress_min_ms     [frame_id] = stress_min_ms
    cc.stress_min_pos_num[frame_id] = stress_min_pos_num
    cc.stress_max_num    [frame_id] = stress_max_num
    cc.stress_max_ms     [frame_id] = stress_max_ms
    cc.stress_max_pos_num[frame_id] = stress_max_pos_num
    cc.hashin_max_num    [frame_id] = hashin_max_num
    cc.hashin_max_ms     [frame_id] = hashin_max_ms
    cc.hashin_max_pos_num[frame_id] = hashin_max_pos_num
    if check_print_report:
        print '\t'.join(['','Hashin,FC','Hashin,FT','Hashin,MC','Hashin,MT',
                       'S11min','S11max','S22min','S22max','S12min','S12max'])
        hsn = cc.hashin_max_num[frame_id]
        smin = cc.stress_min_num[frame_id]
        smax = cc.stress_max_num[frame_id]

        print '\t'.join([str(i) for i in [
          'stress',
          hsn['HSNFCCRT'], hsn['HSNFTCRT'], hsn['HSNMCCRT'], hsn['HSNMTCRT'],
          smin['S11'],     smax['S11'],     smin['S22'],     smax['S22'],
          smin['S12'],     smax['S12']
                                         ]])
        hsnpos = cc.hashin_max_pos_num[frame_id]
        sminpos = cc.stress_min_pos_num[frame_id]
        smaxpos = cc.stress_max_pos_num[frame_id]
        indexes = [0,1,2]
        names = ['ply num', 'ply angle', 'ply pos']
        for i in indexes:
            print '\t'.join([str(i) for i in [
              names[i],
              nap(cc,hsnpos['HSNFCCRT'])[i],nap(cc,hsnpos['HSNFTCRT'])[i],
              nap(cc,hsnpos['HSNMCCRT'])[i],nap(cc,hsnpos['HSNMTCRT'])[i],
              nap(cc,    sminpos['S11'])[i],nap(cc,    smaxpos['S11'])[i],
              nap(cc,    sminpos['S22'])[i],nap(cc,    smaxpos['S22'])[i],
              nap(cc,    sminpos['S12'])[i],nap(cc,    smaxpos['S12'])[i],
                                             ]])
        print '\t'.join([str(i) for i in [
            'allowables', 1.,1.,1.,1.,As11c,As11t,As22c,As22t,As12,As12
           ]])
        hsnms = cc.hashin_max_ms[frame_id]
        sminms = cc.stress_min_ms[frame_id]
        smaxms = cc.stress_max_ms[frame_id]
        print '\t'.join([str(i) for i in [
            'margin of safety',
            hsnms['HSNFCCRT'], hsnms['HSNFTCRT'],
            hsnms['HSNMCCRT'], hsnms['HSNMTCRT'],
            sminms['S11']    , smaxms['S11']    ,
            sminms['S22']    , smaxms['S22']    ,
            sminms['S12']    , smaxms['S12']
                                         ]])

def calc_frames(cc, frames=None, MSlimits=[0.0,0.2,0.5], frame_indexes=[]):
    if frames == None:
        frames = cc.attach_results().steps[cc.step2Name].frames
    if frame_indexes == []:
        iframes = frames
    else:
        iframes = [frames[i] for i in frame_indexes]
    max_id = iframes[-1].frameId
    print_ms_tsai_hill = [True for i in MSlimits]
    print_ms_tsai_wu = [True for i in MSlimits]
    i_mslimit = 0
    # finding frame first buckling and first minimum
    fb_load = 0.
    for i in range(len(iframes)):
        zload = cc.zload[i]
        if abs(zload) < abs(fb_load):
            break
        fb_load = zload
    fb_frame_i = i-1
    fb_frame = iframes[fb_frame_i]
    fb_load = cc.zload[fb_frame_i]
    for i in range(len(iframes)):
        if i <= fb_frame_i :
            continue
        zload = cc.zload[i]
        if abs(zload) > abs(fb_load):
            break
        fb_load = zload
    fm_frame_i = i-1
    fm_frame = iframes[fm_frame_i]
    #
    print '\nreport at first buckling load'
    calc_frame(cc=cc, frame=fb_frame, frame_i=fb_frame_i,
                max_id=max_id, check_print_report=True)
    print '\nreport at first minimum'
    # calculating minimum required stiffness
    delta_u = cc.zdisp[fm_frame_i] - cc.zdisp[fb_frame_i]
    delta_f = cc.zload[fm_frame_i] - cc.zload[fb_frame_i]
    if delta_u <> 0:
        k_min = abs(delta_f / delta_u)
    else:
        k_min = 0
        print 'WARNING - fail to calculate k_min value'
    print 'elastic recovery, minimum stiffness %1.3f' % k_min
    calc_frame(cc=cc, frame=fm_frame, frame_i=fm_frame_i,
                max_id=max_id, check_print_report=True)
    #
    cc.stress_min_num = {}
    cc.stress_min_ms = {}
    cc.stress_min_pos_num = {}
    cc.stress_max_num = {}
    cc.stress_max_ms = {}
    cc.stress_max_pos_num = {}
    cc.hashin_max_num = {}
    cc.hashin_max_ms = {}
    cc.hashin_max_pos_num = {}
    for i in range(len(iframes)):
        f = iframes[i]
        calc_frame(cc=cc, frame=f, frame_i=i,
                    max_id=max_id, check_print_report=False)

    return True

if __name__ == '__main__':
    calc_frames(cc, None, [0.0,0.2,0.5], [])

