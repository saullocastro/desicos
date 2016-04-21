import numpy as np
from numpy import sin, cos

from imperfection import Imperfection
from desicos.abaqus.constants import *
from desicos.logger import warn

class PLoad(Imperfection):
    """Perturbation Load

    """
    def __init__(self, thetadeg, pt, pltotal, step=1):
        super(PLoad, self).__init__()
        self.thetadeg = thetadeg
        self.pt = pt
        self.pltotal = pltotal # resultant pload
        self.step = step
        self.name = 'PL'
        self.index = None
        if abs(pltotal) < 0.1*TOL:
            pltotal = 0.1*TOL
        self.plradial = None    # component radial direction
        self.plx = None        # component x      direction
        self.ply = None        # component y      direction
        self.plz = None        # component z      direction
        # plotting options
        self.xaxis = 'pltotal'
        self.xaxis_label = 'Perturbation Load, N'


    def rebuild(self):
        cc = self.impconf.conecyl
        alpharad = cc.alpharad
        self.plradial = self.pltotal*cos(alpharad)
        self.plz = -self.pltotal*sin(alpharad)
        self.plx = -self.plradial*cos(np.deg2rad(self.thetadeg))
        self.ply = -self.plradial*sin(np.deg2rad(self.thetadeg))
        self.x, self.y, self.z = self.get_xyz()
        self.r, z = cc.r_z_from_pt(self.pt)
        self.thetadeg = self.thetadeg % 360.
        self.thetadegs = [self.thetadeg]
        self.pts = [self.pt]
        self.name = 'PL_pt_{0:03d}_theta_{1:03d}'.format(
                        int(self.pt*100), int(self.thetadeg))
        if abs(self.pltotal) < 0.1*TOL:
            warn('Ignoring perturbation load: {0}'.format(self.name))


    def calc_amplitude(self):
        """Calculate the imperfection amplitude.

        The odb must be available and it will be used to extract the last
        frame of the first analysis step, corresponding to the constant loads.

        """
        from abaqus import mdb

        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        nodes = mod.parts[cc.part_name_shell].nodes

        # calculate unit normal vector w.r.t. the surface
        ux = cos(cc.alpharad)*cos(np.deg2rad(self.thetadeg))
        uy = cos(cc.alpharad)*sin(np.deg2rad(self.thetadeg))
        uz = sin(cc.alpharad)
         # It would be nicer to calculate this based on e.g. MSI amplitude
        max_imp = 10
        r_TOL = 0.1 # Radius of cylinder to search
        pt1 = (self.x + max_imp*ux, self.y + max_imp*uy, self.z + max_imp*uz)
        pt2 = (self.x - max_imp*ux, self.y - max_imp*uy, self.z - max_imp*uz)
        # Search for our node in a cylinder normal to the surface, because
        # 'our' node may be moved by a MSI
        nodes = nodes.getByBoundingCylinder(pt1, pt2, r_TOL)
        if len(nodes) != 1:
            warn("Unable to locate node where perturbation load" +
                 "'{0}' is applied. ".format(self.name) +
                 "Cannot calculate imperfection amplitude.")
            self.amplitude = 0.
            return 0.

        odb = cc.attach_results()
        fo = odb.steps[cc.step1Name].frames[-1].fieldOutputs
        if not 'U' in fo.keys():
            raise RuntimeError(
                    'Field output 'U' not available to calculate amplitude')
        #TODO not sure if this is robust: node.label-1
        u, v, w = fo['U'].values[nodes[0].label-1].data
        cc.detach_results(odb)

        alpha = cc.alpharad
        theta = np.deg2rad(self.thetadeg)
        amp = -((u*cos(theta) + v*sin(theta))*cos(alpha) + w*sin(alpha))
        self.amplitude = amp

        return amp


    def create(self):
        """Include the perturbation load.

        The load step in which the perturbation load is included depends on
        the ``step`` parameter, which can be 1 or 2. If applied in the first
        step it will be kept constant, whereas in the second step it will be
        incremented.

        The perturbation load is included after finding its corresponding
        vertice. The perturbation load is **not created** if its value is
        smaller then ``0.1*TOL`` (see :mod:`desicos.constants`).

        .. note:: Must be called from Abaqus.

        """
        if abs(self.pltotal) < 0.1*TOL:
            return
        from abaqus import mdb
        import regionToolset
        cc = self.impconf.conecyl
        mod = mdb.models[cc.model_name]
        inst_shell = mod.rootAssembly.instances['INST_SHELL']
        region = regionToolset.Region(vertices=inst_shell.vertices.findAt(
                        ((self.x, self.y, self.z),)))
        step_name = cc.get_step_name(self.step)
        mod.ConcentratedForce(name=self.name, createStepName=step_name,
                region=region, cf1=self.plx, cf2=self.ply, cf3=self.plz,
                field='')
