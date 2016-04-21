import numpy as np
from mpl_toolkits.mplot3d import Axes3D

import GUIPlot
from desicos.constants import TOL


# Some constants that are used for both 2D and 3D plots
LABEL_MAP = {
    'angle' : 'Fiber Angle in Degree',
    'start' : 'Starting Position in mm',
    'width' : 'Maximum width in mm',
    'var' : 'Width Variation',
}

COLORS = 'brgcm'

Z_NAMES = ["Ratio of continous fibers", "Ratio of effective area",
          "Degree of Coverage", "Ratio of total effective area",
          "Ratio of total effectiveness"]


def printResults3D(result_handle, data_handle, axes_info, result_types):
    # This function uses the matplotlib to make a 3D-Graph
    #
    # Input:
    #   result_handle Object, containing the Results
    #   data_handle   Object, containing the parameters of the study
    #   axes_info     List of strings, Descritption of Axes
    #   result_types  List of booleans, indicating whether to show each result

    # Make result_types a list of integers
    result_list = [i for i, r in enumerate(result_types) if r]

    # Set Names and limits of Graphic axes
    xAxis, yAxis = axes_info
    xName = LABEL_MAP[xAxis]
    yName = LABEL_MAP[yAxis]
    xAxisData = getattr(data_handle, xAxis)
    yAxisData = getattr(data_handle, yAxis)

    title_parts = []
    if data_handle.width.fix:
        title_parts.append('Maximum Width: %.1f mm' % data_handle.width.min_value)
    if data_handle.start.fix:
        title_parts.append('Starting Position: %.1f mm' % data_handle.start.min_value)
    if data_handle.angle.fix:
        title_parts.append('Fiber Angle: %.1f Degree' % data_handle.angle.min_value)
    if data_handle.var.fix:
        title_parts.append('Width Variation: %.2f' % data_handle.var.min_value)
    GraphTitle = 'Parametric Ply Piece Study\n ' + ', '.join(title_parts)

    # Sort To max (Reduces memory use)
    SortedData = []
    for res in result_list:
        SortedData.append(sortToMax3D(result_handle, data_handle, res, xAxis, yAxis))

    window = GUIPlot.PlotWindow()
    fig = window.qmc.fig
    ax = fig.add_subplot(111, projection='3d')

    # Limits for 3D-Graph
    xMin = xAxisData.min_value - 0.01
    xMax = xAxisData.max_value + 0.01
    yMin = yAxisData.min_value - 0.01
    yMax = yAxisData.max_value + 0.01
    zMin = 1.0
    zMax = 0.0

    for i, res in enumerate(result_list):
        x, y, z = SortedData[i]
        zMin = min(zMin, min(z))
        zMax = max(zMax, max(z))
        ax.plot(x, y, z, '.', color=COLORS[i], label=Z_NAMES[res])

    ax.set_xlabel(xName)
    ax.set_ylabel(yName)
    ax.set_zlabel('Ratio')

    ax.legend(loc='upper left', numpoints=1, bbox_to_anchor=(1, 1))
    ax.set_title(GraphTitle)

    ax.axis([xMin, xMax, yMin, yMax])
    ax.set_zlim(zMin*0.99, zMax*1.01)

    window.show()
    return window


def sortToMax3D(result_handle, data_handle, result_type, xAxis, yAxis):
    # result_type:      0: R_cont
    #                   1: R_Aeff
    #                   2: DoC
    #                   3: R_SumAeff
    #                   4: R_total
    # returns x, y, z
    DATA_COLUMNS = [11, 10, 9, 12, 13]
    col = DATA_COLUMNS[result_type]

    xData = np.array([getattr(r, xAxis) for r in result_handle.get()])
    yData = np.array([getattr(r, yAxis) for r in result_handle.get()])
    zData = np.array([r[col] for r in result_handle.get()])

    xOut = []
    yOut = []
    zOut = []

    for x in getattr(data_handle, xAxis).steps():
        xIndices = abs(xData - x) < TOL
        yFilt = yData[xIndices]
        zFilt = zData[xIndices]
        for y in getattr(data_handle, yAxis).steps():
            yIndices = abs(yFilt - y) < TOL
            zFiltFilt = zFilt[yIndices]
            xOut.append(x)
            yOut.append(y)
            zOut.append(zFiltFilt.max() if len(zFiltFilt) > 0 else 0.0)

    return xOut, yOut, zOut


def printResults2D(result_handle, data_handle, axes_info, result_types):
    # Make result_types a list of integers
    result_list = [i for i, r in enumerate(result_types) if r]

    num_graphs = len(axes_info)
    subplot_rows = 1 if num_graphs == 1 else 2
    subplot_cols = 1 if num_graphs <= 2 else 2

    window = GUIPlot.PlotWindow()
    fig = window.qmc.fig
    for i, axis_name in enumerate(axes_info):
        ax = fig.add_subplot(subplot_rows, subplot_cols, i + 1)
        for j, res in enumerate(result_list):
            x, y, data = sortToMax2D(result_handle, data_handle, res, axis_name)
            ax.plot(x, y, COLORS[j], label=Z_NAMES[res], marker='.')

            # Add annotations stating the values of the other parameters
            if num_graphs in (2, 3):
                other_axes = [a for a in axes_info if a != axis_name]
                for oa_num, other_axis in enumerate(other_axes):
                    ax.annotate(LABEL_MAP[other_axis], xy=(x[0], y[0]),
                        xycoords='data', xytext=(-120, 10 + 10*oa_num),
                        textcoords='offset points',color=COLORS[j])
                    for k, xk, yk, datak in zip(range(len(x)), x, y, data):
                        if datak is None:
                            continue
                        ax.annotate(str(getattr(datak, other_axis)), xy=(xk, yk),
                            xycoords='data', xytext=(0, 10 + 10*(oa_num + (k%3))),
                            textcoords='offset points',color=COLORS[j])

        ax.set_xlabel(LABEL_MAP[axis_name])
        ax.set_ylabel('Ratios')
        param = getattr(data_handle, axis_name)
        ax.set_xlim(param.min_value, param.max_value)
        ax.set_ylim(-0.1, 1.1)

    # Add legend to last subplot
    ax.legend(loc='upper left', numpoints=1, bbox_to_anchor=(1,1))

    window.show()
    return window


def sortToMax2D(result_handle, data_handle, result_type, xAxis):
    # result_type:      0: R_cont
    #                   1: R_Aeff
    #                   2: DoC
    #                   3: R_SumAeff
    #                   4: R_total
    # returns x, y, data
    DATA_COLUMNS = [11, 10, 9, 12, 13]
    col = DATA_COLUMNS[result_type]

    results = result_handle.get()
    xData = np.array([getattr(r, xAxis) for r in results])
    yData = np.array([r[col] for r in results])
    indices = np.array(range(len(results)))

    xOut = []
    yOut = []
    dataOut = []

    for x in getattr(data_handle, xAxis).steps():
        xIndices = abs(xData - x) < TOL
        yFilt = yData[xIndices]
        xOut.append(x)
        if len(yFilt) > 0:
            max_ind = yFilt.argmax()
            yOut.append(yFilt[max_ind])
            # We cannot filter an ordinary list by index, so use a workaround
            res_ind = indices[xIndices][max_ind]
            dataOut.append(results[res_ind])
        else:
            yOut.append(0.0)
            dataOut.append(None)

    return xOut, yOut, dataOut
