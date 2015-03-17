import os
from os.path import basename

import numpy as np

import desicos.abaqus.utils as utils
from desicos.logger import log

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
    step_name = self.get_step_name(step_num)
    names = []
    do_norm = False
    if self.study:
        if self.study.calc_Pcr:
            do_norm = True
            Pcr = self.study.ccs[0].zload[0]
    if gui:
        names.append('%s_load_shortening_curve' % self.model_name)
        if do_norm:
            names.append('%s_load_shortening_curve_norm' % self.model_name)
    else:
        names.append('%s_Step_%02d_Displacement_X_Force' %
                     (self.model_name, step_num))
        if do_norm:
            names.append('%s_Step_%02d_Displacement_X_Force_norm' %
                     (self.model_name, step_num))
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
        text = ('perturbation load = %2.1f N, first buckling load = %2.2f kN' %
                (self.impconf.ploads[0].pltotal, 0.001 * fb_load))
        legendLabel = text
    else:
        legendLabel = self.model_name

    session = __main__.session
    session.XYData(
            name = names[0],
            data = tmp_displ_f,
            xValuesLabel = 'End-Shortening, mm',
            yValuesLabel = 'Reaction Load, kN',
            legendLabel = legendLabel)
    if do_norm:
        session.XYData(
                name = names[1],
                data = tmp_displ_f_norm,
                xValuesLabel = 'Normalized End-Shortening',
                yValuesLabel = 'Normalized Reaction Load',
                legendLabel = legendLabel)
    if along_edge:
        names.append(
            '%s_Step_%02d_Force_along_loaded_edge'
            % (self.model_name, step_num))
        tmp = []
        zload = 0
        for node in self.cross_sections[-1].nodes:
            if node <> None:
                fz = node.fz[step_name][-1]
                zload += fz
                tmp.append((node.theta, 0.001 * fz))
        frmlen = len(node.fz[step_name])
        session.XYData(
                name = names[1],
                data = tmp,
                xValuesLabel = 'Circumferential position, degrees',
                yValuesLabel = 'Reaction Load, kN',
                legendLabel =  '%s, total force = %2.2f kN'
                               % (self.model_name, 0.001 * sum(self.zload)))
    self.ls_curve = tmp_displ_f
    if do_norm:
        return tmp_displ_f, tmp_displ_f_norm
    else:
        return tmp_displ_f, None

def plot_displacements(self, step_num=1, frame_num = -1):
    import __main__
    step_name = self.get_step_name(step_num)
    names = []
    numcharts = 2
    index = -1
    for pload in self.impconf.ploads:
        index += 1
        tmp = []
        maxdisp = 0.
        for node in pload.cross_section.nodes:
            dr = node.dr[step_name][frame_num]
            if abs(dr) > abs(maxdisp):
                maxdisp = dr
            theta = node.theta
            tmp.append((theta, dr))
        names.append(
            '%s_Step_%02d_Displ_along_circumference'
            % (self.model_name, step_num))
        __main__.session.XYData(
                name = names[index * numcharts + 0],
                data = tmp,
                xValuesLabel = 'Circumferential position, degrees',
                yValuesLabel = 'Radial displacement, mm',
                legendLabel  = 'Max displacement = %f mm' % maxdisp)
        tmp = []
        maxdisp = 0.
        for node in pload.meridian.nodes:
            dr = node.dr[step_name][frame_num]
            if abs(dr) > abs(maxdisp):
                maxdisp = dr
            z = node.z
            tmp.append((z, dr))
        names.append(
            '%s_Step_%02d_Displ_along_meridian'
            % (self.model_name, step_num))
        __main__.session.XYData(
                name = names[index * numcharts + 1],
                data = tmp,
                xValuesLabel = 'Meridional position, mm',
                yValuesLabel = 'Radial displacement, mm',
                legendLabel  = 'Max displacement = %f mm' % maxdisp)

