import desicos.abaqus.utils as utils

def plot_xy(self, xs, ys, name = 'default_plot',
             xValuesLabel = 'x_axis', yValuesLabel = 'y_axis',
             legendLabel = '', sort=True):
    import __main__
    tmp = []
    tmp_sort = []
    for i in range(len(xs)):
        tmp_sort.append([xs[i],ys[i]])
    if sort:
        tmp_sort.sort()
    for i in range(len(tmp_sort)):
        x = tmp_sort[i][0]
        y = tmp_sort[i][1]
        tmp.append((x, y))
    __main__.session.XYData(name = name, data = tmp,
                             xValuesLabel = xValuesLabel,
                             yValuesLabel = yValuesLabel,
                             legendLabel  = legendLabel)

def plot_forces(self, step_num=2, along_edge=False, gui=False):
    import __main__
    step_name = self.step_name(step_num)
    names = []
    do_norm = False
    if self.study:
        if self.study.calc_Pcr:
            do_norm = True
            Pcr = self.study.ccs[0].zload[0]
    if gui:
        names.append('%s_load_shortening_curve' % self.jobname)
        if do_norm:
            names.append('%s_load_shortening_curve_norm' % self.jobname)
    else:
        names.append('%s_Step_%02d_Displacement_X_Force' %\
                     (self.jobname, step_num))
        if do_norm:
            names.append('%s_Step_%02d_Displacement_X_Force_norm' %\
                     (self.jobname, step_num))
    lamt = sum(self.plyts)
    tmp_displ_f = []
    tmp_displ_f_norm = []
    fb_load = utils.find_fb_load(self.zload)
    for i in range(len(self.zload)):
        zload = self.zload[i]
        tmp_displ_f.append((abs(self.zdisp[i]), 0.001 * zload))
        if do_norm:
            tmp_displ_f_norm.append((abs(self.zdisp[i]/lamt), zload/Pcr))
    if len(tmp_displ_f) == 0:
        print 'ERROR - plot_forces - run read_outputs first'
        return
    if self.impconf.ploads <> []:
        legendLabel = 'perturbation load = %2.1f N, first buckling load = %2.2f kN' %\
                (self.impconf.ploads[0].pltotal, 0.001 * fb_load)
    else:
        legendLabel = self.jobname

    session = __main__.session
    session.XYData(\
            name = names[ 0 ],
            data = tmp_displ_f,
            xValuesLabel = 'End-Shortening, mm',
            yValuesLabel = 'Reaction Load, kN',
            legendLabel = legendLabel)
    if do_norm:
        session.XYData(\
                name = names[ 1 ],
                data = tmp_displ_f_norm,
                xValuesLabel = 'Normalized End-Shortening',
                yValuesLabel = 'Normalized Reaction Load',
                legendLabel = legendLabel)
    if along_edge:
        names.append(\
            '%s_Step_%02d_Force_along_loaded_edge' \
            % (self.jobname, step_num))
        tmp = []
        zload = 0
        for node in self.cross_sections[-1].nodes:
            if node <> None:
                fz = node.fz[ step_name ][ -1 ]
                zload += fz
                tmp.append((node.theta, 0.001 * fz))
        frmlen = len(node.fz[ step_name ])
        session.XYData(\
                name = names[ 1 ],
                data = tmp,
                xValuesLabel = 'Circumferential position, degrees',
                yValuesLabel = 'Reaction Load, kN',
                legendLabel =  '%s, total force = %2.2f kN' \
                               % (self.jobname, 0.001 * sum(self.zload)))
    self.ls_curve = tmp_displ_f
    if do_norm:
        return tmp_displ_f, tmp_displ_f_norm
    else:
        return tmp_displ_f, None

