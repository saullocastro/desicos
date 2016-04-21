import os
from abaqusConstants import *
def save_curves( std = None ):
    plot_names = session.xyDataObjects.keys()
    if not 'XYPlot-1' in session.xyPlots.keys():
        xyp = session.XYPlot('XYPlot-1')
    else:
        xyp = session.xyPlots['XYPlot-1']
    myv = session.viewports['Viewport: 1']
    myv.restore()
    myv.setValues( displayedObject=xyp,
                   width  = 653.04,
                   height = 297.04,)
    myv.maximize()
    for name in plot_names:
        path = name
        if std <> None:
            path = os.path.join( std.study_dir, name )
            if name.find( std.name ) == -1:
                continue
        c = session.Curve(xyData=session.xyDataObjects[name])
        chart = session.xyPlots['XYPlot-1'].charts['Chart-1']
        chart.setValues(curvesToPlot=(c,))
        if name.find('PL_CURVE') > -1:
            chart.legend.setValues(show=False)
        else:
            chart.legend.setValues(show=False)
            chart.legend.setValues(show=True)
        session.printToFile( fileName = path, format=PNG,
                             canvasObjects=(myv,))