def plot_stress_analysis(self, disp_force_frame = 'DISP'):
    keys = ['HSNFCCRT','HSNFTCRT','HSNMCCRT','HSNMTCRT', 'TSAIW']
    names = { 'HSNFCCRT': 'Hashin, Fiber Compression',
              'HSNFTCRT': 'Hashin, Fiber Tension',
              'HSNMCCRT': 'Hashin, Matrix Compression',
              'HSNMTCRT': 'Hashin, Matrix Tension',
              'TSAIW': 'Tsai-Wu'}
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
        # Verify that failure data is present, before attempting to plot
        if len(self.hashin_max_ms) == 0:
            continue
        if key not in next(self.hashin_max_ms.itervalues()):
            continue
        xs = []; ms = []; fi = []
        for f_num in self.hashin_max_ms.keys():
            xs.append(xaxis[f_num])
            ms.append(self.hashin_max_ms[f_num][key])
            fi.append(self.hashin_max_num[f_num][key])
        name = '_'.join([self.model_name,dff,'MS',key])
        self.plot_xy(xs=xs, ys=ms, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Margin of Safety',
                      legendLabel  = 'MS ' + names[key])
        name = '_'.join([self.model_name,dff,'FI',key])
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
        name = '_'.join([self.model_name,dff,key,'MS','MIN'])
        self.plot_xy(xs=xs, ys=ms, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Margin of Safety',
                      legendLabel  = 'MS ' + key)
        name = '_'.join([self.model_name,dff,key,'STRESS','MIN'])
        self.plot_xy(xs=xs, ys=fi, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Stress, MPa',
                      legendLabel  = 'Stress ' + key)
        xs = []; ms = []; fi = []
        for f_num in self.stress_max_ms.keys():
            xs.append(xaxis[f_num])
            ms.append(self.stress_max_ms[f_num][key])
            fi.append(self.stress_max_num[f_num][key])
        name = '_'.join([self.model_name,dff,key,'MS','MAX'])
        self.plot_xy(xs=xs, ys=ms, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Margin of Safety',
                      legendLabel  = 'MS ' + key)
        name = '_'.join([self.model_name,dff,key,'STRESS','MAX'])
        self.plot_xy(xs=xs, ys=fi, name=name,
                      xValuesLabel = xlabel,
                      yValuesLabel = 'Stress, MPa',
                      legendLabel  = 'Stress ' + key)


def extract_field_output(self, ignore):
    from abaqus import mdb
    from abaqusConstants import NODAL
    import desicos.abaqus.abaqus_functions as abaqus_functions

    if self.model_name in mdb.models.keys():
        part = mdb.models[self.model_name].parts[self.part_name_shell]
    else:
        text = 'The model corresponding to the active odb must be loaded'
        raise RuntimeError(text)

    elements = part.elements
    nodes = part.nodes
    sina = np.sin(self.alpharad)
    cosa = np.cos(self.alpharad)

    odb = abaqus_functions.get_current_odb()
    odbDisplay = abaqus_functions.get_current_odbdisplay()
    frame = abaqus_functions.get_current_frame()
    fieldOutputKey = odbDisplay.primaryVariable[0]
    sub_vector = odbDisplay.primaryVariable[5]

    frame_num = int(frame.frameValue)
    field = frame.fieldOutputs[fieldOutputKey]
    nodal_out = False
    if field.values[0].position == NODAL:
        nodal_out = True

    if nodal_out:
        odbSet = odb.rootAssembly.nodeSets['SHELL_FACES']
        coords = np.array([n.coordinates for n in nodes])
        labels = np.array([n.label for n in nodes])
        if ignore:
            mask = np.in1d(labels, ignore)
            labels = labels[mask]
            coords = coords[mask]
        thetas = np.arctan2(coords[:, 1], coords[:, 0])
    else:
        odbSet = odb.rootAssembly.elementSets['SHELL_FACES']
        coords = utils.vec_calc_elem_cg(elements)
        thetas = np.arctan2(coords[:, 1], coords[:, 0])

    field = field.getSubset(region=odbSet)

    attributes = {
                  'Magnitude': 'magnitude',
                  'Mises': 'mises',
                  'Min. In-Plane Principal': 'minInPlanePrincipal',
                  'Max. In-Plane Principal': 'maxInPlanePrincipal',
                  'Min. Principal': 'minPrincipal',
                  'Mid. Principal': 'midPrincipal',
                  'Max. Principal': 'maxPrincipal',
                  'Out-of-Plane Principal': 'outOfPlanePrincipal',
                  'Tresca': 'tresca',
                  'Third Invariant': 'inv3',
                 }
    components = {
                  'S11': 0,
                  'S22': 1,
                  'S33': 2,
                  'S12': 3,
                  'SF1': 0,
                  'SF2': 1,
                  'SF3': 3,
                  'SM2': 0,
                  'SM1': 1,
                  'SM3': 2,
                 }

    if sub_vector == '':
        out = np.array([val.data for val in field.values])

    elif sub_vector in attributes.keys():
        attr = attributes.get(sub_vector)
        out = np.array([getattr(v, attr) for v in field.values])

    elif sub_vector in components.keys():
        pos = components[sub_vector]
        out = np.array([v.data[pos] for v in field.values])

    elif sub_vector in ('U1', 'UT1', 'U2', 'UT2', 'U3', 'UT3'):
        uvw_rec = np.array([val.data for val in field.values])

        u1_rec = uvw_rec[:,0]
        u2_rec = uvw_rec[:,1]
        u3_rec = uvw_rec[:,2]

        u3_cyl = u3_rec
        u2_cyl = u2_rec*np.cos(thetas) - u1_rec*np.sin(thetas)
        u1_cyl = u2_rec*np.sin(thetas) + u1_rec*np.cos(thetas)

        u1_cone = u1_cyl*cosa + u3_cyl*sina
        u2_cone = u2_cyl
        u3_cone = u3_cyl*cosa - u1_cyl*sina

        displ_vecs = {'U1':u1_cone, 'U2':u2_cone, 'U3':u3_cone,
                      'UT1':u1_cone, 'UT2':u2_cone, 'UT3':u3_cone}
        out = displ_vecs[sub_vector]

    else:
        raise NotImplementedError('{0} cannot be used!'.format(
            sub_vector))

    if not nodal_out:
        firstElement = None
        numIntPts = 0
        for v in field.values:
            if firstElement is None:
                firstElement = v.elementLabel
            if v.elementLabel == firstElement:
                numIntPts += 1
            else:
                break
        out = out.reshape(-1, numIntPts).mean(axis=1)

    if 'S8' in self.elem_type and nodal_out:
        el_coords, el_out = _nodal_field_S8_add_centroids(elements, labels, out)
        el_thetas = np.arctan2(el_coords[:, 1], el_coords[:, 0])
        coords = np.vstack((coords, el_coords))
        thetas = np.hstack((thetas, el_thetas))
        out = np.hstack((out, el_out))
        num_thetas = 2*self.numel_r
    else:
        num_thetas = self.numel_r

    zs = coords[:, 2]
    return _sort_field_data(thetas, zs, out, num_thetas)


