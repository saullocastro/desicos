from abaqusGui import *

import gui_commands
reload(gui_commands)


def plot_ls_curve(std_name, put_in_Excel, open_Excel):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'std.plot_forces(put_in_Excel = %s,\n' % str(put_in_Excel) +\
              '                open_Excel = %s,\n' % str(open_Excel) +\
              '                gui = True)\n'
    sendCommand(cmdstr)
    return True


def plot_kdf_curve(std_name, put_in_Excel, open_Excel,
                   configure_session=False):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'std.plot(gui = True,\n' +\
                'put_in_Excel = %s,\n' % str(put_in_Excel) +\
                'open_Excel = %s,\n' % str(open_Excel) +\
                'configure_session = %s,\n' % str(configure_session) + ')'
    sendCommand(cmdstr)


def plot_stress_analysis(std_name, cc_name):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'for cc in std.ccs:\n'
    cmdstr += '    if cc.model_name == "%s":\n' % cc_name
    cmdstr += '        cc.stress_analysis()\n'
    cmdstr += '        break\n'
    sendCommand(cmdstr)
    return True


def plot_opened_conecyl(std_name, plot_type, outpath):
    cmdstr  = 'import __main__\n'
    cmdstr += 'import desicos.abaqus.abaqus_functions as abaqus_functions\n'
    cmdstr += 'odbdisplay = abaqus_functions.get_current_odbdisplay()\n'
    cmdstr += 'if odbdisplay:\n'
    cmdstr += '    cc_name = os.path.basename(odbdisplay.name).split(".")[0]\n'
    cmdstr += '    fieldOutputKey = odbdisplay.primaryVariable[0]\n'
    cmdstr += '    std = __main__.stds["{0}"]\n'.format(std_name)
    cmdstr += '    for cc in std.ccs:\n'
    cmdstr += '        if cc.model_name == cc_name:\n'
    cmdstr += '            cc.plot_opened(plot_type={0},\n'.format(plot_type)
    cmdstr += '                           outpath=r"{0}")\n'.format(outpath)
    cmdstr += '            break\n'
    cmdstr += 'else:\n'
    cmdstr += '    print("No active odb found!")\n'
    try:
        sendCommand(cmdstr)
    except:
        sendCommand("print('AbaqusException: VisError: " +
                    "The current viewport is not associated with " +
                    "an output database file. " +
                    "Requested operation cancelled.')")
    return True


