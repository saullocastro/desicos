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


def plot_MEA_curve(std_name, put_in_Excel, open_Excel):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'std.plot_R1_forces(put_in_Excel = %s,\n' % str(put_in_Excel) +\
              '                open_Excel = %s,\n' % str(open_Excel) +\
              '                gui = True)\n'
    sendCommand(cmdstr)
    return True


def plot_RF1U3_curve(std_name, put_in_Excel, open_Excel):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "%s" ]\n' % std_name
    cmdstr += 'std.plot_RF1U3_forces(put_in_Excel = %s,\n' % str(put_in_Excel) +\
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


def plot_ppi(std_name, cc_name, ply_index, plot_type):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "{0}" ]\n'.format(std_name)
    cmdstr += 'for cc in std.ccs:\n'
    cmdstr += '    if cc.model_name == "{0}":\n'.format(cc_name)
    cmdstr += '        cc.plot_orientation_opened(use_elements=True, ply_index={0}, plot_type={1}, outpath=std.study_dir)\n'.format(ply_index, plot_type)
    cmdstr += '        break\n'
    sendCommand(cmdstr)
    return True


def plot_msi(std_name, cc_name, plot_type):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "{0}" ]\n'.format(std_name)
    cmdstr += 'for cc in std.ccs:\n'
    cmdstr += '    if cc.model_name == "{0}":\n'.format(cc_name)
    cmdstr += '        cc.plot_msi_opened(plot_type={0}, outpath=std.study_dir)\n'.format(plot_type)
    cmdstr += '        break\n'
    sendCommand(cmdstr)
    return True


def plot_ti(std_name, cc_name, plot_type):
    cmdstr  = 'import __main__\n'
    cmdstr += 'std = __main__.stds[ "{0}" ]\n'.format(std_name)
    cmdstr += 'for cc in std.ccs:\n'
    cmdstr += '    if cc.model_name == "{0}":\n'.format(cc_name)
    cmdstr += '        cc.plot_thickness_opened(plot_type={0}, outpath=std.study_dir)\n'.format(plot_type)
    cmdstr += '        break\n'
    sendCommand(cmdstr)
    return True


def plot_opened_conecyl(plot_type):
    cmdstr  = 'import __main__\n'
    cmdstr += 'import desicos.abaqus.abaqus_functions as abaqus_functions\n'
    cmdstr += '\n'
    cmdstr += 'odbdisplay = abaqus_functions.get_current_odbdisplay()\n'
    cmdstr += 'if odbdisplay is None:\n'
    cmdstr += '    raise RuntimeError("An odb file must be associated with the current Viewport")\n'
    cmdstr += '\n'
    cmdstr += 'cc_name = os.path.basename(odbdisplay.name).split(".")[0]\n'
    cmdstr += 'if "_lb" in cc_name:\n'
    cmdstr += '   std_name = cc_name[:-3]\n'
    cmdstr += 'else:\n'
    cmdstr += '   num = len("_model_") + len(cc_name.split("_")[-1])\n'
    cmdstr += '   std_name = cc_name[:-num]\n'
    cmdstr += '\n'
    cmdstr += 'if not "stds" in dir(__main__):\n'
    cmdstr += '    raise RuntimeError("A study must be loaded or created")\n'
    cmdstr += 'if std_name in __main__.stds.keys():\n'
    cmdstr += '    std = __main__.stds[std_name]\n'
    cmdstr += 'else:\n'
    cmdstr += '    raise RuntimeError("The study corresponding to the active odb must be loaded or created")\n'
    cmdstr += '\n'
    cmdstr += 'for cc in std.ccs:\n'
    cmdstr += '    if cc.model_name == cc_name:\n'
    cmdstr += '        cc.plot_current_field_opened(plot_type={0},\n'.format(plot_type)
    cmdstr += '                                     outpath=std.study_dir)\n'
    cmdstr += '        break\n'
    sendCommand(cmdstr)

    return True



