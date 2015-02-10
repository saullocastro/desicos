import numpy as np
from numpy import deg2rad, rad2deg, pi

from desicos.conecylDB.interpolate import interp


class Shim(object):
    """Represents a shim added to one of the edges

    ============== =========================================================
    Attributes     Description
    ============== =========================================================
    edge           An object of the class :class:`.UnevenTopEdge`
    thetadeg       The circumferential position where the shim starts
    thick          The shim thickness
    width          The shim perimetrical width (along the shell perimeter)
    ============== =========================================================

    """
    def __init__(self,thetadeg, thick, width, edge=None):
        self.thetadeg = thetadeg
        self.thick = thick
        self.width = width
        self.edge = edge
        if edge is not None:
            self.edge.shims.append(self)


class UnevenBottomEdge(object):
    """Uneven Bottom Edge

    The following attributes are taken into account:
    - misalignment of the bottom edge
    - presence of shims
    - measured uneven edge points

    ============== =========================================================
    Attributes     Description
    ============== =========================================================
    betadeg        Misalignment of the bottom edge in degrees
    omegadeg       Azimuth angle of the bottom edge misalignment in degrees.
    shims          ``list`` of shims included to this edge
    measured_u3s   Measured points describing the edge imperfection
    ============== =========================================================

    """
    def __init__(self, betadeg=None, omegadeg=None):
        self.name = 'uneven_bottom_edge'
        self.index = None
        self.impconf = None
        self.thetadegs = []
        self.pts = []
        self.shims = []
        self.measured_u3s = None
        self.scaling_factor = 1.
        # plotting options
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Scaling factor'


    def __nonzero__(self): # in Python 3 this method was renamed to __bool__
        return self.__bool__()


    def __bool__(self):
        cc = self.impconf.conecyl
        return (bool(self.shims) or bool(self.measured_u3s is not None) or
                bool(cc.bc_gaps_bottom_edge))


    def rebuild(self):
        cc = self.impconf.conecyl
        self.thetadegs = [s.thetadeg for s in self.shims]
        self.thetadegs += [s.thetadeg + 360*s.width/(2*pi*cc.rbot)
                           for s in self.shims]
        self.pts = []


    def add_measured_u3s(self, thetadegs, u3s):
        """Adds measured data to the uneven bottom edge

        The edge imperfection that actually goes for each node is a linear
        interpolation of the measured values.

        Parameters
        ----------
        thetadegs : list
            The circumferential positions where the imperfect bottom edge was
            measured, in degrees.
        u3s : list
            The measured imperfections representing displacements along the
            `X_3` axis :ref:`of the adopted model <figure_conecyl>`.

        """
        if len(thetadegs) != len(u3s):
            raise ValueError('thetadegs must have the same length of u3s!')
        self.measured_u3s = np.array([thetadegs, u3s])


    def add_shim(self, thetadeg, thick, width):
        """Adds a shim to the uneven bottom edge

        Parameters
        ----------
        thetadeg : float
            Circumferential position where the shim starts.
        thick : float
            Thickness of the shim.
        width : float
            Perimetrical width of the shim (along the shell perimeter).

        Returns
        -------
        shim : :class:`.Shim` object.

        """
        shim = Shim(thetadeg, thick, width, edge=self)
        return shim


    def calc_amplitude(self):
        return self.scaling_factor


    def create(self):
        r"""Creates the uneven bottom edge imperfections

        The uneven bottom edge will be represented by many GAP elements
        created in such a way to consider all the imperfections contained in
        the current :class:`.UnevenBottomEdge` object.

        The output file ``cc.model_name + '_bottom_edge.gaps'`` will be
        created, where ``cc`` is the :class:`.ConeCyl` object that contains
        this :class:`.UnevenBottomEdge` object.

        The following steps are executed:

        - get the `\theta` coordinate of the bottom nodes from the shell and
          bottom resin rings

        - get imperfection from the ``shims`` attribute

        - get any additional imperfection of the bottom edge represented by
          ``measured_u3s``

        Assumptions:

        - for a given `\theta` coordinate the uneven displacement is the same
          for all the shell and resin ring nodes

        .. note:: Must be called from Abaqus

        """
        from abaqus import mdb
        from abaqusConstants import (PIN_MPC, DOF_MODE_MPC)
        from regionToolset import Region

        from desicos.abaqus.abaqus_functions import edit_keywords

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        ra = mod.rootAssembly
        nodes = np.array(ra.sets['shell_bottom_edges'].nodes)
        tshell = sum(cc.plyts)
        cosa = np.cos(cc.alpharad)
        if cc.resin_add_BIR:
            tmp = np.array(ra.sets['Bottom_IR_faces'].nodes)
            coords = np.array([n.coordinates for n in tmp])
            r_nodes = np.sqrt(coords[:,0]**2 + coords[:,1]**2)
            # taking nodes that are not pinned to the shell
            check = (r_nodes < (cc.rbot - cosa*0.51*tshell))
            nodes = np.hstack((nodes, tmp[check]))
        if cc.resin_add_BOR:
            tmp = np.array(ra.sets['Bottom_OR_faces'].nodes)
            coords = np.array([n.coordinates for n in tmp])
            r_nodes = np.sqrt(coords[:,0]**2 + coords[:,1]**2)
            # taking nodes that are not pinned to the shell
            check = (r_nodes > (cc.rbot + cosa*0.51*tshell))
            nodes = np.hstack((nodes, tmp[check]))
        coords = np.array([n.coordinates for n in nodes])
        r_nodes = np.sqrt(coords[:,0]**2 + coords[:,1]**2)
        theta_nodes = np.arctan2(coords[:,1], coords[:,0])
        #
        # calculating gaps
        #
        # contributions from measured edge imperfection
        if self.measured_u3s is not None:
            measured_u3s = np.asarray(self.measured_u3s)
        else:
            measured_u3s = np.zeros((2, 100))
            measured_u3s[0, :] = np.linspace(0, 360, 100)
        #   calculating u3 for each node
        u3_nodes = interp(rad2deg(theta_nodes), measured_u3s[0, :],
                measured_u3s[1, :], period=360)

        # contributions from shims
        hs = np.zeros_like(theta_nodes)
        for s in self.shims:
            trad1 = deg2rad(s.thetadeg)
            trad2 = deg2rad(s.thetadeg + 360*s.width/(2*pi*cc.rbot))
            thetarads = [trad1-0.001, trad1, trad2, trad2+0.001]
            u3s = [0, s.thick, s.thick, 0]
            tmp = interp(theta_nodes, thetarads, u3s, period=2*pi)
            hs += tmp
        u3_nodes += hs

        # applying scaling_factor
        u3_nodes *= self.scaling_factor

        # calculating gap values
        gaps = u3_nodes.max() - u3_nodes
        # creating GAP elements
        rps_gap = []
        text = ''
        for node, gap in zip(nodes, gaps):
            coord = list(node.coordinates)
            coord[2] -= gap
            rp = ra.ReferencePoint(point=coord)
            inst_name = node.instanceName
            #FIXME TODO really bad approach, but couldn' find any other way to
            #           get the actual node id that is printed in the .inp
            #           file
            rp_id = int(rp.name.split('-')[1]) + 2
            #
            rps_gap.append(rp)
            gap_name = 'gap_{0}_{1:d}'.format(inst_name, 1000000+node.label)
            inst_node = '{0}.{1:d}'.format(inst_name, node.label)
            text += ('\n*Element, type=GAPUNI, elset={0}'.format(gap_name))
            text += ('\n{0:d},{1},{2:d}'.format(1000000+node.label, inst_node,
                     rp_id))
            text += '\n*GAP, elset={0}'.format(gap_name)
            text += '\n{0:f},0,0,-1\n'.format(gap)

        bottom_name_gaps = '{0}_bottom_edge.gaps'.format(cc.model_name)
        with open(bottom_name_gaps, 'w') as f:
            f.write(text)

        if not self.impconf.uneven_top_edge:
            pattern = '*Instance'
            text = '*INCLUDE, INPUT={0}'.format(bottom_name_gaps)
            edit_keywords(mod=mod, text=text, before_pattern=pattern)

        set_RP_bot=ra.sets['RP_bot']
        rps = ra.referencePoints
        rps_gap_datums = [rps[rp.id] for rp in rps_gap]
        region = Region(referencePoints=rps_gap_datums)
        ra_cyl_csys = ra.features['ra_cyl_csys']
        ra_cyl_csys = ra.datums[ra_cyl_csys.id]
        mod.MultipointConstraint(name='MPC_RP_GAPs_bot_edge',
                                 controlPoint=set_RP_bot,
                                 surface=region,
                                 mpcType=PIN_MPC,
                                 userMode=DOF_MODE_MPC,
                                 userType=0, csys=ra_cyl_csys)