def extract_fiber_orientation(self, ply_index, use_elements):
    if use_elements:
        from abaqus import mdb

        if self.model_name in mdb.models.keys():
            part = mdb.models[self.model_name].parts[self.part_name_shell]
        else:
            raise RuntimeError("Cannot obtain element locations, model for '{0}' is not loaded".format(self.model_name))

        elements = part.elements
        coords = utils.vec_calc_elem_cg(elements)
        thetas = np.arctan2(coords[:, 1], coords[:, 0])
        zs = coords[:, 2]
    else:
        thetas = np.linspace(-np.pi, np.pi, self.numel_r + 1)
        thetas = (thetas[:-1] + thetas[1:]) / 2
        mean_circumf = np.pi*(self.rtop + self.rbot)
        # Estimate num elements in vertical direction
        numel_z = int(np.ceil(float(self.L) / mean_circumf * self.numel_r))
        zs = np.linspace(0, self.H, numel_z + 1)
        zs = (zs[:-1] + zs[1:]) / 2
        thetas, zs = np.meshgrid(thetas, zs)
        thetas = thetas.flatten()
        zs = zs.flatten()
        # Determine coords
        rs = self.fr(zs)
        xs = rs*np.cos(thetas)
        ys = rs*np.sin(thetas)
        coords = np.column_stack([xs, ys, zs])
    out = np.array(self.impconf.ppi.fiber_orientation(ply_index, coords))

    return _sort_field_data(thetas, zs, out, self.numel_r)


def extract_thickness_data(self):
    from abaqus import mdb

    if self.model_name in mdb.models.keys():
        part = mdb.models[self.model_name].parts[self.part_name_shell]
    else:
        raise RuntimeError("Cannot obtain element locations, model for '{0}' is not loaded".format(self.model_name))

    elements = part.elements
    coords = utils.vec_calc_elem_cg(elements)
    thetas = np.arctan2(coords[:, 1], coords[:, 0])
    zs = coords[:, 2]
    labels = coords[:, 3]
    thicks = np.zeros_like(zs)
    for layup in part.compositeLayups.values():
        if not layup.suppressed:
            el_set = part.sets[layup.plies[0].region[0]]
            layup_els = np.array([e. label for e in el_set.elements])
            layup_thickness = sum(p.thickness for p in layup.plies.values())
            thicks[np.in1d(labels, layup_els)] = layup_thickness
    return _sort_field_data(thetas, zs, thicks, self.numel_r)


