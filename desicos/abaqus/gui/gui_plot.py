from abaqusGui import *

import gui_commands
reload(gui_commands)

def plot_ls_curve(std_name, put_in_Excel, open_Excel ):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'std.plot_forces( put_in_Excel = %s,\n' % str(put_in_Excel) +\
              '                 open_Excel   = %s,\n' % str(open_Excel) +\
              '                 gui          = True)\n'
    sendCommand( cmdstr )
    return True

def plot_kdf_curve(std_name, put_in_Excel, open_Excel,
                   configure_session=False ):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'std.plot( gui=True,\n' +\
                'put_in_Excel      = %s,\n' % str(put_in_Excel) +\
                'open_Excel        = %s,\n' % str(open_Excel)   +\
                'configure_session = %s,\n' % str(configure_session) + ')'
    sendCommand( cmdstr )

def plot_stress_analysis(std_name, cc_name):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'for cc in std.ccs:\n'
    cmdstr += '    if cc.jobname == "%s":\n' % cc_name
    cmdstr += '        cc.stress_analysis()\n'
    cmdstr += '        break\n'
    sendCommand( cmdstr )
    return True

def plot_opened_conecyl(std_name):
    cmdstr  = 'import __main__\n'
    cmdstr += 'import utils\n'
    cmdstr += 'odbdisplay = utils.get_odbdisplay()\n'
    cmdstr += 'if odbdisplay:\n'
    cmdstr += '    cc_name = os.path.basename(odbdisplay.name).split(".")[0]\n'
    cmdstr += '    std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += '    for cc in std.ccs:\n'
    cmdstr += '        if cc.jobname == cc_name:\n'
    cmdstr += '            cc.plot_opened_conecyl()\n'
    cmdstr += '            break\n'
    cmdstr += 'else:\n'
    cmdstr += '    print("No active odb found!")\n'
    sendCommand( cmdstr )
    return True


