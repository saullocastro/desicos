import os

import numpy

import desicos.conecylDB as conecylDB
from desicos.logger import *
from desicos.abaqus.constants import *
from desicos.composite.laminate import read_stack

import _imperfections
import _imperfections._pload
import _plot
#
class ConeCyl(object):

    def __init__(self):
        self.index = 0
        self.name = ''
        self.rename = True
        self.jobname = ''
        self.rebuilt = False
        self.created_model = False
        # geometry related
        self.r = None
        self.r2 = None
        self.h = None
        self.alphadeg = 0.
        self.alpharad = None
        self.betadeg = 0.
        self.betarad = None
        self.omegadeg = 0.
        self.omegarad = None
        self.cutouts = []
        self.sketch_planes = []
        self.cutplanes = []
        self.cross_sections = []
        self.meridians = []
        self.thetas = []
        self.cross_zs = []
        # laminaprop related
        # laminaprop below from COCOMAT, see Degenhardt, 2010
        #(142.5e3,8.7e3,0.28,5.1e3,5.1e3,3.4e3)
        self.laminaprop = None
        # property related
        self.laminate_t = None
        self.plyt = None
        self.stack = []

        # TODO this will be used for many materials and ply thicknesses
        self.plyts = []
        self.laminaprops = []
        self.allowables  = []
        self.laminapropKey  = 'material'
        self.laminapropKeys  = []
        self.lam = None

        # load related
        self.linear_buckling = False
        self.axial_displ = None
        self.axial_include = True
        self.pressure_value = -1.
        self.pressure_include = False
        self.analytical_model = False
        self.separate_load_steps = True
        self.impconf = _imperfections.ImpConf()
        self.impconf.conecyl = self

        # boundary conditions
        self.botU1 = True
        self.botU2 = True
        self.botU3 = True
        self.botUR1 = True
        self.botUR2 = True
        self.botUR3 = True
        self.topU1 = True
        self.topU2 = True
        self.topU3 = False
        self.topUR1 = True
        self.topUR2 = True
        self.topUR3 = True
        # mesh related
        self.boundary_clearance = None #0.1 or other fraction
        self.numel_r = None
        self.numel_h = None
        self.numel_hr_ratio = None
        self.elem_type = 'S8R5'
        self.elsize_r  = None
        self.elsize_r2 = None
        self.elsize_h  = None
        self.meshname = ''
        self.mesh_size_driven_by_cutouts = False
        # analysis related
        self.direct_ABD_input = False
        self.rsm = False # reduced stiffness method
        self.rsm_reduction_factor = 1.
        self.rsm_mode = 1
        #
        self.step1Name   = ''
        self.step2Name   = ''
        self.minInc1 = 1.e-6
        self.initialInc1 = 0.1
        self.maxInc1 = 1.
        self.maxNumInc1 = 10000
        #
        self.minInc2 = 1.e-6
        self.initialInc2 = 0.01
        self.maxInc2 = 0.01
        self.maxNumInc2 = 100000
        #
        self.artificial_damping1 = False
        self.artificial_damping2 = True
        self.damping_factor1 = None
        self.damping_factor2 = 1.e-7
        self.adaptiveDampingRatio = False
        self.time_points = 40
        # file management related
        self.tmp_dir = TMP_DIR
        self.study = None
        self.study_dir = TMP_DIR
        self.output_dir = os.path.join(TMP_DIR, 'outputs')
        #ABAQUS objects
        self.mdb = None
        self.mod = None
        self.part = None
        self.inst = None
        self.local_csys = None
        self.job = None
        self.nodes = {}
        self.faces = []
        self.rp_top = None
        #OUTPUTS
        self.jobwalltime = None
        self.ls_curve = None
        self.ener_total = 0.
        self.zdisp = []
        self.zload = []
        self.stress_min_num     = {}
        self.stress_min_ms      = {}
        self.stress_min_pos_num = {}
        self.stress_max_num     = {}
        self.stress_max_ms      = {}
        self.stress_max_pos_num = {}
        self.hashin_max_num     = {}
        self.hashin_max_ms      = {}
        self.hashin_max_pos_num = {}
        self.output_requests = ['UT', 'NFORC']
        self.request_stress_output = False
        self.request_force_output = False

    def fromDB(self, name=''):
        if name <> '':
            self.name = name
        ccs = conecylDB.ccs.ccs
        if self.name in ccs.keys():
            ccdict = ccs[ self.name ]
            for k,v in ccdict.iteritems():
                if k == 'pload':
                    pload = _imperfections._pload.PLoad(theta=0.,
                                                         pt=0.5,
                                                         pltotal = v)
                    pload.impconf = self.impconf
                    setattr(self.impconf, 'ploads', [ pload ])
                else:
                    setattr(self, k, v)
            #NOTE commented because it was making tricky to set the parameters
            #     during a parametric study
            #self.rebuild(save_rebuild=False)
        else:
            error('{0} not found in the conecylDB'.format(self.name))

        return self

    def rebuild(self, **kwargs):
        import _rebuild
        return _rebuild.rebuild(self, **kwargs)

    def prepare_to_save(self):
        self.rebuilt = False
        self.mdb  = None
        self.mod  = None
        self.part = None
        self.inst = None
        self.job  = None
        self.faces = []
        self.rp_top = None
        self.local_csys = None
        self.sketch_planes = []
        self.cutplanes = []
        #
        for mer in self.meridians:
            mer.part_edges = []
            mer.inst_edges = []
        for cs  in self.cross_sections:
            cs.part_edges = []
            cs.inst_edges = []
        #
        for node in self.nodes.values():
            node.rebuild()
            node.obj = None
        #
        for cutout in self.cutouts:
            cutout.diag1_plane = None
            cutout.diag2_plane = None
            cutout.diag1_edges = []
            cutout.diag2_edges = []
            cutout.inner_edges = []
            cutout.middle_edges = []
            cutout.outer_edges = []
            cutout.sketch_plane = None
            cutout.sketches = []
            cutout.faces = []

        for imp in self.impconf.imperfections:
            imp.vertice = None
            imp.sketches = []
            imp.faces = []
            imp.sketch_plane = None

        return True

    def r_z_from_pt(self, pt=0.5):
        r = self.r + (self.r2 - self.r)*pt
        z = self.h * pt
        return r, z

    def step_name(self, step_num):
        if step_num == 1:
            return self.step1Name
        else:
            return self.step2Name

    def create_model(self):
        import _create_model
        return _create_model._create_model(self)

    def write_job(self, **kwargs):
        import _write_job
        return _write_job.write_job(self, **kwargs)

    def read_walltime(self):
        #FIXME why the error?? remove try / except
        try:
            tmppath = os.path.join(self.output_dir, self.jobname + '.msg')
            tmp = open(tmppath, 'r')
            lines = tmp.readlines()
            a,a,a,a,w = lines[-1].split()
            self.jobwalltime = float(w)
            tmp.close()
        except:
            self.jobwalltime = None

    def attach_results(self):
        odbname = self.jobname + '.odb'
        odbpath = os.path.join(self.output_dir, odbname)
        if not os.path.isfile(odbpath):
            warn('result was not found')
            return False
        import __main__
        session = __main__.session
        if not odbpath in session.odbs.keys():
            return session.openOdb(name = odbname,
                                     path = odbpath,
                                     readOnly = True)
        else:
            return session.odbs[ odbname ]

    def detach_results(self, odb):
        import visualization
        visualization.closeOdb(odb)

    def read_outputs(self, **kwargs):
        import _read_outputs
        return _read_outputs.read_outputs(self, **kwargs)

    def plot_displacements(self, **kwargs):
        return _plot.plot_displacements(self, **kwargs)

    def plot_forces(self, **kwargs):
        return _plot.plot_forces(self, **kwargs)

    def plot_stress_analysis(self, **kwargs):
        return _plot.plot_stress_analysis(self, **kwargs)
        import abaqus_functions
        abaqus_functions.configure_session()

    def plot_xy(self, xs, ys, **kwargs):
        return _plot.plot_xy(self, xs, ys, **kwargs)

    def plot_opened_conecyl(self, **kwargs):
        #NOTE requires matplotlib do not move the import below
        import plot
        #outside this function
        return plot.plot_opened_conecyl(self, **kwargs)

    def read_ehr(self):
        self.read_displacements(step_num = 1)
        for pload in self.impconf.ploads:
            pload.calc_ehr_and_displ()

    def check_completed(self, wait=False, print_found=False):
        if not self.rebuilt:
            self.rebuild()
        tmp = os.path.join(self.output_dir, self.jobname + '.log')
        if wait == True:
            log('Waiting for job completion...')
        #TODO a general function to check the log file
        while True:
            if os.path.isfile(tmp):
                tmpfile = open(tmp, 'r')
                lines = tmpfile.readlines()
                tmpfile.close()
                if len(lines) == 0:
                    continue
                if len(lines) < 2:
                    continue
                if lines[-2].find('End Abaqus/Standard Analysis') > -1:
                    if print_found:
                        log('RUN COMPLETED for model {0}'.format(self.jobname))
                    return True
                elif lines[-1].find('Abaqus/Analysis exited with errors') > -1:
                    if print_found:
                        log('RUN COMPLETED WITH ERRORS for model {0}'.format(
                            self.jobname))
                    return True

                else:
                    if not wait:
                        warn('RUN NOT COMPLETED for model {0}'.format(
                            self.jobname))
                        return False
            else:
                if not wait:
                    warn('RUN NOT STARTED for model {0}'.format(self.jobname))
                    return False
            if wait:
                import time
                time.sleep(5)

    def stress_analysis(self, **kwargs):
        if self.linear_buckling:
            return True
        if not self.check_completed():
            return False
        self.read_outputs(last_frame = False,
                           last_cross_section = False,
                           read_fieldOutputs = True)
        import _stress_analysis
        ans = _stress_analysis.calc_frames(self, **kwargs)
        self.read_outputs()
        self.plot_stress_analysis()

        return ans

    def create_cutout(self, theta, pt, d, numel=None):
        """
            theta   cylindrical coordinate theta in degrees
            pt      coordinate z/cylinder height (or cone height)
            d       the float number for the cutout diameter
        """
        import cutout
        cutobj = cutout.Cutout()
        cutobj.theta = theta
        cutobj.pt = pt
        cutobj.d = d
        if numel <> None:
            cutobj.numel = numel
        cutobj.index = len(self.cutouts)
        cutobj.conecyl = self
        self.cutouts.append(cutobj)
        return cutobj

    def calc_ABD_matrix(self):
        self.lam = read_stack(stack = self.stack,
                              plyt = self.plyt,
                              laminaprop  = self.laminaprop,
                              plyts = self.plyts,
                              laminaprops = self.laminaprops)

    def calc_nasaKDF(self):
        self.calc_ABD_matrix()
        if self.alphadeg > 0. :
            rm = (self.r + self.r2)/2.
            req = rm/numpy.cos(self.alpharad)
        else:
            req = self.r
        Ex = self.lam.A[0,0]
        Ey = self.lam.A[1,1]
        Dx = self.lam.D[0,0]
        Dy = self.lam.D[1,1]
        teq = 3.4689* (Dx*Dy/(Ex*Ey))**0.25
        phi = 1/16. * (req/teq)**0.5
        self.nasaKDF = 1. - 0.901*(1-numpy.e**-phi)
        return self.nasaKDF

    def measure_me(self):
        nodes = self.part.nodes
        amps = []
        for node in nodes:
            x, y, z = node.coordinates
            node_r = (x**2 + y**2)**0.5
            pt = z / self.h
            r, z = self.r_z_from_pt(pt)
            amps.append(node_r - r)
        in_amp = min(amps)
        out_amp = max(amps)
        abs_amps = [abs(amp) for amp in amps]
        max_amp = max(abs_amps)
        return max_amp