def _nodal_field_S8_add_centroids(elements, node_labels, node_values):
    # For S8 elements and nodal fields, one may want to add values for the
    # centroids as well, to create a regular grid. This is done by
    # interpolation.
    # Values of interpolation functions at centroid: -0.25 for corner
    # nodes, 0.5 for side nodes
    INTERP = np.array([-0.25, -0.25, -0.25, -0.25, 0.5, 0.5, 0.5, 0.5])

    el_coords = utils.vec_calc_elem_cg(elements)
    el_out = np.zeros((el_coords.shape[0], ))
    for i, el in enumerate(elements):
        # el.connectivity can't be used, as it uses node indices, not labels
        mask = np.in1d(node_labels, [n.label for n in el.getNodes()])
        el_out[i] = np.dot(INTERP, node_values[mask])
    # return coords, values for element centroids
    return el_coords[:,:3], el_out


def _sort_field_data(thetas, zs, values, num_thetas):
    # Sort unorganized field data and put it into a matrix

    # First sort, by z
    asort = zs.argsort()
    zs = zs[asort].reshape(-1, num_thetas)
    thetas = thetas[asort].reshape(-1, num_thetas)
    values = values[asort].reshape(-1, num_thetas)

    # Second sort, by theta
    asort = thetas.argsort(axis=1)
    for i, asorti in enumerate(asort):
        zs[i,:] = zs[i,:][asorti]
        thetas[i,:] = thetas[i,:][asorti]
        values[i,:] = values[i,:][asorti]

    return thetas, zs, values


def transform_plot_data(self, thetas, zs, plot_type):
    sina = np.sin(self.alpharad)
    cosa = np.cos(self.alpharad)

    valid_plot_types = (1, 2, 3, 4, 5)
    if not plot_type in valid_plot_types:
        raise ValueError('Valid values for plot_type are:\n\t\t' +
                         ' or '.join(map(str, valid_plot_types)))

    H = self.H
    rtop = self.rtop
    rbot = self.rbot
    L = H/cosa

    def fr(z):
        return rbot - z*sina/cosa

    if self.alpharad == 0.:
        plot_type = 4
    if plot_type == 1:
        r_plot = fr(zs)
        if self.alpharad==0.:
            r_plot_max = L
        else:
            r_plot_max = rtop/sina + L
        y = r_plot_max - r_plot*np.cos(thetas*sina)
        x = r_plot*np.sin(thetas*sina)
    elif plot_type == 2:
        r_plot = fr(zs)
        y = r_plot*np.cos(thetas*sina)
        x = r_plot*np.sin(thetas*sina)
    elif plot_type == 3:
        r_plot = fr(zs)
        r_plot_max = rtop/sina + L
        y = r_plot_max - r_plot*np.cos(thetas)
        x = r_plot*np.sin(thetas)
    elif plot_type == 4:
        x = fr(zs)*thetas
        y = zs
    elif plot_type == 5:
        x = fr(0)*thetas
        y = zs
    return x, y