class UnevenTopEdge(object):
    """Uneven Top Edge

    The following attributes are taken into account:
    - misalignment of the top edge
    - presence of shims
    - measured uneven edge points

    ============== =========================================================
    Attributes     Description
    ============== =========================================================
    betadeg        Misalignment of the top edge in degrees
    omegadeg       Azimuth angle of the top edge misalignment in degrees.
    shims          ``list`` of shims included to this edge
    measured_u3s   Measured points describing the edge imperfection
    ============== =========================================================

    """
    def __init__(self, betadeg=None, omegadeg=None):
        self.name = 'uneven_top_edge'
        self.index = None
        self.impconf = None
        self.betadeg = betadeg
        self.omegadeg = omegadeg
        self.thetadegs = []
        self.pts = []
        self.shims = []
        self.measured_u3s = None
        self.scaling_factor = 1.
        # plotting options
        self.xaxis = 'scaling_factor'
        self.xaxis_label = 'Scaling factor'


    def __nonzero__(self): # in Python 3 this method was renamed to __bool__
        return self.__bool__()


    def __bool__(self):
        cc = self.impconf.conecyl
        return (bool(self.betadeg) or bool(self.shims) or
                bool(self.measured_u3s is not None) or bool(cc.bc_gaps_top_edge))


    def rebuild(self):
        cc = self.impconf.conecyl
        self.thetadegs = [s.thetadeg for s in self.shims]
        self.thetadegs += [s.thetadeg + 360*s.width/(2*pi*cc.rtop)
                           for s in self.shims]
        self.pts = []


    def add_measured_u3s(self, thetadegs, u3s):
        """Adds measured data to the uneven top edge

        The edge imperfection that actually goes for each node is a linear
        interpolation of the measured values.

        Parameters
        ----------
        thetadegs : list
            The circumferential positions where the imperfect top edge was
            measured, in degrees.
        u3s : list
            The measured imperfections representing displacements along the
            `X_3` axis :ref:`of the adopted model <figure_conecyl>`.

        """
        if len(thetadegs) != len(u3s):
            raise ValueError('thetadegs must have the same length of u3s!')
        self.measured_u3s = np.array([thetadegs, u3s])


    def add_shim(self, thetadeg, thick, width):
        """Adds a shim to the uneven top edge

        Parameters
        ----------
        thetadeg : float
            Circumferential position where the shim starts.
        thick : float
            Thickness of the shim.
        width : float
            Perimetrical width of the shim (along the shell perimeter).

        Returns
        -------
        shim : :class:`.Shim` object.

        """
        shim = Shim(thetadeg, thick, width, edge=self)
        return shim


    def calc_amplitude(self):
        return self.scaling_factor


    def create(self):
        r"""Creates the uneven top edge imperfections

        The uneven top edge will be represented by many GAP elements created
        in such a way to consider all the imperfections contained in the
        current :class:`.UnevenTopEdge` object.

        The output file ``cc.model_name + '_top_edge.gaps'`` will be created,
        where ``cc`` is the :class:`.ConeCyl` object that contains this
        :class:`.UnevenTopEdge` object.

        The following steps are executed:

        - get the `\theta` coordinate of the top nodes from the shell and top
          resin rings

        - get imperfection from the ``shims`` attribute

        - get any additional imperfection of the top edge represented by
          ``measured_u3s``

        - include effect of the misalignment angle ``betadeg``

        Assumptions:

        - for a given `\theta` coordinate the uneven displacement is the same
          for all the shell and resin ring nodes, but the load asymmetry angle
          ``cc.betadeg`` may change this equality. The contribution due to
          `\beta` is given by:

          .. math::
              \Delta u_3 = R_{top} tan(\beta) cos(\theta-\omega)

        .. note:: Must be called from Abaqus

        """
        from abaqus import mdb
        from abaqusConstants import (PIN_MPC, DOF_MODE_MPC)
        from regionToolset import Region

        from desicos.abaqus.abaqus_functions import edit_keywords

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        ra = mod.rootAssembly
        nodes = np.array(ra.sets['shell_top_edges'].nodes)
        tshell = sum(cc.plyts)
        cosa = np.cos(cc.alpharad)
        if cc.resin_add_TIR:
            tmp = np.array(ra.sets['Top_IR_faces'].nodes)
            coords = np.array([n.coordinates for n in tmp])
            r_nodes = np.sqrt(coords[:,0]**2 + coords[:,1]**2)
            # taking nodes that are not pinned to the shell
            check = (r_nodes < (cc.rtop - cosa*0.51*tshell))
            nodes = np.hstack((nodes, tmp[check]))
            if cc.bc_fix_top_side_u3:
                tmp = np.array(ra.sets['Top_IR_faces_side'].nodes)
                coords = np.array([n.coordinates for n in tmp])
                # taking nodes that are not on the top edge
                check = (coords[:,2] < (cc.H-0.1))
                nodes = np.hstack((nodes, tmp[check]))
        if cc.resin_add_TOR:
            tmp = np.array(ra.sets['Top_OR_faces'].nodes)
            coords = np.array([n.coordinates for n in tmp])
            r_nodes = np.sqrt(coords[:,0]**2 + coords[:,1]**2)
            # taking nodes that are not pinned to the shell
            check = (r_nodes > (cc.rtop + cosa*0.51*tshell))
            nodes = np.hstack((nodes, tmp[check]))
            if cc.bc_fix_top_side_u3:
                tmp = np.array(ra.sets['Top_OR_faces_side'].nodes)
                coords = np.array([n.coordinates for n in tmp])
                # taking nodes that are not on the top edge
                check = (coords[:,2] < (cc.H-0.1))
                nodes = np.hstack((nodes, tmp[check]))
        coords = np.array([n.coordinates for n in nodes])
        r_nodes = np.sqrt(coords[:,0]**2 + coords[:,1]**2)
        theta_nodes = np.arctan2(coords[:,1], coords[:,0])
        #
        # calculating gaps
        #
        # contributions from measured edge imperfection
        if self.measured_u3s is not None:
            measured_u3s = np.asarray(self.measured_u3s)
        else:
            measured_u3s = np.zeros((2, 100))
            measured_u3s[0, :] = np.linspace(0, 360, 100)
        #   calculating u3 for each node
        u3_nodes = interp(rad2deg(theta_nodes), measured_u3s[0, :],
                measured_u3s[1, :], period=360)
        #   applying load asymmetry according to cc.betarad and omega
        betarad = deg2rad(cc.betadeg)
        omegarad = deg2rad(cc.omegadeg)
        u3_nodes -= cc.rtop*np.tan(betarad)*np.cos(theta_nodes-omegarad)

        # contributions from shims
        hs = np.zeros_like(theta_nodes)
        for s in self.shims:
            trad1 = deg2rad(s.thetadeg)
            trad2 = deg2rad(s.thetadeg + 360*s.width/(2*pi*cc.rtop))
            thetarads = [trad1-0.001, trad1, trad2, trad2+0.001]
            u3s = [0, s.thick, s.thick, 0]
            tmp = interp(theta_nodes, thetarads, u3s, period=2*pi)
            hs += tmp
        u3_nodes -= hs

        # applying scaling_factor
        u3_nodes *= self.scaling_factor

        # calculating gap values
        gaps = u3_nodes - u3_nodes.min()
        # creating GAP elements
        rps_gap = []
        text = ''
        for node, gap in zip(nodes, gaps):
            coord = list(node.coordinates)
            coord[2] += gap
            rp = ra.ReferencePoint(point=coord)
            inst_name = node.instanceName
            #FIXME TODO really bad approach, but couldn' find any other way to
            #           get the actual node id that is printed in the .inp
            #           file
            rp_id = int(rp.name.split('-')[1]) + 2
            #
            rps_gap.append(rp)
            gap_name = 'gap_{0}_{1:d}'.format(inst_name, 2000000+node.label)
            inst_node = '{0}.{1:d}'.format(inst_name, node.label)
            text += ('\n*Element, type=GAPUNI, elset={0}'.format(gap_name))
            text += ('\n{0:d},{1:d},{2}'.format(2000000+node.label, rp_id,
                     inst_node))
            text += '\n*GAP, elset={0}'.format(gap_name)
            text += '\n{0:f},0,0,-1\n'.format(gap)

        top_name_gaps = '{0}_top_edge.gaps'.format(cc.model_name)
        with open(top_name_gaps, 'w') as f:
            f.write(text)

        pattern = '*Instance'
        if self.impconf.uneven_bottom_edge:
            bottom_name_gaps = '{0}_bottom_edge.gaps'.format(cc.model_name)
            text = '*INCLUDE, INPUT={0}'.format(bottom_name_gaps)
            text += '\n**\n*INCLUDE, INPUT={0}'.format(top_name_gaps)
        else:
            text = '*INCLUDE, INPUT={0}'.format(top_name_gaps)
        edit_keywords(mod=mod, text=text, before_pattern=pattern, insert=True)

        set_RP_top = ra.sets['RP_top']
        rps = ra.referencePoints
        rps_gap_datums = [rps[rp.id] for rp in rps_gap]
        region = Region(referencePoints=rps_gap_datums)
        ra_cyl_csys = ra.features['ra_cyl_csys']
        ra_cyl_csys = ra.datums[ra_cyl_csys.id]
        mod.MultipointConstraint(name='MPC_RP_GAPs_top_edge',
                                 controlPoint=set_RP_top,
                                 surface=region,
                                 mpcType=PIN_MPC,
                                 userMode=DOF_MODE_MPC,
                                 userType=0, csys=ra_cyl_csys)

