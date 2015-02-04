import numpy as np

import _read_outputs


def read_outputs(self, last_frame=False, last_cross_section=True,
        read_fieldOutputs=False):

    if not self.check_completed():
        print 'ERROR! Output not found for model %s !' % self.model_name
        return False

    # this is required to avoid an error for corrupted odbs
    try:
        odb = self.attach_results()
    except:
        print 'ERROR - Probably %s.odb is corrupted' % self.model_name
        return False

    if self.linear_buckling:
        pcrs = []
        for frame in odb.steps[self.step1Name].frames:
            description = frame.description
            if description.find('EigenValue') > -1:
                pcr = float(description.split('EigenValue =')[1].strip())
                pcrs.append(pcr)
        self.zdisp = np.linspace(       0., self.axial_displ or 1., 10)
        self.zload = np.linspace(min(pcrs),              min(pcrs), 10)
        self.detach_results(odb)
        return True

    _read_outputs._read_axial_load_displ_history(self, odb)

    return True


def _read_outputs_cross_section(cc, odb, cross_section_index=-1,
        last_frame=False):
    cross_section = cc.cross_sections[cross_section_index]
    _read_outputs._read_outputs_entity(cc, odb, cross_section, last_frame)


def _read_outputs_meridian(cc, odb, meridian_index=0, last_frame=False):
    meridian = cc.meridians[meridian_index]
    _read_outputs._read_outputs_entity(cc, odb, meridian, last_frame)


def _read_outputs_entity(cc, odb, entity, last_frame=False):
    setname = '%s_%03d' % (entity.prefix, entity.index)
    #TODO this if below is temporary... the meridians should not be even created
    #     if they have not nodes associated
    if len(entity.nodes) == 0:
        return
    odb_mesh_node_array = odb.rootAssembly.instances['INSTANCECYLINDER'].\
                              nodeSets[setname]
    step_names = odb.steps.keys()
    nodes = entity.nodes
    # reseting values
    nodes_dict = {}
    for node in nodes:
        if node == None:
            continue
        nodes_dict[node.id] = node
        for step_name in step_names:
            frmlen = len(odb.steps[step_name].frames)
            node.dx[step_name] = [None for i in range(frmlen)]
            node.dy[step_name] = [None for i in range(frmlen)]
            node.dz[step_name] = [None for i in range(frmlen)]
            node.dr[step_name] = [None for i in range(frmlen)]
            # for NFORC outputs a starting float value is required
            # because there are more then one nodeLabel value
            #node.fx[step_name] = [0. for i in range(frmlen)]
            #node.fy[step_name] = [0. for i in range(frmlen)]
            node.fz[step_name] = [0.   for i in range(frmlen)]
    # reading new values
    for step_name in step_names:
        frames = odb.steps[step_name].frames
        #
        if last_frame:
            frm_list = [-1]
        else:
            frm_list = range(len(frames))
        for i in frm_list:
            frame = frames[i]
            #
            if 'UT' in frame.fieldOutputs.keys():
                fOut = frame.fieldOutputs['UT']
            else:
                fOut = frame.fieldOutputs['U']
            subfOut = fOut.getSubset(region=odb_mesh_node_array)
            subfOutValues = subfOut.values
            for value in subfOutValues:
                node_id = value.nodeLabel
                #if not node_id in nodes_dict.keys():
                #    continue
                node = nodes_dict[node_id]
            #for value in frame.fieldOutputs['NFORC1'].values:
            #    node_id = value.nodeLabel
            #    tmp['NFORC1'][step_name][node_id] = value.data
            #for value in frame.fieldOutputs['NFORC2'].values:
            #    node_id = value.nodeLabel
            #    tmp['NFORC2'][step_name][node_id] = value.data
                data = value.data
                dx = data[0]
                dy = data[1]
                dz = data[2]
                # this set of operations below could be done in a array
                thetarad = np.arctan2(dy, dx)
                dr  = dx / np.cos(thetarad)
                node.dx[step_name][i] = dx
                node.dy[step_name][i] = dy
                node.dz[step_name][i] = dz
                node.dr[step_name][i] = dr
                #
                #fx = tmp['NFORC1'][step_name][node_id]
                #
                #fy = tmp['NFORC2'][step_name][node_id]
                #
            fOut = frame.fieldOutputs['NFORC3']
            subfOut = fOut.getSubset(region=odb_mesh_node_array)
            subfOutValues = subfOut.values
            for value in subfOutValues:
                node_id = value.nodeLabel
                #if not node_id in nodes_dict.keys():
                #    continue
                node = nodes_dict[node_id]
                node.fz[step_name][i] += value.data
                #
                #node.fx[step_name] += fx
                #node.fy[step_name] += fy


def _read_axial_load_displ_history(cc, odb):
    step_name = cc.step2Name
    step = odb.steps[step_name]
    historyRegion = step.historyRegions['Node ASSEMBLY.2']
    zdisp_data = historyRegion.historyOutputs['U3'].data
    zload_data = historyRegion.historyOutputs['RF3'].data
    cc.zdisp = [value[1] for value in zdisp_data]
    if cc.displ_controlled:
        cc.zload = [-value[1] for value in zload_data]
    else:
        cc.zload = [cc.axial_load*value[0] for value in zload_data]
