import os
import cPickle as pickle
import traceback

import numpy as np
from numpy import arctan2, sin, cos, pi

import utils
from constants import TMP_DIR

def plot_xyz( x,y,z ):
    import mpl_toolkits.mplot3d.axes3d as p3
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    ax = p3.Axes3D( fig )
    ax.scatter( x, y, z )
    fig.add_axes( ax )
    plt.show()
    return fig

def plot_xy_contour( x,y,contour, grid=500 ):
    from scipy.interpolate import griddata
    import matplotlib.pyplot as plt
    from matplotlib import cm
    x.shape = len(x),1
    y.shape = len(y),1
    xy = np.concatenate( (x,y), axis = 1 )
    xi = np.linspace( x.min(), x.max(), grid )
    yi = np.linspace( y.min(), y.max(), grid )
    xx,yy = np.meshgrid( xi, yi )
    zz = griddata( xy, contour, (xx,yy), method='nearest' )
    zz.shape = len(zz),len(zz)
    fig = plt.figure()
    plt.pcolor( xx,yy,zz , cmap=cm.jet)
    plt.colorbar()
    plt.show()
    return fig

def plot_xyzt (x,y,z,t):
    import matplotlib.pyplot as plt
    from matplotlib import cm
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    x, y = np.meshgrid(x, y)
    contour = t/t.max()  # normalize 0..1
    surf = ax.plot_surface(
        x, y, z, rstride=1, cstride=1,
        facecolors=cm.jet(contour),
        linewidth=0, antialiased=False, shade=False)
    plt.show()
    return fig

def plot_xyz_from_txt_file(filename, sample=None):
    xyz = np.loadtxt(filename)
    if sample:
        xyz = utils.sample_array(xyz, sample)
    x = xyz[:,0]
    y = xyz[:,1]
    z = xyz[:,2]
    fig = plot_xyz( x, y, z )
    return fig

