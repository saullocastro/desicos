import sys
import numpy
import __main__
# local modules
sys.path.append(r'C:\Users\pfh-castro\doutorado\desicos\abaqus-conecyl-python')
import conecyl
#
lbmi = False
spli = True
gdi = False
if lbmi:
    pre = 'wp3_t03_01_lbmi_mode_01'
    names = ['wp3_t03_01_lbmi_mode_01_model_01',
             'wp3_t03_01_lbmi_mode_01_model_05',
             'wp3_t03_01_lbmi_mode_01_model_08' ]
    step_name = 'PLoad_Axial_Displ_Step'
if spli:
    pre = 'wp3_t03_01_spli'
    names = ['wp3_t03_01_spli_model_01',
             'wp3_t03_01_spli_model_05',
             'wp3_t03_01_spli_model_08' ]
    step_name = 'PLoad_Axial_Displ_Step'
cc = conecyl.ConeCyl()
session = __main__.session
for name in names:
    odb = session.odbs['C:/Temp/abaqus/%s/outputs/%s.odb' % (pre,name)]
    step = odb.steps[step_name]
    frames = step.frames
    #

    def el_theta( el ):
        nodes = el.getNodes()
        theta = 0.
        for n in nodes:
            x,y,z = n.coordinates
            theta += numpy.arctan2( y, x )
        theta /= len(nodes)
        return numpy.rad2deg(theta)
    theta_els = []
    for el in elements:
        theta = el_theta( el )
        theta_els.append( [theta, el] )
    theta_els.sort( key = lambda x: x[0] )
    thetas, els = zip( *thetas_els )
    ids = [ e.label for e in els ]
    for i, frame in enumerate( frames ):
        xs[i] = -frame.fieldOutputs['UT'].values[0].data[2]
        values = frame.fieldOutputs['SF'].values
        sf = numpy.zeros( len(theta_els), dtype=float )
        for value in values:
            label = value.elementLabel
            if label in ids:
                index = ids.index( label )
                sf[index] = value.data[0]

        cc.plot_xy( xs=thetas, ys=sf, name = 'theta_sf1_frame_%02d'%frame.frameId )

    if False:
        xs = numpy.zeros(len(frames), dtype=float)
        sf1 = xs.copy()
        sf2 = xs.copy()
        sf3 = xs.copy()
        sm1 = xs.copy()
        sm2 = xs.copy()
        sm3 = xs.copy()
        ids_pos = range(120)
        for i, frame in enumerate(frames):
            xs[i] = -frame.fieldOutputs['UT'].values[0].data[2]
            values = frame.fieldOutputs['SF'].values
            sf = numpy.zeros( (len(ids),6), dtype=float )
            for value in values:
                if value.elementLabel in ids:
                    j = ids_pos[ ids.index( value.elementLabel ) ]
                    sf[j] = value.data
            sf1[i], sf2[i], dummy, sf3[i], dummy, dummy = sf.sum(axis=0)
            values = frame.fieldOutputs['SM'].values
            sm = numpy.zeros( (len(ids),3), dtype=float )
            j = -1
            for value in values:
                if value.elementLabel in ids:
                    j = ids_pos[ ids.index( value.elementLabel ) ]
                    sm[j] = value.data[0:3]
            sm2[i], sm1[i], sm3[i] = sm.sum(axis=0)
        cc.plot_xy( xs=xs, ys=sf1, name = name + 'sf1' )
        cc.plot_xy( xs=xs, ys=sf2, name = name + 'sf2' )
        cc.plot_xy( xs=xs, ys=sf3, name = name + 'sf3' )
        cc.plot_xy( xs=xs, ys=sm1, name = name + 'sm1' )
        cc.plot_xy( xs=xs, ys=sm2, name = name + 'sm2' )
        cc.plot_xy( xs=xs, ys=sm3, name = name + 'sm3' )