def plot_field_data(self, x, y, field, create_npz_only, ax, figsize, save_png,
        aspect, clean, outpath, pngname, npzname, pyname, num_levels,
        show_colorbar, lines):
    npzname = npzname.split('.npz')[0] + '.npz'
    pyname = pyname.split('.py')[0] + '.py'
    pngname = pngname.split('.png')[0] + '.png'

    npzname = os.path.join(outpath, npzname)
    pyname = os.path.join(outpath, pyname)
    pngname = os.path.join(outpath, pngname)

    if lines: # not empty or None
        # Concatenate all lines into a single matrix, separated by 'sep'
        sep = np.array([[float('NaN')], [float('NaN')]])
        all_lines = (2*len(lines) - 1)*[sep]
        all_lines[::2] = [np.array(l, copy=False) for l in lines]
        line = np.hstack(all_lines)
    else:
        line = np.empty((2, 0))

    if not create_npz_only:
        try:
            import matplotlib.pyplot as plt
            import matplotlib
        except:
            create_npz_only = True

    if not create_npz_only:
        levels = np.linspace(field.min(), field.max(), num_levels)
        if ax is None:
            fig = plt.figure(figsize=figsize)
            ax = fig.add_subplot(111)
        else:
            if isinstance(ax, matplotlib.axes.Axes):
                ax = ax
                fig = ax.figure
                save_png = False
            else:
                raise ValueError('"ax" must be an Axes object')
        contours = ax.contourf(x, y, field, levels=levels)
        if show_colorbar:
            plt.colorbar(contours, ax=ax, shrink=0.5, format='%.4g', use_gridspec=True)
        ax.plot(line[0,:], line[1,:], 'k-', linewidth=0.5)
        ax.grid(False)
        ax.set_aspect(aspect)
        #ax.set_title(
            #r'$PL=20 N$, $F_{{C}}=50 kN$, $w_{{PL}}=\beta$, $mm$')
        if clean:
            ax.xaxis.set_ticks_position('none')
            ax.yaxis.set_ticks_position('none')
            ax.xaxis.set_ticklabels([])
            ax.yaxis.set_ticklabels([])
            ax.set_frame_on(False)
        else:
            ax.xaxis.set_ticks_position('bottom')
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks([-self.rbot*np.pi, 0, self.rbot*np.pi])
            ax.xaxis.set_ticklabels([r'$-\pi$', '$0$', r'$+\pi$'])
        if save_png:
            log('')
            log('Plot saved at: {0}'.format(pngname))
            plt.tight_layout()
            plt.savefig(pngname, transparent=True,
                        bbox_inches='tight', pad_inches=0.05,
                        dpi=400)

    else:
        log('Matplotlib cannot be imported from Abaqus')
    np.savez(npzname, x=x, y=y, field=field, line=line)
    with open(pyname, 'w') as f:
        f.write("import os\n")
        f.write("\n")
        f.write("import numpy as np\n")
        f.write("import matplotlib.pyplot as plt\n")
        f.write("from mpl_toolkits.axes_grid1 import make_axes_locatable\n")
        f.write("\n")
        f.write("add_title = False\n")
        f.write("tmp = np.load(r'{0}')\n".format(basename(npzname)))
        f.write("pngname = r'{0}'\n".format(basename(pngname)))
        f.write("x = tmp['x']\n")
        f.write("y = tmp['y']\n")
        f.write("field = tmp['field']\n")
        f.write("line = tmp['line']\n")
        f.write("clean = {0}\n".format(clean))
        f.write("show_colorbar = {0}\n".format(show_colorbar))
        f.write("plt.figure(figsize={0})\n".format(figsize))
        f.write("ax = plt.gca()\n")
        f.write("levels = np.linspace(field.min(), field.max(), {0})\n".format(
                num_levels))
        f.write("contours = ax.contourf(x, y, field, levels=levels)\n")
        f.write("if show_colorbar:\n")
        f.write("    divider = make_axes_locatable(ax)\n")
        f.write("    cax = divider.append_axes('right', size='5%', pad=0.05)\n")
        f.write("    cbar = plt.colorbar(contours, cax=cax, format='%.2f', use_gridspec=True,\n")
        f.write("                        ticks=[field.min(), field.max()])\n")
        f.write("    cbar.outline.remove()\n")
        f.write("    cbar.ax.tick_params(labelsize=14, pad=0., tick2On=False)\n")
        f.write("ax.plot(line[0,:], line[1,:], 'k-', linewidth=0.5)\n")
        f.write("ax.grid(False)\n")
        f.write("ax.set_aspect('{0}')\n".format(aspect))
        f.write("if add_title:\n")
        f.write("    ax.set_title(r'Abaqus, $PL=20 N$, $F_{{C}}=50 kN$, $w_{{PL}}=\\beta$, $mm$')\n")
        f.write("if clean:\n")
        f.write("    ax.xaxis.set_ticks_position('none')\n")
        f.write("    ax.yaxis.set_ticks_position('none')\n")
        f.write("    ax.xaxis.set_ticklabels([])\n")
        f.write("    ax.yaxis.set_ticklabels([])\n")
        f.write("    ax.set_frame_on(False)\n")
        f.write("else:\n")
        f.write("    ax.xaxis.set_ticks_position('bottom')\n")
        f.write("    ax.yaxis.set_ticks_position('left')\n")
        f.write("    ax.xaxis.set_ticks([{0}, 0, {1}])\n".format(
                -self.rbot*np.pi, self.rbot*np.pi))
        f.write("    ax.xaxis.set_ticklabels([r'$-\\pi$', '$0$', r'$+\\pi$'])\n")
        f.write("plt.savefig(pngname, transparent=True,\n")
        f.write("            bbox_inches='tight', pad_inches=0.05, dpi=400)\n")
        f.write("plt.show()\n")
    log('')
    log('Output exported to "{0}"'.format(npzname))
    log('Please run the file "{0}" to plot the output'.format(
          pyname))
    log('')