def plot_opened_conecyl(cc, displ_vec='w',
        figsize=(3.3, 3.3), aspect='equal', clean=True,
        frame=None, figname='', plot_type=1):
    workingplt = True
    try:
        import matplotlib.pyplot as plt
    except:
        workingplt = False
    '''Prints the opened cylinder with the active output

    '''
    # if index=0 there is no reference point RP in the model
    #            at the assembly level
    for index in [0, 1]:
        try:
            if not frame:
                frame = utils.get_current_frame()
            if not frame:
                raise ValueError('A frame must be selected!')
            frame_num = int(frame.frameValue)
            print 'DEBUG, len(cc.part.nodes)', len(cc.part.nodes)
            coords = np.array([n.coordinates for n in cc.part.nodes])
            #TODO include more outputs like stress etc
            try:
                field = frame.fieldOutputs['UT']
            except:
                field = frame.fieldOutputs['U']

            uvw_rec = np.array([val.data for val in field.values][index:])
            u_rec = uvw_rec[:,0]
            v_rec = uvw_rec[:,1]
            w_rec = uvw_rec[:,2]

            res_alpha = arctan2(v_rec, u_rec)

            thetas = arctan2(coords[:, 1], coords[:, 0])
            #thetas[thetas<0.] += 2*pi

            r_rec = (u_rec**2 + v_rec**2)**0.5
            v = r_rec*sin((-thetas + res_alpha))
            w = (r_rec*cos((-thetas + res_alpha))*cos(cc.alpharad)
                 + w_rec*sin(cc.alpharad))
            u = -w_rec*cos(cc.alpharad) + r_rec*sin(cc.alpharad)

            displ_vecs = {'u':u, 'v':v, 'w':w}
            uvw = displ_vecs[displ_vec]

            zs = coords[:, 2]

            print 'DEBUG - cc.numel_r', cc.numel_r
            nt = cc.numel_r

            if 'S8' in cc.elem_type:
                print 'WARNING - S8xx elements'
                nt *= 2

            #first sort
            asort = zs.argsort()
            zs = zs[asort].reshape(-1, nt)
            thetas = thetas[asort].reshape(-1, nt)
            uvw = uvw[asort].reshape(-1, nt)

            #second sort
            asort = thetas.argsort(axis=1)
            for i, asorti in enumerate(asort):
                zs[i,:] = zs[i,:][asorti]
                thetas[i,:] = thetas[i,:][asorti]
                uvw[i,:] = uvw[i,:][asorti]

            sina = sin(cc.alpharad)
            cosa = cos(cc.alpharad)

            H = cc.h
            r2 = cc.r2
            r1 = cc.r
            L = H/cosa

            def fr(z):
                return r1 - z*sina/cosa

            if cc.alpharad==0.:
                plot_type=4
            if plot_type==1:
                r_plot = fr(zs)
                if cc.alpharad==0.:
                    r_plot_max = L
                else:
                    r_plot_max = r2/sina + L
                y = r_plot_max - r_plot*cos(thetas*sina)
                print 'HERE', y.min(), y.max()
                x = r_plot*sin(thetas*sina)
            elif plot_type==2:
                r_plot = fr(zs)
                y = r_plot*cos(thetas*sina)
                x = r_plot*sin(thetas*sina)
            elif plot_type==3:
                r_plot = fr(zs)
                r_plot_max = r2/sina + L
                y = r_plot_max - r_plot*cos(thetas)
                x = r_plot*sin(thetas)
            elif plot_type==4:
                x = fr(zs)*thetas
                y = zs
            elif plot_type==5:
                x = thetas
                y = zs

            CIRCUM = x
            MERIDIAN = y
            FIELD = uvw

            npzname = os.path.join(TMP_DIR, 'abaqus_output.npz')
            pyname = os.path.join(TMP_DIR, 'abaqus_output_plot.py')
            if workingplt:
                plt.figure(figsize=figsize)
                ax = plt.gca()
                levels = np.linspace(FIELD.min(), FIELD.max(), 400)
                ax.contourf(CIRCUM, MERIDIAN, FIELD, levels=levels)
                ax.grid(False)
                ax.set_aspect(aspect)
                ax.xaxis.set_ticks_position('bottom')
                ax.yaxis.set_ticks_position('left')
                lim = cc.r2*pi
                #ax.xaxis.set_ticks([-lim, 0, lim])
                #ax.xaxis.set_ticklabels([r'$-\pi$', '$0$', r'$+\pi$'])
                #ax.set_title(
                    #r'$PL=20 N$, $F_{{C}}=50 kN$, $w_{{PL}}=\beta$, $mm$')
                if clean:
                    ax.xaxis.set_ticks_position('none')
                    ax.yaxis.set_ticks_position('none')
                    ax.xaxis.set_ticklabels([])
                    ax.yaxis.set_ticklabels([])
                    ax.set_frame_on(False)
                if not figname:
                    figname = 'abaqus_output.png'
                filename =  os.path.join(TMP_DIR, figname)
                print('Plot saved at: {0}'.format(filename))
                plt.tight_layout()
                plt.savefig(filename, transparent=True, bbox_inches='tight',
                            pad_inches=0.05, dpi=300)

            else:
                print('Matplotlib cannot be imported from Abaqus')
            np.savez(npzname, CIRCUM=CIRCUM,
                    MERIDIAN=MERIDIAN, FIELD=FIELD)
            with open(pyname, 'w') as f:
                f.write(
r'''import os

import numpy as np
import matplotlib.pyplot as plt
tmp = np.load('abaqus_output.npz')
CIRCUM = tmp['CIRCUM']
MERIDIAN = tmp['MERIDIAN']
FIELD = tmp['FIELD']
clean = {clean}
figname = '{figname}'
plt.figure(figsize={figsize})
ax = plt.gca()
levels = np.linspace(FIELD.min(), FIELD.max(), 400)
ax.contourf(CIRCUM, MERIDIAN, FIELD, levels=levels)
ax.grid(b=None)
ax.set_aspect('{aspect}')
ax.xaxis.set_ticks_position('bottom')
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks([{mintick}, 0, {maxtick}])
ax.xaxis.set_ticklabels([r'$-\pi$', '$0$', r'$+\pi$'])
ax.set_title(
    r'Abaqus, $PL=20 N$, $F_{{C}}=50 kN$, $w_{{PL}}=\beta$, $mm$')
if clean:
    ax.xaxis.set_ticks_position('none')
    ax.yaxis.set_ticks_position('none')
    ax.xaxis.set_ticklabels([])
    ax.yaxis.set_ticklabels([])
    ax.set_frame_on(False)
if not figname:
    figname = 'abaqus_result.png'
plt.savefig(figname, transparent=True,
            bbox_inches='tight', pad_inches=0.05, dpi=300)
plt.show()
'''.format(clean=clean, figname=figname, figsize=figsize, aspect=aspect,
           mintick=-cc.r2*pi, maxtick=cc.r2*pi))
            print('Output exported to "{0}"'.format(npzname))
            print('Please run the file "{0}" to plot the output'.format(
                  pyname))
            return CIRCUM, MERIDIAN, FIELD
        except:
            traceback.print_exc()
    print('Opened plot could not be generated! :(')

if __name__ == '__main__':
    for index in range(1, 32, 2):
        figname = 'z33_mode_{0:02d}.png'.format(index)
        frame = odb.steps['Linear_Buckling_Step'].frames[index]
        a, b, c = plot_opened_conecyl(cc, clean=True,
                            frame=frame, displ_vec='w', figname=figname)