def plot_displacements(self, step_num=1, frame_num = -1):
    import __main__
    step_name = self.step_name(step_num)
    names = []
    numcharts = 2
    index = -1
    for pload in self.impconf.ploads:
        index += 1
        tmp = []
        maxdisp = 0.
        for node in pload.cross_section.nodes:
            dr = node.dr[ step_name ][ frame_num ]
            if abs(dr) > abs(maxdisp):
                maxdisp = dr
            theta = node.theta
            tmp.append((theta, dr))
        names.append(\
            '%s_Step_%02d_Displ_along_circumference' \
            % (self.jobname, step_num))
        __main__.session.XYData(\
                name = names[ index * numcharts + 0 ],
                data = tmp,
                xValuesLabel = 'Circumferential position, degrees',
                yValuesLabel = 'Radial displacement, mm',
                legendLabel  = 'Max displacement = %f mm' % maxdisp)
        tmp = []
        maxdisp = 0.
        for node in pload.meridian.nodes:
            dr = node.dr[ step_name ][ frame_num ]
            if abs(dr) > abs(maxdisp):
                maxdisp = dr
            z = node.z
            tmp.append((z, dr))
        names.append(\
            '%s_Step_%02d_Displ_along_meridian' \
            % (self.jobname, step_num))
        __main__.session.XYData(\
                name = names[ index * numcharts + 1 ],
                data = tmp,
                xValuesLabel = 'Meridional position, mm',
                yValuesLabel = 'Radial displacement, mm',
                legendLabel  = 'Max displacement = %f mm' % maxdisp)

def plot_stress_analysis(self, disp_force_frame = 'DISP'):
    keys = ['HSNFCCRT','HSNFTCRT','HSNMCCRT','HSNMTCRT']
    names = { 'HSNFCCRT': 'Hashin, Fiber Compression',
              'HSNFTCRT': 'Hashin, Fiber Tension',
              'HSNMCCRT': 'Hashin, Matrix Compression',
              'HSNMTCRT': 'Hashin, Matrix Tension' }
    dff = disp_force_frame.upper()
    if   dff == 'DISP':
        xlabel = 'End-Shortening, mm'
        xaxis = [abs(i) for i in self.zdisp]
    elif dff == 'FORCE':
        xaxis = [i*0.001 for i in self.zload]
        xlabel = 'Reaction Load, kN'
    elif dff == 'FRAME':
        xaxis = [i for i in range(len(self.zdisp))]
        xlabel = 'Frame index'
    for key in keys:
        xs = []; ms = []; fi = []
        for f_num in self.hashin_max_ms.keys():
            xs.append(xaxis[f_num])
            ms.append(self.hashin_max_ms[f_num][key])
            fi.append(self.hashin_max_num[f_num][key])
        name = '_'.join([self.jobname,dff,'MS',key])
        self.plot_xy(xs=xs, ys=ms, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Margin of Safety',
                      legendLabel  = 'MS ' + names[key])
        name = '_'.join([self.jobname,dff,'FI',key])
        self.plot_xy(xs=xs, ys=fi, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Failure Index',
                      legendLabel  = 'FI ' + names[key])
    keys = ['S11','S22','S12']
    for key in keys:
        xs = []; ms = []; fi = []
        for f_num in self.stress_min_ms.keys():
            xs.append(xaxis[f_num])
            ms.append(self.stress_min_ms[f_num][key])
            fi.append(self.stress_min_num[f_num][key])
        name = '_'.join([self.jobname,dff,key,'MS','MIN'])
        self.plot_xy(xs=xs, ys=ms, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Margin of Safety',
                      legendLabel  = 'MS ' + key)
        name = '_'.join([self.jobname,dff,key,'STRESS','MIN'])
        self.plot_xy(xs=xs, ys=fi, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Stress, MPa',
                      legendLabel  = 'Stress ' + key)
        xs = []; ms = []; fi = []
        for f_num in self.stress_max_ms.keys():
            xs.append(xaxis[f_num])
            ms.append(self.stress_max_ms[f_num][key])
            fi.append(self.stress_max_num[f_num][key])
        name = '_'.join([self.jobname,dff,key,'MS','MAX'])
        self.plot_xy(xs=xs, ys=ms, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Margin of Safety',
                      legendLabel  = 'MS ' + key)
        name = '_'.join([self.jobname,dff,key,'STRESS','MAX'])
        self.plot_xy(xs=xs, ys=fi, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Stress, MPa',
                      legendLabel  = 'Stress ' + key)
